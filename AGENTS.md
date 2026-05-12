# Repository Guidelines

## Project Structure & Module Organization

This is a full-stack personal to-do manager. The backend lives in `backend/` and uses
Python 3.11+, FastAPI, SQLAlchemy 2.0 async, Alembic, PostgreSQL, and FastAPI WebSockets.
Backend application code is under `backend/app/`:

- `app/main.py`: `create_app()` factory, CORS, routers, exception handlers, `/health`.
- `app/api/`: thin FastAPI routers for auth, lists, tasks, and shared dependencies/errors.
- `app/services/`: business logic for lists, tasks, notifications, and task history.
- `app/repositories/`: persistence helpers that do not contain business rules.
- `app/models/`: SQLAlchemy ORM models, including users, OAuth identities, lists, tasks,
  notification acknowledgements, and task history records.
- `app/schemas/`: Pydantic request/response models; keep these separate from ORM models.
- `app/websocket/`: `/ws/notifications` WebSocket handling.
- `app/core/`: settings and HMAC-SHA256 session/state token helpers.

Backend tests are in `backend/tests/`. Alembic migrations are in
`backend/alembic/versions/`; use `backend/scripts/new_migration.py` for sequentially named
migration files.

The frontend lives in `frontend/` and uses React 18, TypeScript, Vite, Vitest, Testing
Library, and `lucide-react`. Source code is under `frontend/src/`:

- `src/api/client.ts`: typed API client, `credentials: 'include'`, 401 `auth:expired` event.
- `src/auth/`: auth context and global auth state.
- `src/routes/`: top-level app/login/todo routes.
- `src/features/`: feature UI for lists, tasks, task history, and notifications.
- `src/hooks/`: reusable hooks such as WebSocket notification lifecycle management.
- `src/types/domain.ts`: canonical frontend domain types.

Product and implementation specs are in `specs/`. Speckit governance lives under
`.specify/`; `.specify/memory/constitution.md` supersedes other project docs when they
conflict.

## Build, Test, and Development Commands

Backend commands are run from `backend/`, normally with `.venv` active:

- `python3 -m venv .venv && source .venv/bin/activate`: create and enter the local venv.
- `pip install -e .`: install backend dependencies from `pyproject.toml`.
- `alembic upgrade head`: apply database migrations.
- `python scripts/new_migration.py description`: create a new sequential Alembic migration.
- `python scripts/seed.py`: seed demo data.
- `uvicorn app.main:app --reload`: run the API on `http://localhost:8000`.
- `pytest`: run backend tests.
- `pytest tests/test_auth_and_tasks.py`: run a single backend test file.
- `ruff check .`: lint using the backend Ruff configuration, when Ruff is installed.

Frontend commands are run from `frontend/`:

- `npm install`: install frontend dependencies.
- `npm run dev`: run the Vite dev server on `http://localhost:5173`.
- `npm test`: run Vitest once.
- `npm run build`: run `tsc -b` and build with Vite.
- `npm run preview`: preview the production build.

Infrastructure commands from the repository root:

- `docker compose up -d postgres`: start only PostgreSQL for host-run backend/frontend.
- `docker compose up --build`: run PostgreSQL, backend, and frontend together.
- `docker compose exec backend alembic upgrade head`: migrate the containerized backend DB.
- `docker compose exec backend python scripts/seed.py`: seed the containerized backend DB.

For local development, copy `backend/.env.example` to `backend/.env` and
`frontend/.env.example` to `frontend/.env`.

## Architecture & Domain Conventions

Keep the backend layered. Route handlers validate input, depend on `get_current_user` and
`get_session`, delegate to services, and return Pydantic schemas. Business logic belongs in
`services/`. Routers must not perform direct database work. Repositories are for persistence
helpers only, not business rules.

Authentication uses Google OpenID Connect, GitHub OAuth, and a signed HTTP-only
`ptm_session` cookie. Tokens are custom HMAC-SHA256 values implemented in
`app/core/security.py`; do not add a JWT library. The same cookie is used by REST and the
notifications WebSocket.

All list/task operations must enforce `user_id` ownership. Cross-account resource access
intentionally returns `404`, not `403`, to avoid leaking resource existence.

Task history is part of the current product surface. `PATCH /api/tasks/{task_id}` and
`PATCH /api/tasks/{task_id}/status` record field diffs through `services/tasks.py`; history
is read with `GET /api/tasks/{task_id}/history`. Keep history schemas and frontend
`TaskHistory*` components aligned when changing this contract.

Notifications use IDs formatted as `"{type}:{task_id}"`, for example
`overdue:550e8400-...`. `NotificationAck` stores per-user dismissals; acknowledged
notifications are omitted unless the WebSocket subscription asks for them.

## Coding Style & Naming Conventions

Use Python type hints and keep Python lines at or below 100 characters, matching
`backend/pyproject.toml`. SQLAlchemy models use 2.0 async conventions. Import every ORM
model in `backend/app/db/base.py` so Alembic autogenerate can see metadata. Use
`TimestampMixin` from `models/base.py` where timestamps are relevant.

Use TypeScript React function components. Components use `PascalCase.tsx`; hooks use
`useThing.ts`; tests use `*.test.tsx`. Match the existing two-space indentation and
single-quote import style. Prefer existing API, auth, feature, and type patterns before
adding abstractions or dependencies.

New dependencies require a concrete reason. This is a private MVP; keep changes small and
avoid abstractions for hypothetical future scale.

## Testing Guidelines

Backend tests use `pytest` and `pytest-asyncio`. Most tests run against in-memory SQLite via
`backend/tests/conftest.py`; the `client` fixture uses `create_app()` and overrides settings
and DB session dependencies. Use the `login()` helper from `conftest.py` before protected
resource calls. PostgreSQL-specific integration coverage is in
`backend/tests/test_postgres_integration.py` and only runs when `POSTGRES_TEST_DATABASE_URL`
is set.

Frontend tests use Vitest, Testing Library, JSDOM, and setup from
`frontend/src/test/setup.ts`. Add tests next to the changed frontend behavior.

Before committing, run:

- `cd backend && pytest`
- `cd frontend && npm test`
- `cd frontend && npm run build`

For backend model or migration changes, run the `check-migration` agent before committing
and ensure a matching Alembic migration exists.

## Commit & Pull Request Guidelines

The repository now has short imperative history entries such as `updated CLAUDE.md`,
`Added Task history feature`, and `Updated history UI table modal`. Continue using concise,
imperative commit messages, for example `Add task filtering tests` or
`Fix notification interval handling`.

Pull requests should include a concise summary, test results, and setup or migration notes.
For UI changes, include screenshots or a short description of the changed behavior. Link
related issues/specs when available and call out changes to `.env.example`, OAuth settings,
database migrations, or WebSocket/API contracts.

## Security & Configuration Tips

Do not commit real secrets. Keep OAuth client secrets and `SESSION_SECRET` outside version
control. `TEST_AUTH_ENABLED=true` enables the local demo login endpoint and button; never
enable it in staging or production.

Backend environment variables are documented in `backend/.env.example`; key values include
`DATABASE_URL`, `SESSION_SECRET`, `COOKIE_SECURE`, `CORS_ALLOWED_ORIGINS`,
`CORS_ALLOWED_ORIGIN_REGEX`, `WS_NOTIFICATION_INTERVAL_SECONDS`, and OAuth client settings.
Frontend environment variables are documented in `frontend/.env.example` and currently
include `VITE_API_BASE_URL` and `VITE_WS_BASE_URL`.
