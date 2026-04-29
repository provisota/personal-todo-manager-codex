# Repository Guidelines

## Project Structure & Module Organization

This is a full-stack personal to-do manager. The backend lives in `backend/` and uses FastAPI, SQLAlchemy async, Alembic, and PostgreSQL. Backend code is under `backend/app/`: routes in `app/api/`, models in `app/models/`, schemas in `app/schemas/`, services in `app/services/`, and WebSocket handling in `app/websocket/`. Backend tests are in `backend/tests/`.

The frontend lives in `frontend/` and uses React, TypeScript, and Vite. Source code is in `frontend/src/`, with routes in `src/routes/`, API code in `src/api/`, hooks in `src/hooks/`, and feature components in `src/features/`. Product specs are in `specs/`.

## Build, Test, and Development Commands

- `docker compose up -d postgres`: start the local PostgreSQL service.
- `cd backend && alembic upgrade head`: apply database migrations.
- `cd backend && python scripts/seed.py`: seed demo data.
- `cd backend && uvicorn app.main:app --reload`: run the API.
- `cd frontend && npm run dev`: run the Vite dev server.
- `cd frontend && npm run build`: type-check and build the frontend.
- `docker compose up --build`: run PostgreSQL, backend, and frontend together.

## Coding Style & Naming Conventions

Use Python 3.11+ with type hints. Keep Python lines at or below 100 characters, matching `backend/pyproject.toml` Ruff settings. Follow existing FastAPI layering: routers handle HTTP, services contain business logic, and models/schemas define persistence and API contracts.

Use TypeScript and React function components in the frontend. Components use `PascalCase.tsx`; hooks use `useThing.ts`; tests use `*.test.tsx`. Match the existing two-space indentation and single-quote import style.

## Testing Guidelines

Backend tests use `pytest` and `pytest-asyncio`; run them with `cd backend && pytest`. Frontend tests use Vitest and Testing Library; run them with `cd frontend && npm test`. Add tests beside changed behavior: backend tests in `backend/tests/`, frontend tests near the relevant source file.

## Commit & Pull Request Guidelines

The current history only shows `init commit`, so no strict commit convention is established. Use short, imperative commit messages such as `Add task filtering tests` or `Fix notification interval handling`.

Pull requests should include a concise summary, test results, and setup or migration notes. For UI changes, include screenshots or a short description. Link related issues when available and call out changes to `.env.example`, OAuth settings, or database migrations.

## Security & Configuration Tips

Do not commit real secrets. Copy `backend/.env.example` and `frontend/.env.example` for local configuration. For local demo login, set `TEST_AUTH_ENABLED=true`; keep production OAuth client secrets and `SESSION_SECRET` outside version control.
