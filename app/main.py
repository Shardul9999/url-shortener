from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}
