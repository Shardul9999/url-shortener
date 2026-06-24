from datetime import datetime
from ipaddress import ip_address

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, field_validator

_BLOCKED_HOSTNAMES = {"localhost", "localhost.localdomain"}


class ShortenRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    original_url: AnyHttpUrl
    expires_in_hours: int | None = None

    @field_validator("original_url")
    @classmethod
    def reject_private_urls(cls, v: AnyHttpUrl) -> AnyHttpUrl:
        host = v.host
        if host is None:
            raise ValueError("URL must include a host.")
        if host.lower() in _BLOCKED_HOSTNAMES:
            raise ValueError("URLs pointing to localhost are not allowed.")
        # Strip IPv6 brackets before parsing.
        # try/except/else: else only runs when ip_address() succeeds (i.e. host
        # IS an IP), so our own ValueError from else propagates normally.
        try:
            addr = ip_address(host.strip("[]"))
        except ValueError:
            pass  # hostname, not a bare IP — allow it
        else:
            if addr.is_loopback or addr.is_private or addr.is_link_local:
                raise ValueError("URLs pointing to private or internal IP addresses are not allowed.")
        return v


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
