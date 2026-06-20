from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Url
from app.schemas import ShortenRequest, ShortenResponse
from app.services.shortener import generate_short_code
from app.config import settings

router = APIRouter()


@router.post("/shorten", response_model=ShortenResponse, status_code=201)
async def shorten_url(
    payload: ShortenRequest,
    db: AsyncSession = Depends(get_db),
) -> ShortenResponse:
    expires_at = None
    if payload.expires_in_hours is not None:
        expires_at = datetime.now(timezone.utc) + timedelta(hours=payload.expires_in_hours)

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

    raise HTTPException(status_code=500, detail="Could not generate a unique short code. Try again.")


@router.get("/{short_code}")
async def redirect_url(
    short_code: str,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    result = await db.execute(select(Url).where(Url.short_code == short_code))
    url = result.scalar_one_or_none()

    if url is None:
        raise HTTPException(status_code=404, detail="Short URL not found.")

    if url.expires_at is not None and url.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=404, detail="Short URL has expired.")

    return RedirectResponse(url.original_url, status_code=302)
