from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

import redis.asyncio as redis

from app.cache import get_redis
from app.config import settings
from app.database import get_db, AsyncSessionLocal
from app.models import Click, Url
from app.schemas import ShortenRequest, ShortenResponse
from app.services.shortener import generate_short_code
from app.services.ratelimit import is_allowed

router = APIRouter()


async def _record_click(
    short_code: str, referrer: str | None, ip_address: str | None
) -> None:
    """Insert a Click row and increment url.click_count after the response is sent.

    Wrapped in try/except so a DB hiccup never breaks the redirect response.
    """
    try:
        async with AsyncSessionLocal() as session:
            session.add(
                Click(short_code=short_code, referrer=referrer, ip_address=ip_address)
            )
            result = await session.execute(
                select(Url).where(Url.short_code == short_code)
            )
            url = result.scalar_one_or_none()
            if url is not None:
                url.click_count += 1
            await session.commit()
    except Exception:
        pass


@router.post("/shorten", response_model=ShortenResponse, status_code=201)
async def shorten_url(
    request: Request,
    payload: ShortenRequest,
    db: AsyncSession = Depends(get_db),
    cache: redis.Redis = Depends(get_redis),
) -> ShortenResponse:
    ip = request.client.host
    if not await is_allowed(
        cache, f"ratelimit:{ip}", settings.RATE_LIMIT_PER_MINUTE, 60
    ):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again later.",
            headers={"Retry-After": "60"},
        )
    expires_at = None
    if payload.expires_in_hours is not None:
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=payload.expires_in_hours
        )

    for _ in range(5):
        code = generate_short_code()
        url = Url(
            short_code=code,
            original_url=str(payload.original_url),
            expires_at=expires_at,
        )
        db.add(url)
        try:
            await db.commit()
            await db.refresh(url)
            return ShortenResponse(
                short_code=url.short_code,
                short_url=f"{settings.BASE_URL}/{url.short_code}",
                original_url=url.original_url,
            )
        except IntegrityError:
            await db.rollback()

    raise HTTPException(
        status_code=500, detail="Could not generate a unique short code. Try again."
    )


@router.get("/{short_code}")
async def redirect_url(
    short_code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    cache: redis.Redis = Depends(get_redis),
) -> RedirectResponse:
    referrer = request.headers.get("referer")
    ip = request.client.host
    cache_key = f"url:{short_code}"

    cached = await cache.get(cache_key)
    if cached:
        background_tasks.add_task(_record_click, short_code, referrer, ip)
        return RedirectResponse(cached, status_code=302)

    result = await db.execute(select(Url).where(Url.short_code == short_code))
    url = result.scalar_one_or_none()

    if url is None:
        raise HTTPException(status_code=404, detail="Short URL not found.")

    if url.expires_at is not None and url.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=404, detail="Short URL has expired.")

    await cache.set(cache_key, url.original_url, ex=settings.CACHE_TTL_SECONDS)
    background_tasks.add_task(_record_click, short_code, referrer, ip)
    return RedirectResponse(url.original_url, status_code=302)
