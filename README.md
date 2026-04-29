# Personal To-Do Manager
<!-- TOC -->
* [Personal To-Do Manager](#personal-to-do-manager)
  * [Stack](#stack)
  * [Local Setup](#local-setup)
    * [Start PostgreSQL:](#start-postgresql)
    * [Backend:](#backend)
    * [Frontend:](#frontend)
    * [Open:](#open)
  * [OAuth Configuration](#oauth-configuration)
    * [Google](#google)
    * [GitHub](#github)
  * [Environment Variables](#environment-variables)
  * [API Summary](#api-summary)
  * [Deletion Rule](#deletion-rule)
  * [WebSocket](#websocket)
  * [Tests](#tests)
  * [Docker](#docker)
<!-- TOC -->

Full-stack MVP for private personal project/task management. Users sign in with Google or GitHub SSO, manage private lists and tasks, search/filter tasks, and receive WebSocket notifications for overdue and due-soon work.

## Stack

- Backend: Python, FastAPI, SQLAlchemy async, Alembic, PostgreSQL.
- Frontend: React, TypeScript, Vite.
- Auth: Google OpenID Connect and GitHub OAuth.
- Real time: FastAPI WebSocket endpoint.
- Tests: pytest for backend, Vitest/Testing Library for frontend.

## Local Setup

### Start PostgreSQL:

```bash
docker compose up -d postgres
```

### Backend:

First run:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload
```
then
```bash
cd backend
uvicorn app.main:app --reload
```

### Frontend:

First run:
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
then
```bash
cd frontend
npm run dev
```

Open:
- Frontend: `http://localhost:5173`
- API docs: `http://localhost:8000/docs`

For local-only demo login, set `TEST_AUTH_ENABLED=true` in `backend/.env` and use "Use local demo login" on the login page.

## OAuth Configuration

### Google

Create OAuth credentials in Google Cloud Console:

- Application type: Web application.
- Authorized redirect URI: `http://localhost:8000/auth/google/callback`.
- Scopes: `openid`, `email`, `profile`.

Set:

```env
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

### GitHub

Create a GitHub OAuth App:

- Homepage URL: `http://localhost:5173`
- Authorization callback URL: `http://localhost:8000/auth/github/callback`

Set:

```env
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
```

## Environment Variables

Backend variables are documented in `backend/.env.example`.

Important values:

- `DATABASE_URL`: async SQLAlchemy PostgreSQL URL.
- `SESSION_SECRET`: long random signing secret.
- `CORS_ALLOWED_ORIGINS`: comma-separated frontend origins, for example `http://localhost:5173,http://127.0.0.1:5173`.
- `WS_NOTIFICATION_INTERVAL_SECONDS`: default notification poll interval.
- `TEST_AUTH_ENABLED`: enables local/test auth endpoint when true.

Frontend variables are documented in `frontend/.env.example`.

## API Summary

Auth:

- `GET /auth/google/login`
- `GET /auth/google/callback`
- `GET /auth/github/login`
- `GET /auth/github/callback`
- `POST /auth/logout`
- `GET /auth/me`
- `POST /auth/test-login` only when `TEST_AUTH_ENABLED=true`

Lists:

- `GET /api/lists`
- `POST /api/lists`
- `PATCH /api/lists/{list_id}`
- `DELETE /api/lists/{list_id}`

Tasks:

- `GET /api/tasks?list_id=...&search=...&status=...&priority=...&due=...`
- `POST /api/tasks`
- `PATCH /api/tasks/{task_id}`
- `PATCH /api/tasks/{task_id}/status`
- `DELETE /api/tasks/{task_id}`

Due filters:

- `overdue`
- `today`
- `next_7_days`
- `all`

Authorization is enforced on every list/task operation. Cross-account resource access returns `404`.

## Deletion Rule

Deleting a list/project cascades deletion of all tasks in that list. The frontend shows a confirmation dialog before the request is sent.

## WebSocket

Endpoint:

```text
WS /ws/notifications
```

The WebSocket handshake uses the same HTTP-only session cookie as the REST API.

Server sends an initial notification batch on connect and repeats checks every `WS_NOTIFICATION_INTERVAL_SECONDS` seconds by default. The client may change interval within 30-300 seconds using `subscribe`.

Client to server:

```json
{
  "type": "subscribe",
  "payload": {
    "enabled_types": ["overdue", "due_soon"],
    "interval_seconds": 60,
    "include_acknowledged": false
  }
}
```

```json
{
  "type": "ack",
  "payload": {
    "notification_id": "overdue:task-uuid"
  }
}
```

Server to client:

```json
{
  "type": "notification_batch",
  "payload": {
    "generated_at": "2026-04-29T10:00:00Z",
    "notifications": [
      {
        "id": "overdue:task-uuid",
        "type": "overdue",
        "task_id": "task-uuid",
        "list_id": "list-uuid",
        "title": "Submit report",
        "due_date": "2026-04-28",
        "priority": "high",
        "message": "Task is overdue"
      }
    ]
  }
}
```

Notification rules:

- `overdue`: task status is not `done` and due date is before today.
- `due_soon`: task status is not `done` and due date is today through the next 3 days, inclusive.

## Tests

Backend:

```bash
cd backend
pytest
```

Frontend:

```bash
cd frontend
npm test
```

## Docker

Run the full stack:

```bash
docker compose up --build
```

For the first backend container run, apply migrations:

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python scripts/seed.py
```

The compose file includes PostgreSQL, backend, and frontend services. Local host development can also run only PostgreSQL in Docker and run backend/frontend directly on the host.
