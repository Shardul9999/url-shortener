import time
import uuid

import redis.asyncio as redis

# Atomic sliding-window check-and-increment via Lua.
# Redis executes Lua scripts as a single unit — no other command
# can interleave between the ZREMRANGEBYSCORE, ZCARD, and ZADD.
_SLIDING_WINDOW_SCRIPT = """
local key     = KEYS[1]
local now     = tonumber(ARGV[1])
local window  = tonumber(ARGV[2])
local limit   = tonumber(ARGV[3])
local member  = ARGV[4]

redis.call('ZREMRANGEBYSCORE', key, '-inf', now - window)
local count = tonumber(redis.call('ZCARD', key))

if count < limit then
    redis.call('ZADD', key, now, member)
    redis.call('EXPIRE', key, window)
    return 1
end
return 0
"""


async def is_allowed(
    r: redis.Redis,
    key: str,
    limit: int,
    window_seconds: int,
) -> bool:
    now = time.time()
    member = f"{now}:{uuid.uuid4()}"
    result = await r.eval(
        _SLIDING_WINDOW_SCRIPT,
        1,  # number of KEYS
        key,  # KEYS[1]
        now,  # ARGV[1]
        window_seconds,  # ARGV[2]
        limit,  # ARGV[3]
        member,  # ARGV[4] — unique per request so concurrent hits don't overwrite
    )
    return bool(result)
