# PROJECT_CONTEXT.md
Paste this entire file into every new Claude Code / Antigravity / Cursor session before asking it to write code.

---

## Project
URL Shortener + Analytics API — resume-grade backend project demonstrating async Python, caching, rate limiting, and containerized deployment.

## Stack (exact versions — do not suggest alternatives or newer/older versions)
- Python 3.11
- FastAPI 0.111.0
- Uvicorn 0.29.0 (ASGI server)
- SQLAlchemy 2.0.30 (async style, NOT 1.x syntax)
- Alembic 1.13.1 (migrations)
- asyncpg 0.29.0 (Postgres async driver)
- redis-py 5.0.4 (NOT aioredis package — redis-py 5.x has native async support via `redis.asyncio`)
- Pydantic 2.7.1 (v2 syntax — `model_config`, NOT v1 `class Config`)
- pydantic-settings 2.2.1
- PostgreSQL 16 (via Docker)
- pytest 8.2.0 + pytest-asyncio 0.23.6
- httpx 0.27.0 (for async test client)

## Folder structure (fixed — do not deviate, do not invent new top-level folders)
```
url-shortener/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app instance, includes routers
│   ├── config.py            # pydantic-settings Settings class, reads .env
│   ├── models.py            # SQLAlchemy ORM models (Url, Click)
│   ├── schemas.py           # Pydantic request/response models
│   ├── database.py          # async engine, async session factory, get_db dependency
│   ├── cache.py             # Redis async connection + get_redis dependency
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── urls.py          # POST /shorten, GET /{code}
│   │   └── analytics.py     # GET /analytics/{code}
│   └── services/
│       ├── __init__.py
│       ├── shortener.py     # short code generation logic
│       └── ratelimit.py     # sliding window rate limiter (Redis)
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # pytest fixtures: test db, test redis, test client
│   ├── test_urls.py
│   └── test_ratelimit.py
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── .env                      # gitignored — never read/write actual secrets here
├── .gitignore
└── README.md
```

## Database schema (do not change column names without updating this file)
**urls table**
- id: UUID, primary key
- short_code: VARCHAR(10), unique, indexed
- original_url: TEXT, not null
- created_at: TIMESTAMP, default now()
- expires_at: TIMESTAMP, nullable
- click_count: INTEGER, default 0

**clicks table**
- id: UUID, primary key
- short_code: VARCHAR(10), indexed, foreign key reference (logical, not enforced)
- clicked_at: TIMESTAMP, default now()
- referrer: TEXT, nullable
- ip_address: VARCHAR(45), nullable

## Environment variables (exact names — use these, never invent new ones)
```
DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/urlshortener
REDIS_URL=redis://cache:6379/0
SECRET_KEY=change-me-in-production
BASE_URL=http://localhost:8000
RATE_LIMIT_PER_MINUTE=100
CACHE_TTL_SECONDS=3600
```

## Hard rules for AI (do not violate these)
1. Always use `async def` for route handlers and DB/Redis calls. Never suggest sync (`def`) for I/O operations.
2. Always use SQLAlchemy 2.0 async syntax: `select()`, `AsyncSession`, `await session.execute(...)`. Never use legacy `Query` API or sync `Session`.
3. Always use `redis.asyncio` import path from redis-py 5.x. Never suggest `import aioredis` (deprecated, merged into redis-py).
4. Always use Pydantic v2 syntax: `model_config = ConfigDict(...)`, `field_validator`. Never use Pydantic v1 `class Config` or `@validator`.
5. Never invent new files or folders outside the structure above. If a new file seems needed, say so explicitly and ask before creating it.
6. Never modify more than the one file/function explicitly asked about in a given prompt.
7. All responses from the API must go through Pydantic schemas — never return raw SQLAlchemy model objects directly.
8. Database writes must use explicit `await session.commit()` — never rely on autocommit.

---

## SESSION STATE (update this section every session — this is what changes)

### Already built (working, tested)
- [✅] Docker Compose stack boots (api + db + cache)
- [✅] FastAPI skeleton + health check
- [✅] SQLAlchemy models + Alembic migration
- [✅] POST /shorten endpoint
- [✅] GET /{code} redirect endpoint
- [✅] Redis cache on redirect
- [✅] Rate limiter
- [ ] Async click tracking
- [ ] GET /analytics/{code}
- [✅] Tests
- [✅] CI pipeline
- [ ] Deployed

### Current task (fill this in right now, every session)
> Example: "Writing app/cache.py — the Redis async connection module and get_redis dependency. Nothing else yet."

### Known issues / blockers
> Example: "Alembic autogenerate isn't picking up the Click model — need to check if it's imported in env.py"
