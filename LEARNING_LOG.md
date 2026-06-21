# URL Shortener — Learning Log

A session-by-session record of what was built, why decisions were made, and what you should know for interviews or general backend knowledge.

---

## Session 1 — Project Skeleton, Models, Migration, Core Endpoints

### Files created
`app/config.py` · `app/main.py` · `app/database.py` · `app/models.py` · `app/schemas.py` · `app/services/shortener.py` · `app/routers/urls.py` · `alembic.ini` · `alembic/env.py` · `alembic/script.py.mako` · first Alembic migration

---

### 1. Pydantic Settings — reading config from environment

**What we did:** Used `pydantic-settings` `BaseSettings` to load all environment variables (`DATABASE_URL`, `REDIS_URL`, etc.) into a typed `Settings` class, with a module-level `settings` singleton.

**Why it matters:**
- Never call `os.environ` directly inside business logic — it makes code untestable and scatters config reading everywhere.
- `BaseSettings` automatically reads from `.env` files AND real environment variables, with env vars taking priority (so Docker/prod env vars override the `.env` file).
- Pydantic validates and type-converts values at startup — if `RATE_LIMIT_PER_MINUTE` is missing or not an int, the app crashes immediately with a clear error rather than failing silently at runtime.

**Interview angle:** "How do you manage configuration in a Python API?" → Pydantic Settings with a singleton, injected via import. Not `os.environ`, not a raw config file parser.

---

### 2. Pydantic v2 vs v1 syntax — know the difference

**What we did:** Used `model_config = ConfigDict(...)` and typed fields directly. Never used v1's `class Config` or `@validator`.

