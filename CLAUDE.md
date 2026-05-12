# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend (run from `backend/` with venv active)

```bash
source .venv/bin/activate
uvicorn app.main:app --reload                 # dev server
pytest                                        # all tests
pytest tests/test_auth_and_tasks.py           # single test file
alembic upgrade head                          # apply migrations
python scripts/new_migration.py description   # new migration (sequential NNNN_ prefix)
python scripts/seed.py                        # seed demo data
ruff check .                                  # lint (line-length 100)
```

### Frontend (run from `frontend/`)

```bash
npm run dev    # dev server on :5173
npm test       # Vitest (run once)
npm run build  # tsc + vite build
```

### Infrastructure

```bash
docker compose up -d postgres       # just DB for local dev
docker compose up --build           # full stack
docker compose exec backend alembic upgrade head
```

### Pre-commit checklist

Before every commit: `cd backend && pytest` + `cd frontend && npm test && npm run build`. For model changes, always run the **check-migration** agent first. Use the `/check-all` skill to run the full suite in one step before opening a PR.

## Architecture

**Backend** — layered FastAPI app in `backend/app/`:

- `main.py` — `create_app()` factory; registers routers and CORS. Import this factory (not the module-level `app`) in tests.
- `api/` — thin route handlers; `deps.py` provides `get_current_user` and `get_session` as FastAPI dependencies.
- `services/` — business logic (lists, tasks, notifications, history). No DB calls in routers.
- `repositories/auth.py` — upsert logic for OAuth identities.
- `models/` — SQLAlchemy 2.0 async ORM models. `base.py` provides `TimestampMixin` and `new_uuid`. `task_history.py` holds `TaskChangeRecord` + `FieldChange` (recorded on every `PATCH /tasks/{id}` and status update).
- `schemas/` — Pydantic request/response models (separate from ORM models).
- `websocket/notifications.py` — single WS endpoint; pushes `notification_batch` messages on connect and on a configurable interval.
- `core/security.py` — custom HMAC-SHA256 signed tokens (no third-party JWT library). Session cookie name is `ptm_session`.
- `api/errors.py` — shared HTTP exception helpers used across routers.

**Auth flow**: OAuth login → callback upserts `OAuthIdentity` + `User` → sets `ptm_session` HTTP-only cookie containing `{sub: user_id}`. The same signing mechanism protects the OAuth state parameter.

**Authorization**: all list/task endpoints check `user_id` ownership. Cross-account access returns **404**, not 403 (intentional — avoids leaking resource existence).

**Frontend** — feature-based React + TypeScript + Vite in `frontend/src/`:

- `api/client.ts` — single typed `api` object; always sends `credentials: 'include'`. Dispatches `auth:expired` custom event on 401.
- `auth/AuthContext.tsx` — global auth state.
- `features/` — self-contained UI components per domain (lists, tasks, notifications).
- `hooks/useNotificationsSocket.ts` — manages WebSocket lifecycle and reconnection.
- `types/domain.ts` — canonical TypeScript types shared across the app.

**Frontend naming**: components → `PascalCase.tsx`; hooks → `useThing.ts`; tests → `*.test.tsx`. Two-space indentation, single-quote imports.

## Key conventions

**Testing (backend)**: tests use in-memory SQLite via `conftest.py`. The `client` fixture calls `create_app()` and overrides `get_session` and `get_settings`. `TEST_AUTH_ENABLED=true` is set in test settings to enable `/auth/test-login`. Use the `login()` helper from `conftest.py` to authenticate before resource calls.

**Notification IDs**: formatted as `"{type}:{task_id}"` (e.g., `overdue:550e8400-...`). The `NotificationAck` table persists per-user dismissals; acknowledged notifications are excluded from subsequent WS batches unless `include_acknowledged: true` is sent.

**Migrations**: models must be imported in `backend/app/db/base.py` (which is itself imported in `alembic/env.py`) for autogenerate to detect changes.

**Task history**: both `PATCH /api/tasks/{task_id}` and `PATCH /api/tasks/{task_id}/status` snapshot field diffs into `task_history` / `task_history_fields` via `_capture_history` in `services/tasks.py`. Retrieve via `GET /api/tasks/{task_id}/history`.

**Local demo login**: set `TEST_AUTH_ENABLED=true` in `backend/.env` to enable the "Use local demo login" button. Never enable in production.

## Agents

**check-migration** — spawn this agent after any changes to `backend/app/models/` or `backend/alembic/versions/`. It runs `alembic check` and reports whether the current models are reflected in existing migrations. If a migration is missing, it returns the exact command to generate one. Do not create migrations without running this agent first.

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan at `.specify/memory/constitution.md`. The constitution supersedes CLAUDE.md when conflicts arise.
<!-- SPECKIT END -->
