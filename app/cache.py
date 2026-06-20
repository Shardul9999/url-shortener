import redis.asyncio as redis

from app.config import settings

_pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)


async def get_redis() -> redis.Redis:
    async with redis.Redis(connection_pool=_pool) as client:
        yield client
