from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl


class ShortenRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    original_url: HttpUrl
    expires_in_hours: int | None = None


class ShortenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    short_code: str
    short_url: str
    original_url: str


class ClickOut(BaseModel):
    clicked_at: datetime
    referrer: str | None
    ip_address: str | None


class AnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    short_code: str
    original_url: str
    click_count: int
    created_at: datetime
    expires_at: datetime | None
    recent_clicks: list[ClickOut]
