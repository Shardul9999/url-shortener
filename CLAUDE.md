# AI Agent Rules — url-shortener project

This file is read automatically by Claude Code (as `CLAUDE.md` in project root).
For Antigravity / Cursor / other tools: paste this content into their
"custom instructions" / "rules" / "memory" settings for this project.

---

## Before doing anything else
1. Read `PROJECT_CONTEXT.md` in this same folder. It has the stack, folder
   structure, schema, and current session state. Treat it as ground truth.
2. If `PROJECT_CONTEXT.md` says a file/feature is already built, do not
   regenerate it from scratch — read the existing file first and edit it.
3. If asked to do something that conflicts with PROJECT_CONTEXT.md
   (wrong library version, wrong folder, wrong pattern), say so explicitly
   instead of silently complying.

## Scope discipline
- Touch only the file(s) explicitly named in the current task.
- Do not refactor, "improve," or rename things outside the current task
  unless asked.
- Do not create new files or folders beyond what's listed in
  PROJECT_CONTEXT.md's folder structure. If a new file genuinely seems
  necessary, stop and ask first.
- One logical change per commit. Do not bundle unrelated edits.

## Technical rules (non-negotiable for this project)
- Async everywhere for I/O: `async def` route handlers, `await` on all
  DB and Redis calls. Never sync DB sessions.
- SQLAlchemy 2.0 style only: `select(Model).where(...)`, `AsyncSession`,
  `await session.execute(...)`, explicit `await session.commit()`.
  Never SQLAlchemy 1.x `Query` API.
- redis-py 5.x only: `import redis.asyncio as redis`. Never
  `import aioredis` — that package is deprecated and merged upstream.
- Pydantic v2 only: `model_config = ConfigDict(...)`, `field_validator`.
  Never v1 `class Config` or `@validator`.
- All API responses serialize through a Pydantic schema. Never return a
  raw SQLAlchemy ORM object directly from a route.
- Read environment variables only via `app/config.py`'s `Settings` class.
  Never call `os.environ` directly inside business logic.

## When writing code
- Match the existing code style in the file you're editing before
  introducing a new pattern.
- Add type hints to every function signature.
- If you're not sure which library version's syntax to use, check
  `requirements.txt` in this project — it has every version pinned.
- Write a docstring for any function whose purpose isn't obvious from
  its name and signature.

## When you don't know something
- If the task requires information not in PROJECT_CONTEXT.md or the
  current file (e.g. "what does the analytics endpoint return"), ask
  rather than guessing a plausible-sounding answer.
- Never invent an API method, library function, or CLI flag you are not
  certain exists. If uncertain, say "I'm not fully sure this exists,
  let's verify" rather than presenting a guess as fact.

## Testing expectations
- Every new endpoint needs at least one happy-path test and one
  failure-path test in the matching `tests/test_*.py` file.
- Tests use `pytest-asyncio` and the fixtures defined in
  `tests/conftest.py` — don't create parallel/duplicate fixtures.
- Run tests after writing them. Don't claim something works without
  having executed it.

## Multi-step / agentic tasks (Antigravity specifically)
- Before executing a multi-file plan, list the files you intend to
  create or modify and wait for confirmation if the list is longer than
  2 files.
- After each file is written, briefly state what changed before moving
  to the next file — don't silently chain 5+ edits with no checkpoint.
- If a planned step turns out to require deviating from
  PROJECT_CONTEXT.md's folder structure, stop and flag it instead of
  proceeding.

## End of session
- Before ending a session, summarize what was built/changed so the user
  can update the "Already built" checklist in PROJECT_CONTEXT.md.
