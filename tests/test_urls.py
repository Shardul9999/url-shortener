import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def _shorten(client: AsyncClient, url: str = "https://example.com") -> dict:
    """Helper — POST /shorten and return the parsed JSON body."""
    response = await client.post("/shorten", json={"original_url": url})
    assert response.status_code == 201
    return response.json()


# ---------------------------------------------------------------------------
# POST /shorten
# ---------------------------------------------------------------------------

async def test_shorten_returns_short_code(client: AsyncClient):
    body = await _shorten(client)
    assert "short_code" in body
    assert len(body["short_code"]) == 6
    assert body["original_url"] == "https://example.com/"
    assert body["short_url"].endswith(f"/{body['short_code']}")


# ---------------------------------------------------------------------------
# GET /{short_code} — redirect
# ---------------------------------------------------------------------------

async def test_redirect_cache_miss(client: AsyncClient):
    """First request goes to DB (cache miss) and should 302."""
    body = await _shorten(client)
    response = await client.get(f"/{body['short_code']}", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "https://example.com/"


async def test_redirect_cache_hit(client: AsyncClient, redis_client):
    """Second request is served from Redis — should still 302 to the same URL."""
    body = await _shorten(client)
    code = body["short_code"]

    # first request populates the cache
    await client.get(f"/{code}", follow_redirects=False)

    # confirm the key is now in Redis
    cached = await redis_client.get(f"url:{code}")
    assert cached == "https://example.com/"

    # second request should still redirect correctly
    response = await client.get(f"/{code}", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "https://example.com/"


async def test_redirect_nonexistent_code_returns_404(client: AsyncClient):
    response = await client.get("/doesnotexist", follow_redirects=False)
    assert response.status_code == 404


async def test_redirect_expired_url_returns_404(client: AsyncClient):
    """URL created with expires_in_hours=-1 is already expired on arrival."""
    response = await client.post(
        "/shorten",
        json={"original_url": "https://example.com", "expires_in_hours": -1},
    )
    assert response.status_code == 201
    code = response.json()["short_code"]

    response = await client.get(f"/{code}", follow_redirects=False)
    assert response.status_code == 404
