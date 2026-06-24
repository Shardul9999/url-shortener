from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import analytics, urls

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}


app.include_router(urls.router)
app.include_router(analytics.router)
