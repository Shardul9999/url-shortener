from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

import redis.asyncio as redis

from app.cache import get_redis
from app.config import settings
from app.database import get_db
from app.models import Url
from app.schemas import ShortenRequest, ShortenResponse
from app.services.shortener import generate_short_code
from app.services.ratelimit import is_allowed

router = APIRouter()


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
    db: AsyncSession = Depends(get_db),
    cache: redis.Redis = Depends(get_redis),
) -> RedirectResponse:
    cache_key = f"url:{short_code}"

    cached = await cache.get(cache_key)
    if cached:
        return RedirectResponse(cached, status_code=302)

    result = await db.execute(select(Url).where(Url.short_code == short_code))
    url = result.scalar_one_or_none()

    if url is None:
        raise HTTPException(status_code=404, detail="Short URL not found.")

    if url.expires_at is not None and url.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=404, detail="Short URL has expired.")

    await cache.set(cache_key, url.original_url, ex=settings.CACHE_TTL_SECONDS)
    return RedirectResponse(url.original_url, status_code=302)