| v1 (old — don't use)         | v2 (correct)                        |
|------------------------------|-------------------------------------|
| `class Config: orm_mode = True` | `model_config = ConfigDict(from_attributes=True)` |
| `@validator('field')`        | `@field_validator('field')`         |
| `class Config: env_file='.env'` | `model_config = ConfigDict(env_file='.env')` |

**Interview angle:** Pydantic v2 was a full rewrite (Rust core, 5-50x faster). If asked about performance of data validation in Python, this is a real answer.

---

### 3. SQLAlchemy 2.0 async style — why and how

**What we did:** Used `create_async_engine`, `async_sessionmaker`, `AsyncSession`, and `await session.execute(select(...))`. Used `Mapped[type]` and `mapped_column()` for model definitions.

**Why async for DB calls:**
- Database I/O is blocking by nature. In a sync setup, a slow query freezes the entire thread.
- With `async def` + `await`, FastAPI can handle other requests while waiting for the DB to respond.
- Under load, this is the difference between 50 concurrent users and 500.

**SQLAlchemy 2.0 vs 1.x:**
| 1.x (old)                    | 2.0 (correct)                        |
|------------------------------|--------------------------------------|
| `session.query(User).filter(...)` | `select(User).where(...)`        |
| `Session` (sync)             | `AsyncSession`                       |
| `db.query(Url).first()`      | `await db.execute(select(Url))` then `.scalar_one_or_none()` |

**`expire_on_commit=False` on the session maker:** Without this, SQLAlchemy expires all loaded attributes after a commit. In async code, accessing an expired attribute triggers another DB round-trip — which is illegal outside an active session context. This setting prevents that footgun.

**Interview angle:** "What's the difference between `select()` and `session.query()`?" → `query()` is the legacy 1.x API, `select()` is the 2.0 Core-style API that works with both sync and async sessions.

---

### 4. Alembic with async SQLAlchemy

**What we did:** Wrote an async-compatible `env.py` that wraps migrations in `asyncio.run(run_migrations_online())`, uses `create_async_engine`, and calls `await connection.run_sync(do_run_migrations)`.

**Why this is non-trivial:**
- Alembic itself is synchronous — it was designed before async Python existed.
- The trick is `run_sync()`: it hands a sync-callable to the async connection, which runs it in a thread pool under the hood.
- Without this pattern, you'd get `greenlet_spawn` errors or be forced to use a sync engine just for migrations.

**Key pattern:**
```python
async with connectable.connect() as connection:
    await connection.run_sync(do_run_migrations)
```

**`poolclass=pool.NullPool` in migration engine:** Migrations are one-shot scripts. Using `NullPool` means connections are not pooled — each migration step gets a fresh connection and releases it immediately. This avoids leaving idle connections open after the migration completes.

**Interview angle:** "How do you run Alembic migrations with an async SQLAlchemy setup?" → This exact pattern. Many candidates don't know Alembic needs special handling for async.

---

### 5. Docker networking — container hostnames vs localhost

**Bug hit:** Running `alembic upgrade head` from the host machine failed with `getaddrinfo failed` because `DATABASE_URL` in `.env` uses host `db` (the Docker Compose service name), which only resolves inside the Docker network.

**How Docker Compose networking works:**
- Docker Compose creates a private network for the stack.
- Services can reach each other by their service name (e.g., `db`, `cache`).
- From your **host machine**, those names don't exist — you must use `localhost` and the published port.

**Rule of thumb:**
- Inside Docker (app container talking to db container): `db:5432`
- From host machine (your terminal, alembic, psql): `localhost:5432`

**Interview angle:** Very common in take-home projects and system design rounds. "Why can't my app connect to the database?" → check whether you're using the right hostname for the context (container vs host).

---

### 6. FastAPI route ordering — a real bug we hit

**Bug hit:** `GET /health` was returning `{"detail": "Short URL not found."}` because `GET /{short_code}` was registered before `/health`. FastAPI matched "health" as a short code value.

**Root cause:** `app.include_router(urls.router)` was called before `@app.get("/health")` was defined. FastAPI evaluates routes in registration order.

**Fix:** Register specific/literal routes before wildcard/parameterized ones.

```python
# WRONG — /{short_code} registered first, catches /health
app.include_router(urls.router)

@app.get("/health")
async def health_check(): ...

# CORRECT — /health registered first
@app.get("/health")
async def health_check(): ...

app.include_router(urls.router)
```

**Interview angle:** Classic FastAPI/Flask gotcha. "Why is my static route returning a 404?" → route ordering. Examiners love this because it shows you've actually built something, not just read docs.

---

### 7. Short code generation — `secrets` vs `random`

**What we did:** Used `secrets.choice()` over a custom alphabet that excludes visually ambiguous characters (`0`, `O`, `1`, `l`, `I`).

**Why `secrets` not `random`:**
- `random` uses a Mersenne Twister — a deterministic PRNG seeded from system time. An attacker who knows the seed can predict future outputs.
- `secrets` uses the OS's cryptographically secure random source (`/dev/urandom` on Linux). Outputs are not predictable.
- For any token, short code, or ID that a user will see in a URL, use `secrets`.

**Collision retry pattern:** On `IntegrityError` (unique constraint violation), we roll back and retry up to 5 times. With a 6-char code from a 54-char alphabet (54^6 ≈ 24 billion combinations), collisions are astronomically rare — but the retry guard makes it correct regardless.

**Interview angle:** "How do you generate a short code safely?" → `secrets.choice`, custom alphabet without ambiguous chars, retry on collision, unique DB constraint as the source of truth.

---

### 8. Virtual environment vs system Python

**Problem hit:** VS Code's Pylance was showing import errors for `sqlalchemy`, `fastapi`, etc. even after `pip install -r requirements.txt`.

**Why it happened:** `pip install` was running against the system Python, not the project's virtual environment. VS Code's type checker uses whichever Python interpreter it's pointed at — and the system Python had no packages installed.

**Fix:**
1. Create a venv: `python -m venv .venv`
2. Install into it: `.venv\Scripts\pip install -r requirements.txt`
3. In VS Code: `Ctrl+Shift+P` → "Python: Select Interpreter" → pick `.venv`

**Additional wrinkle:** Some packages in `requirements.txt` were pinned to versions that had no pre-built wheels for Python 3.13 (e.g., `asyncpg==0.29.0` only supports up to 3.12). The actual app runs on Python 3.11 inside Docker — the venv is just for local IDE tooling, so we installed without strict version pins locally.

**Interview angle:** "What is a virtual environment and why do you need one?" → Isolates project dependencies so different projects can use different versions of the same library without conflict.

---

### 9. `HttpUrl` vs `str` for URL fields

**What we did:** Used `HttpUrl` for `ShortenRequest.original_url` instead of plain `str`.

**What Pydantic's `HttpUrl` does:**
- Validates the value is a well-formed HTTP/HTTPS URL.
- Normalises it (adds trailing slash to bare domains, etc.) — which is why the stored URL becomes `https://example.com/` even if you passed `https://example.com`.
- Rejects obviously bad input (`"not a url"`, `"ftp://..."`) before it touches the DB.

**Interview angle:** Input validation should happen at the boundary (the request schema), not inside business logic. Pydantic schemas are your first line of defence.

---

### 10. `server_default` vs `default` in SQLAlchemy

**What we did:** Used `server_default=func.now()` for timestamp columns, and `default=0` for `click_count`.

| | `default=` | `server_default=` |
|---|---|---|
| Where it runs | Python side, before INSERT | DB side, as part of the SQL DDL |
| Appears in migration | No | Yes (as `DEFAULT now()`) |
| Works without Python | No | Yes (raw SQL inserts also get the default) |

For timestamps, `server_default` is correct — the DB clock is the authoritative source, and the default is enforced at the schema level.

**Interview angle:** Subtle but shows depth. "Where should default timestamps come from?" → The database, not application code, so every row is consistent regardless of how it was inserted.

---

## Session 2 — Redis Cache, Rate Limiter (Sliding Window), PowerShell Gotchas

### Files created / modified
`app/cache.py` (new) · `app/services/ratelimit.py` (new) · `app/routers/urls.py` (cache-aside + rate limit added)

---

### 1. Redis connection pooling — why a pool, not a fresh connection per request

**What we did:** Created a module-level `ConnectionPool` once at import time, then passed it to a `Redis` client inside `get_redis()`.

```python
_pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)

async def get_redis() -> redis.Redis:
    async with redis.Redis(connection_pool=_pool) as client:
        yield client
```

**Why pooling matters:**
- Opening a TCP connection to Redis takes time (DNS lookup, TCP handshake, auth). Doing this per request adds ~5–20ms of overhead every single time.
- A pool keeps a set of connections open and reuses them. A request borrows one, uses it, returns it — no handshake overhead.
- Without a pool, under load you'd exhaust OS file descriptors and Redis's connection limit simultaneously.

**`decode_responses=True`:** Redis stores and returns raw bytes. This flag makes the client automatically decode bytes to `str` — no manual `.decode('utf-8')` scattered everywhere.

**Interview angle:** "How do you connect to Redis in a FastAPI app?" → Module-level connection pool, not a new connection per request. Same principle applies to any connection-based resource (DB, message broker, etc.).

---

### 2. Cache-aside pattern (lazy loading)

**What we did:** On `GET /{short_code}`, check Redis first. On hit, return immediately without touching Postgres. On miss, query Postgres, write result to Redis with a TTL, then redirect.

```
Request → Redis hit?  → YES → redirect (no DB)
                      → NO  → query DB → write to Redis → redirect
```

**Why cache-aside, not write-through:**
- Write-through updates the cache on every write. Cache-aside only populates the cache when data is actually read — so URLs that are never visited don't waste Redis memory.
- For a URL shortener, most URLs get most of their traffic shortly after creation. Cache-aside naturally handles this without pre-warming.

**Key naming convention:** `url:{short_code}` — namespace your keys. When you later add rate limiter keys (`ratelimit:{ip}`), analytics keys, etc., namespacing prevents collisions and makes `redis-cli KEYS "url:*"` useful for debugging.

**Measured result from this project:**
- Cache miss (first hit, goes to Postgres): ~40ms
- Cache hit (subsequent hits, Redis only): ~7ms
- **6x latency improvement** on repeat requests

**Interview angle:** "How did you implement caching?" → Cache-aside pattern, Redis sorted set for rate limiting, TTL-based expiry. Quote the 6x number — concrete metrics stand out.

---

### 3. Sliding window rate limiter with Redis sorted sets

**What we did:** Each request from an IP is stored as a member in a Redis sorted set, with the Unix timestamp as the score. The window is enforced by removing members older than `now - window_seconds` before counting.

```
Key:    ratelimit:{ip}
Score:  time.time()          ← Unix timestamp (float)
Member: "{timestamp}:{uuid}" ← unique per request
```

**Why sorted sets:**
- A simple counter (`INCR`) only tells you total count — it can't tell you *when* requests happened, so you can't implement a sliding window.
- A sorted set with timestamps as scores lets you `ZREMRANGEBYSCORE key -inf (now - 60)` to instantly evict expired entries, then `ZCARD` to count what's left in the window.
- This is a true sliding window — not a fixed 60-second bucket that resets on the clock minute, but a rolling 60 seconds from *now*.

**Fixed window vs sliding window:**

| | Fixed Window | Sliding Window |
|---|---|---|
| Implementation | `INCR` + `EXPIRE` | Sorted set + `ZREMRANGEBYSCORE` |
| Weakness | Burst at window boundary (100 req at 0:59, 100 req at 1:01) | No boundary burst |
| Memory | O(1) | O(requests in window) |
| Interview preference | Simpler to explain | Correct to implement |

**Why `uuid4()` in the member:** Two concurrent requests from the same IP at the same millisecond would have identical timestamps. If the member were just the timestamp, `ZADD` would overwrite the existing entry (same score, same member = update, not add). The UUID suffix guarantees uniqueness so every request gets its own slot.

**Interview angle:** "What's the difference between a fixed window and a sliding window rate limiter?" → Fixed window can be double-exploited at the boundary. Sliding window uses a sorted set with timestamps as scores to track the exact time of each request.

---

### 4. Race conditions — TOCTOU and why Lua fixes it

**The question asked this session:** "Why does a naive GET count → check → INCR have a race condition, and how does Lua fix it?"

**The race (check-then-act):**

```
Request A          Request B
---------          ---------
GET count → 99
                   GET count → 99
99 < 100 ✅
                   99 < 100 ✅
INCR → 100
                   INCR → 101  ← both slipped through
```

Both requests read 99 before either increments. This is called a **TOCTOU — Time Of Check To Time Of Use** race. The gap between checking and acting is where the race lives.

**Why pipeline (MULTI/EXEC) doesn't fully solve it:**
- A pipeline sends all commands in one batch — you can't read an intermediate result and branch on it.
- You'd have to INCR first, then check — meaning you've already counted the request before deciding to block it. Requires a second round-trip to undo.

**Why Lua is the correct fix:**
- Redis is single-threaded for command execution.
- A Lua script running on Redis is atomic — no other client command can execute between any two lines of the script.
- This means the ZREMRANGEBYSCORE → ZCARD → conditional ZADD is one indivisible operation. Request B physically waits until Request A's script finishes before it can read the count.

```lua
redis.call('ZREMRANGEBYSCORE', key, '-inf', now - window)
local count = tonumber(redis.call('ZCARD', key))
if count < limit then
    redis.call('ZADD', key, now, member)
    return 1   -- allow
end
return 0       -- block
```

**Interview angle (one sentence):** "The naive approach has a TOCTOU gap between reading the count and writing the increment — Lua eliminates it because Redis executes the entire script atomically, so no other command can interleave between the check and the write."

---

### 5. PowerShell vs Bash — a practical difference for backend developers

**Problems hit this session:**
- `curl` in PowerShell is an alias for `Invoke-WebRequest`, not the real curl binary. Flags like `-w`, `-o /dev/null` don't work.
- `/dev/null` doesn't exist on Windows — use `NUL`.
- Even `curl.exe` sometimes still gets intercepted depending on PATH ordering.

**Fixes:**
- Use `curl.exe` explicitly, or call via full path `& "C:\Windows\System32\curl.exe"`
- Use `NUL` instead of `/dev/null`
- For scripting loops, PowerShell equivalent of `for i in {1..110}` is `1..110 | ForEach-Object { ... }`
- For grouping output, PowerShell equivalent of `| sort | uniq -c` is `| Group-Object | Select-Object Count, Name`

**Why this matters:** Backend dev interviews often involve live debugging on whatever OS the interviewer's machine runs. Knowing these differences shows real-world experience — not just tutorial knowledge.

---

### 6. HTTP 429 and the Retry-After header

**What we did:** When the rate limit is exceeded, raise a 429 with a `Retry-After: 60` header.

**Why Retry-After matters:**
- HTTP spec says 429 responses *should* include `Retry-After` — the number of seconds the client should wait before retrying.
- Well-behaved clients (curl, browsers, API clients) can read this and back off automatically instead of hammering the server in a retry loop.
- Without it, a client that retries immediately just burns through 429s, creating more load.

**Interview angle:** "How do you implement rate limiting in an API?" → Redis sliding window, 429 status, `Retry-After` header. Three parts — most candidates only mention the first one.

---

### 7. Measuring cache performance — the right way to state it on a resume

**What we measured:**
- Cache miss (Postgres round-trip): ~40ms
- Cache hit (Redis only): ~7ms
- Ratio: ~6x improvement

**How to state it on a resume:**
> "Implemented Redis cache-aside on the URL redirect endpoint — reduced repeat-request latency from ~40ms to ~7ms (6x improvement) by serving cached redirects from Redis, eliminating the Postgres round-trip on cache hits."

**Don't put raw milliseconds without context** — they depend on hardware, network, and load. The mechanism + ratio is what interviewers evaluate. If asked, you can mention your local Docker measurements as a baseline.

---
