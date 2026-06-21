import pytest
import pytest_asyncio
import redis.asyncio as redis
from httpx import AsyncClient, ASGITransport
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.main import app
from app.database import Base, get_db
from app.cache import get_redis

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/urlshortener_test"
TEST_REDIS_URL = "redis://localhost:6379/1"  # index 1 — separate from dev (index 0)

# NullPool: every connect() creates a fresh connection; no connection is ever
# returned to a pool. This prevents "Future attached to a different loop" errors
# that arise when pooled connections established in one asyncio loop are reused
# in a different loop (pytest-asyncio uses per-test loops by default).
_test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)


# ---------------------------------------------------------------------------
# Tables — created once before the session, dropped after
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_tables():
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _test_engine.dispose()


# ---------------------------------------------------------------------------
# DB session — wraps each test in a transaction + savepoints so that
# app-level commits don't escape, and everything rolls back after the test.
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture()
async def db_session() -> AsyncSession:
    async with _test_engine.connect() as conn:
        await conn.begin()
        session = AsyncSession(bind=conn, join_transaction_mode="create_savepoint")
        try:
            yield session
        finally:
            await session.close()
            await conn.rollback()


# ---------------------------------------------------------------------------
# Redis — DB index 1, flushed clean before each test
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture()
async def redis_client() -> redis.Redis:
    client = redis.Redis.from_url(TEST_REDIS_URL, decode_responses=True)
    await client.flushdb()
    yield client
    await client.aclose()


# ---------------------------------------------------------------------------
# HTTP test client — dependency overrides point to test DB and test Redis
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture()
async def client(db_session: AsyncSession, redis_client: redis.Redis) -> AsyncClient:
    async def _override_get_db():
        yield db_session

    async def _override_get_redis():
        yield redis_client

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_redis] = _override_get_redis

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
