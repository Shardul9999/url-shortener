import asyncio

import pytest
import redis.asyncio as redis
from httpx import AsyncClient

from app.services.ratelimit import is_allowed
from app.config import settings

pytestmark = pytest.mark.asyncio

LIMIT = 3
WINDOW = 2  # seconds — short so the window-expiry test doesn't slow the suite


# ---------------------------------------------------------------------------
# Unit tests — is_allowed() directly against test Redis
# ---------------------------------------------------------------------------

async def test_allows_up_to_limit(redis_client: redis.Redis):
    """Every call within the limit should return True."""
    for i in range(LIMIT):
        allowed = await is_allowed(redis_client, "test:unit", LIMIT, WINDOW)
        assert allowed is True, f"Expected True on call {i + 1}, got False"


async def test_blocks_after_limit(redis_client: redis.Redis):
    """The call immediately after the limit is hit must return False."""
    for _ in range(LIMIT):
        await is_allowed(redis_client, "test:unit", LIMIT, WINDOW)

    blocked = await is_allowed(redis_client, "test:unit", LIMIT, WINDOW)
    assert blocked is False


async def test_allows_again_after_window_expires(redis_client: redis.Redis):
    """After the window passes, the counter resets and requests are allowed again."""
    for _ in range(LIMIT):
        await is_allowed(redis_client, "test:window", LIMIT, WINDOW)

    blocked = await is_allowed(redis_client, "test:window", LIMIT, WINDOW)
    assert blocked is False

    await asyncio.sleep(WINDOW + 0.1)  # wait for the sorted set entries to fall outside the window

    allowed = await is_allowed(redis_client, "test:window", LIMIT, WINDOW)
    assert allowed is True


# ---------------------------------------------------------------------------
# Integration test — POST /shorten through the HTTP client
# ---------------------------------------------------------------------------

async def test_shorten_returns_429_after_rate_limit(client: AsyncClient):
    """
    Fire RATE_LIMIT_PER_MINUTE + 1 requests through the real endpoint.
    The first N should be 201; the one after the limit should be 429.
    """
    limit = settings.RATE_LIMIT_PER_MINUTE
    payload = {"original_url": "https://example.com"}

    for i in range(limit):
        response = await client.post("/shorten", json=payload)
        assert response.status_code == 201, (
            f"Expected 201 on request {i + 1}, got {response.status_code}"
        )

    response = await client.post("/shorten", json=payload)
    assert response.status_code == 429
    assert response.headers.get("retry-after") == "60"


async def test_redirect_returns_429_after_rate_limit(client: AsyncClient):
    """
    Fire REDIRECT_RATE_LIMIT_PER_MINUTE + 1 GET /{code} requests.
    The one past the limit should be 429.
    """
    # Create a URL to redirect to
    post = await client.post("/shorten", json={"original_url": "https://example.com"})
    assert post.status_code == 201
    code = post.json()["short_code"]

    limit = settings.REDIRECT_RATE_LIMIT_PER_MINUTE
    for i in range(limit):
        r = await client.get(f"/{code}", follow_redirects=False)
        assert r.status_code == 302, f"Expected 302 on request {i + 1}, got {r.status_code}"

    r = await client.get(f"/{code}", follow_redirects=False)
    assert r.status_code == 429
    assert r.headers.get("retry-after") == "60"
