from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Click, Url
from app.schemas import AnalyticsResponse, ClickOut

router = APIRouter()


@router.get("/analytics/{short_code}", response_model=AnalyticsResponse)
async def get_analytics(
    short_code: str,
    db: AsyncSession = Depends(get_db),
) -> AnalyticsResponse:
    result = await db.execute(select(Url).where(Url.short_code == short_code))
    url = result.scalar_one_or_none()
    if url is None:
        raise HTTPException(status_code=404, detail="Short URL not found.")

    clicks_result = await db.execute(
        select(Click)
        .where(Click.short_code == short_code)
        .order_by(Click.clicked_at.desc())
        .limit(10)
    )
    clicks = clicks_result.scalars().all()

    return AnalyticsResponse(
        short_code=url.short_code,
        original_url=url.original_url,
        click_count=url.click_count,
        created_at=url.created_at,
        expires_at=url.expires_at,
        recent_clicks=[
            ClickOut(
                clicked_at=c.clicked_at,
                referrer=c.referrer,
                ip_address=c.ip_address,
            )
            for c in clicks
        ],
    )
