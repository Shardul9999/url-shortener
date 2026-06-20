from fastapi import FastAPI

from app.routers import urls

app = FastAPI()


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}


app.include_router(urls.router)
