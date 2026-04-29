# Personal To-Do Manager - technical specification

## 1. Purpose and scope

Personal To-Do Manager is a full-stack MVP for managing personal work across multiple projects. The product must let an authenticated user create private lists/projects, manage tasks with priorities and deadlines, search and filter tasks, and receive real-time WebSocket notifications about overdue and soon-due work.

The implementation target is:

- Backend: Python, FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL.
- Frontend: React, TypeScript, Vite.
- Real-time transport: FastAPI WebSocket endpoint.
- Authentication: SSO only through Google OpenID Connect and GitHub OAuth.
- Local delivery: runnable backend, frontend, database, migrations, seed data, and automated tests.

The MVP explicitly does not include sharing, invitations, public links, teams, organizations, recurring tasks, file attachments, comments, or collaboration.

## 2. Product rules

### 2.1 Core rules

- The system supports multiple users.
- Every list/project and task belongs to exactly one user.
- Users can only read, create, update, delete, search, filter, and receive notifications for their own data.
- No data sharing is allowed.
- Backend authorization is mandatory on every HTTP and WebSocket operation. Frontend-only filtering is not sufficient.

### 2.2 Main user flows

1. A visitor opens the app and sees an authentication screen.
2. The visitor signs in with Google or GitHub.
3. The backend creates or updates the local user profile and establishes an authenticated session.
4. The frontend loads the authenticated user, lists/projects, and selected list tasks.
5. The user creates, renames, and deletes lists/projects.
6. The user creates, edits, deletes, searches, filters, and quickly changes status for tasks.
7. The frontend opens a WebSocket connection after login.
8. The backend sends an initial notification batch and then periodic notification updates.
9. The client sends a meaningful message back, such as notification preferences or acknowledgement.
10. The user logs out and the session is invalidated.

## 3. Architecture

### 3.1 High-level layout

```text
personal-todo-manager/
  backend/
    app/
      api/
      auth/
      core/
      db/
      models/
      repositories/
      schemas/
      services/
      websocket/
      main.py
    alembic/
    tests/
    pyproject.toml
  frontend/
    src/
      api/
      auth/
      components/
      features/
      hooks/
      layouts/
      routes/
      styles/
      types/
      main.tsx
    package.json
  docker-compose.yml
  README.md
```

### 3.2 Runtime components

- React SPA: serves the user interface, stores no authoritative permissions, and calls backend APIs with credentials.
- FastAPI app: owns authentication, authorization, validation, business rules, REST endpoints, WebSocket endpoint, and OpenAPI schema.
- PostgreSQL: durable storage for users, OAuth identities, lists, tasks, notification acknowledgements, and optional session rows.
- Alembic: database schema migrations.
- Test suite: backend unit/integration tests and frontend component/API-client tests.

### 3.3 Local development ports

- Frontend: `http://localhost:5173`.
- Backend API: `http://localhost:8000`.
- OpenAPI UI: `http://localhost:8000/docs`.
- PostgreSQL: `localhost:5432`.

## 4. Backend specification

### 4.1 Backend dependencies

Recommended backend packages:

- `fastapi` for HTTP and WebSocket endpoints.
- `uvicorn[standard]` for local ASGI serving.
- `sqlalchemy[asyncio]` for ORM and database access.
- `asyncpg` for PostgreSQL async driver.
- `alembic` for migrations.
- `pydantic-settings` for environment-based settings.
- `authlib` for OAuth/OIDC flows.
- `itsdangerous` or signed JWT/session helper for secure session tokens.
- `python-multipart` only if form parsing is needed.
- `pytest`, `pytest-asyncio`, `httpx`, `freezegun` or an injectable clock for tests.

### 4.2 Backend module responsibilities

- `app/main.py`: FastAPI app creation, middleware registration, router mounting, startup checks.
- `app/core/config.py`: typed settings loaded from environment variables.
- `app/core/security.py`: session signing, token parsing, CSRF/state helpers, security utilities.
- `app/db/session.py`: async SQLAlchemy engine and session factory.
- `app/models/`: SQLAlchemy database models.
- `app/schemas/`: Pydantic request and response DTOs.
- `app/repositories/`: database queries with user scoping.
- `app/services/`: business operations and notification detection.
- `app/auth/`: provider-specific OAuth configuration and callback handling.
- `app/api/`: HTTP route modules.
- `app/websocket/`: connection manager, message schemas, notification loop.

### 4.3 Configuration

Backend settings should be loaded from environment variables and documented in `README.md`.

Required:

```env
DATABASE_URL=postgresql+asyncpg://todo:todo@localhost:5432/todo
BACKEND_BASE_URL=http://localhost:8000
FRONTEND_BASE_URL=http://localhost:5173
SESSION_SECRET=replace-with-long-random-secret
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
```

Optional:

```env
ENVIRONMENT=local
COOKIE_SECURE=false
COOKIE_DOMAIN=
ACCESS_TOKEN_TTL_MINUTES=10080
WS_NOTIFICATION_INTERVAL_SECONDS=60
CORS_ALLOWED_ORIGINS=http://localhost:5173
TEST_AUTH_ENABLED=false
```

Production-like deployments must use HTTPS, `COOKIE_SECURE=true`, strict CORS origins, and a strong unique `SESSION_SECRET`.

## 5. Data model

### 5.1 Entity overview

```text
User 1..n OAuthIdentity
User 1..n ProjectList
ProjectList 1..n Task
User 1..n NotificationAck
```

### 5.2 Tables

#### users

Stores the local user profile.

| Column | Type | Constraints | Notes |
| --- | --- | --- | --- |
| id | uuid | primary key | Generated by backend/database |
| email | text | nullable, indexed | Email may be unavailable from provider |
| display_name | text | not null | Provider display name or fallback |
| avatar_url | text | nullable | Provider avatar |
| created_at | timestamptz | not null | Server timestamp |
| updated_at | timestamptz | not null | Server timestamp |
| last_login_at | timestamptz | nullable | Updated after successful OAuth callback |

#### oauth_identities

Maps provider accounts to local users.

| Column | Type | Constraints | Notes |
| --- | --- | --- | --- |
| id | uuid | primary key | Generated |
| user_id | uuid | fk users.id, cascade delete | Owner |
| provider | text | not null | `google` or `github` |
| provider_user_id | text | not null | Stable provider subject/id |
| email | text | nullable | Provider email at login time |
| display_name | text | not null | Provider profile name |
| avatar_url | text | nullable | Provider profile image |
| created_at | timestamptz | not null | Timestamp |
| updated_at | timestamptz | not null | Timestamp |

Unique constraint:

```sql
unique(provider, provider_user_id)
```

#### project_lists

Stores user-owned lists/projects.

| Column | Type | Constraints | Notes |
| --- | --- | --- | --- |
| id | uuid | primary key | Generated |
| user_id | uuid | fk users.id, indexed, not null | Owner |
| name | text | not null | 1-100 chars |
| sort_order | integer | not null, default 0 | Future-friendly ordering |
| created_at | timestamptz | not null | Timestamp |
| updated_at | timestamptz | not null | Timestamp |

Recommended constraints:

```sql
unique(user_id, lower(name))
```

If case-insensitive unique indexes are implemented through PostgreSQL expression indexes, document the exact Alembic migration.

#### tasks

Stores user-owned tasks scoped through a list/project.

| Column | Type | Constraints | Notes |
| --- | --- | --- | --- |
| id | uuid | primary key | Generated |
| user_id | uuid | fk users.id, indexed, not null | Denormalized owner for efficient authorization |
| list_id | uuid | fk project_lists.id, indexed, not null | Parent list |
| title | text | not null | 1-200 chars |
| description | text | not null, default empty string | Notes |
| status | text | not null | `todo`, `in_progress`, `done` |
| priority | text | not null | `low`, `medium`, `high` |
| due_date | date | nullable | Date without time zone |
| created_at | timestamptz | not null | Timestamp |
| updated_at | timestamptz | not null | Timestamp |
| completed_at | timestamptz | nullable | Set when status becomes `done` |

Deletion decision:

- Deleting a list cascades deletion of all tasks in that list.
- This must be stated in `README.md` because the source requirements allow either cascade deletion or blocked deletion.
- The UI must show a confirmation dialog that clearly says all tasks in the list will be deleted.

Recommended constraints:

```sql
check (status in ('todo', 'in_progress', 'done'))
check (priority in ('low', 'medium', 'high'))
check (length(trim(title)) between 1 and 200)
```

#### notification_acks

Tracks notifications acknowledged by a user.

| Column | Type | Constraints | Notes |
| --- | --- | --- | --- |
| id | uuid | primary key | Generated |
| user_id | uuid | fk users.id, indexed, not null | Owner |
| task_id | uuid | fk tasks.id, cascade delete, not null | Related task |
| notification_type | text | not null | `overdue` or `due_soon` |
| acknowledged_at | timestamptz | not null | Timestamp |

Unique constraint:

```sql
unique(user_id, task_id, notification_type)
```

### 5.3 Authorization invariant

For every task query, enforce both:

- `tasks.user_id == current_user.id`
- task parent list belongs to the same user when creating or moving tasks.

Do not trust client-provided `user_id`. It must never be accepted in create/update payloads.

## 6. Authentication and session design

### 6.1 OAuth providers

The app must support:

- Google OAuth with OpenID Connect.
- GitHub OAuth.

Authentication screen must show:

- Continue with Google.
- Continue with GitHub.

### 6.2 OAuth endpoints

```http
GET /auth/google/login
GET /auth/google/callback
GET /auth/github/login
GET /auth/github/callback
POST /auth/logout
GET /auth/me
```

### 6.3 OAuth flow

1. Frontend sends the browser to `/auth/{provider}/login`.
2. Backend creates a signed `state` value containing provider, nonce, and redirect target.
3. Backend redirects to provider authorization URL.
4. Provider redirects to `/auth/{provider}/callback`.
5. Backend validates `state`.
6. Backend exchanges code for provider tokens.
7. Backend fetches provider profile.
8. Backend upserts `oauth_identities`.
9. Backend creates or updates the local `users` row.
10. Backend sets an HTTP-only session cookie.
11. Backend redirects to frontend application route.
12. Frontend calls `/auth/me` to hydrate the current user.

### 6.4 Session strategy

Use a secure HTTP-only cookie by default.

Cookie settings:

- `HttpOnly=true`
- `SameSite=Lax` for local OAuth redirects
- `Secure=false` only in local development
- `Secure=true` outside local development
- Path `/`
- Expiration aligned with configured session TTL

The cookie may contain a signed opaque session token or a signed JWT. For this MVP, a signed JWT is acceptable if it contains only:

- `sub`: local user id.
- `iat`: issued timestamp.
- `exp`: expiry timestamp.
- `session_version` if future invalidation is needed.

Do not store provider access tokens in browser-accessible storage.

### 6.5 Test-mode SSO

Automated tests must cover SSO success without calling real Google or GitHub. Implement one of these:

- Mock Authlib provider responses in backend tests.
- Add a test-only provider service selected by dependency injection.
- Add a test-only endpoint enabled only when `TEST_AUTH_ENABLED=true`.

The test-mode path must never be enabled by default.

## 7. REST API specification

All non-auth endpoints require an authenticated user. Unauthorized requests return `401`. Attempts to access another user's resources return `404` to avoid leaking resource existence.

### 7.1 Common response formats

Error response:

```json
{
  "detail": {
    "code": "validation_error",
    "message": "Title is required",
    "fields": {
      "title": "Must not be empty"
    }
  }
}
```

Pagination is not required for MVP, but list endpoints should accept optional `limit` and `offset` if implementation time allows.

### 7.2 Auth API

#### GET /auth/me

Returns current user.

```json
{
  "id": "7d8a2f9b-1b6a-45a0-9e6d-0c195d8da1b7",
  "email": "user@example.com",
  "display_name": "User Name",
  "avatar_url": "https://example.com/avatar.png"
}
```

#### POST /auth/logout

Clears session cookie and returns:

```json
{
  "ok": true
}
```

### 7.3 Lists/projects API

#### GET /api/lists

Returns all lists for current user.

```json
[
  {
    "id": "uuid",
    "name": "Work",
    "task_count": 8,
    "open_task_count": 5,
    "created_at": "2026-04-29T10:00:00Z",
    "updated_at": "2026-04-29T10:00:00Z"
  }
]
```

#### POST /api/lists

Request:

```json
{
  "name": "Work"
}
```

Validation:

- `name` is required.
- Trimmed length must be 1-100 characters.
- Duplicate list names for the same user should return `409`.

#### PATCH /api/lists/{list_id}

Request:

```json
{
  "name": "Personal Work"
}
```

#### DELETE /api/lists/{list_id}

Deletes the list and cascades all tasks in it.

Response:

```json
{
  "ok": true,
  "deleted_tasks": 4
}
```

### 7.4 Tasks API

#### GET /api/tasks

Query parameters:

| Name | Type | Required | Values |
| --- | --- | --- | --- |
| list_id | uuid | yes | Existing list owned by current user |
| search | string | no | Search in title and description |
| status | string | no | `todo`, `in_progress`, `done` |
| priority | string | no | `low`, `medium`, `high` |
| due | string | no | `overdue`, `today`, `next_7_days`, `all` |

Response:

```json
[
  {
    "id": "uuid",
    "list_id": "uuid",
    "title": "Prepare sprint plan",
    "description": "Draft priorities and milestones",
    "status": "in_progress",
    "priority": "high",
    "due_date": "2026-05-01",
    "created_at": "2026-04-29T10:00:00Z",
    "updated_at": "2026-04-29T10:00:00Z",
    "completed_at": null
  }
]
```

Search implementation:

- MVP option: use `ILIKE` on `title` and `description`.
- Better PostgreSQL option: add a generated `tsvector` column or GIN index in a later iteration.

Due filters:

- `overdue`: `due_date < current_date` and `status != done`.
- `today`: `due_date = current_date`.
- `next_7_days`: `current_date <= due_date <= current_date + 7 days`.
- `all`: no due-date restriction.

#### POST /api/tasks

Request:

```json
{
  "list_id": "uuid",
  "title": "Prepare sprint plan",
  "description": "Draft priorities and milestones",
  "status": "todo",
  "priority": "high",
  "due_date": "2026-05-01"
}
```

Validation:

- `list_id` must belong to current user.
- `title` is required, trimmed length 1-200.
- `description` defaults to empty string.
- `status` defaults to `todo`.
- `priority` defaults to `medium`.
- `due_date` may be null.

#### PATCH /api/tasks/{task_id}

Allows editing any task field.

Request example:

```json
{
  "title": "Prepare final sprint plan",
  "status": "in_progress",
  "priority": "high",
  "due_date": "2026-05-02"
}
```

When status changes to `done`, set `completed_at` if it is not already set. When status changes from `done` back to another status, clear `completed_at`.

#### PATCH /api/tasks/{task_id}/status

Fast status change endpoint for task list UI.

Request:

```json
{
  "status": "done"
}
```

#### DELETE /api/tasks/{task_id}

Deletes the task.

Response:

```json
{
  "ok": true
}
```

## 8. WebSocket specification

### 8.1 Endpoint

```text
WS /ws/notifications
```

The WebSocket connection must be authenticated. Recommended approach:

- Browser sends the same HTTP-only session cookie during WebSocket handshake.
- Backend resolves current user from the cookie before accepting the socket.
- If authentication fails, close with code `1008` policy violation.

### 8.2 Server behavior

On connect:

1. Authenticate user.
2. Accept WebSocket connection.
3. Register connection in connection manager.
4. Use default preferences until client sends `subscribe`.
5. Send initial notification batch.
6. Start periodic checks while connected.

Periodic rule:

- Default interval: 60 seconds.
- Client may request a supported interval through `subscribe`.
- Minimum accepted interval: 30 seconds.
- Maximum accepted interval: 300 seconds.
- The chosen interval must be documented in `README.md`.

### 8.3 Notification rules

Notification types:

- `overdue`: task status is not `done` and `due_date` is before today.
- `due_soon`: task status is not `done` and `due_date` is from today through the next 3 days, inclusive.

Dates must be evaluated in the backend. For MVP, use the server's configured date/time zone consistently and document it. A later iteration can add user time zones.

### 8.4 Client-to-server messages

The client must send at least one meaningful message. This implementation should support both `subscribe` and `ack`.

#### subscribe

Sent after connection or when preferences change.

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

Effect:

- Updates in-memory connection preferences.
- Changes future server notification batches for that connection.
- If invalid, server responds with an error message and keeps previous preferences.

#### ack

Marks a notification as read.

```json
{
  "type": "ack",
  "payload": {
    "notification_id": "overdue:task-uuid"
  }
}
```

Effect:

- Parses notification id into type and task id.
- Confirms task belongs to current user.
- Creates or updates `notification_acks`.
- Sends an acknowledgement response.

### 8.5 Server-to-client messages

#### notification_batch

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

#### ack_ok

```json
{
  "type": "ack_ok",
  "payload": {
    "notification_id": "overdue:task-uuid"
  }
}
```

#### error

```json
{
  "type": "error",
  "payload": {
    "code": "invalid_message",
    "message": "Unsupported WebSocket message type"
  }
}
```

### 8.6 WebSocket implementation notes

- Use Pydantic schemas for incoming message validation.
- Keep each connected socket isolated by user id.
- Cancel periodic tasks on disconnect.
- Catch `WebSocketDisconnect` and remove the connection.
- Do not broadcast notifications across users.
- Keep notification query logic in a service so it can be tested without WebSocket plumbing.

## 9. Frontend specification

### 9.1 Frontend dependencies

Recommended frontend packages:

- `react`, `react-dom`, `typescript`, `vite`.
- `react-router-dom` for routing.
- `@tanstack/react-query` for server state and cache invalidation.
- `react-hook-form` and `zod` for form state and validation.
- `tailwindcss` for styling.
- `lucide-react` for icons.
- Optional: `sonner` or equivalent toast library for notifications.
- `vitest`, `@testing-library/react`, `@testing-library/user-event`, `msw` for tests.

### 9.2 Routes

```text
/login
/app
/app/lists/:listId
```

Routing behavior:

- Unauthenticated users are redirected to `/login`.
- Authenticated users visiting `/login` are redirected to `/app`.
- If no list exists, `/app` shows a list empty state and create-list action.
- If lists exist and no list is selected, route to the first list or remember last selected list in local storage.

### 9.3 UI layout

Main authenticated screen:

- Left sidebar: user summary, project/list navigation, create list button, logout action.
- Main area: selected list header, search input, filters, task list, create task action.
- Notification area: toast stack, banner, or notification panel visible while WebSocket is connected.

Responsive behavior:

- Desktop: persistent sidebar.
- Narrow screens: sidebar collapses into a menu/drawer.
- Task list remains usable on mobile; dense table-only layout should be avoided for narrow screens.

### 9.4 Required UI states

Authentication:

- Login page with "Continue with Google" and "Continue with GitHub".
- Loading state while checking `/auth/me`.
- Error state if session check fails unexpectedly.

Lists:

- Empty state when user has no lists.
- Create list form.
- Rename list action.
- Delete list confirmation that mentions cascade task deletion.

Tasks:

- Empty state for selected list with no tasks.
- Empty search/filter result state.
- Loading state for task list fetch.
- Create task UI.
- Edit task UI.
- Delete task confirmation.
- Quick status control from list view.
- Client-side validation messages for title, due date, status, and priority.

Interactive styling:

- Visible hover states on buttons, links, task rows, and list items.
- Visible keyboard focus states.
- Consistent spacing and typography.
- Disabled states during mutations.

### 9.5 Frontend data model

Recommended TypeScript types:

```ts
export type TaskStatus = 'todo' | 'in_progress' | 'done';
export type TaskPriority = 'low' | 'medium' | 'high';

export interface User {
  id: string;
  email: string | null;
  display_name: string;
  avatar_url: string | null;
}

export interface ProjectList {
  id: string;
  name: string;
  task_count: number;
  open_task_count: number;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: string;
  list_id: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  due_date: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}
```

### 9.6 API client behavior

- Use `fetch` or a small wrapper around `fetch`.
- Always call API with `credentials: 'include'` so cookies are sent.
- On `401`, clear local user state and redirect to `/login`.
- Use React Query keys such as:
  - `['me']`
  - `['lists']`
  - `['tasks', listId, filters]`
- Invalidate `['lists']` after task mutations because task counts can change.
- Invalidate selected task query after create/update/delete/status changes.

### 9.7 WebSocket client behavior

Connection lifecycle:

1. Open `ws://localhost:8000/ws/notifications` after user is authenticated.
2. Send `subscribe` after `onopen`.
3. Render received notifications.
4. Send `ack` when user dismisses or marks notification as read.
5. Reconnect with backoff after unexpected disconnect.
6. Close socket on logout.

Backoff:

- Initial delay: 1 second.
- Max delay: 30 seconds.
- Reset delay after successful connection.

Notification UI:

- Show overdue notifications with stronger visual emphasis than due-soon notifications.
- Include task title, due date, and priority.
- Provide a control to dismiss/acknowledge.
- Clicking a notification should navigate to the relevant list and make the task visible.

## 10. Backend implementation details

### 10.1 SQLAlchemy model conventions

- Use UUID primary keys.
- Use timezone-aware timestamps.
- Use Python enums for status and priority, mapped to string values.
- Add indexes for common filters:
  - `tasks(user_id, list_id)`
  - `tasks(user_id, status)`
  - `tasks(user_id, priority)`
  - `tasks(user_id, due_date)`
  - `project_lists(user_id)`

### 10.2 Repository pattern

Repositories should always accept `user_id` for user-owned resources.

Example methods:

```python
async def get_list_for_user(session: AsyncSession, user_id: UUID, list_id: UUID) -> ProjectList | None:
    ...

async def get_task_for_user(session: AsyncSession, user_id: UUID, task_id: UUID) -> Task | None:
    ...
```

Route handlers should not write unscoped queries like "get task by id" for user-owned resources.

### 10.3 Service layer

Recommended services:

- `AuthService`: provider profile normalization and user upsert.
- `ListService`: create, rename, delete with cascade count.
- `TaskService`: create, update, delete, status changes, search/filter.
- `NotificationService`: overdue/due-soon detection, notification DTO creation, acknowledgement.

### 10.4 Validation rules

List:

- Trim name before saving.
- Reject empty name.
- Reject names over 100 characters.

Task:

- Trim title before saving.
- Reject empty title.
- Reject titles over 200 characters.
- Normalize description to empty string when omitted.
- Validate status and priority enum values.
- Allow null due date.

WebSocket:

- Reject unsupported message types.
- Reject invalid intervals outside allowed range.
- Ignore or reject notification acknowledgement for resources not owned by current user.

### 10.5 Time and date handling

- Store task due date as `date`, not timestamp.
- Store audit fields as timezone-aware UTC timestamps.
- Evaluate "today", "overdue", and "next 7 days" with one backend date provider.
- In tests, inject or freeze the date provider.

## 11. Security requirements

- Never expose provider client secrets to the frontend.
- Never store OAuth access tokens in local storage or session storage.
- Use HTTP-only cookies for app session.
- Validate OAuth `state`.
- Use strict CORS origins.
- Use SameSite cookie protection.
- Authorize every user-owned resource on the backend.
- Return `404` for another user's list/task ids.
- Validate all request bodies with Pydantic.
- Keep error messages clear but avoid leaking cross-user resource existence.
- Do not log OAuth tokens, session tokens, or full cookie headers.

## 12. Testing strategy

### 12.1 Backend tests

Required test cases from the source requirements:

1. SSO login success path in test mode using a mock/stub provider response.
2. A user can create a list and a task.
3. A user cannot access another user's lists or tasks.
4. WebSocket notifications are sent for overdue or due-soon tasks.

Additional recommended backend tests:

- Logout clears the session.
- `/auth/me` returns current user when authenticated.
- List delete cascades tasks and returns deleted count.
- Task search matches title and description.
- Status, priority, and due-date filters work independently and together.
- `completed_at` is set and cleared correctly when status changes.
- WebSocket `subscribe` changes interval/preferences.
- WebSocket `ack` creates `notification_acks`.
- Invalid WebSocket messages return an error message.

Test database:

- Use isolated PostgreSQL test database when possible.
- Alternative for fast unit tests: SQLite is acceptable only for non-SQL-specific service tests, but authorization and migration behavior should be tested against PostgreSQL.

### 12.2 Frontend tests

Recommended frontend tests:

- Login page renders both SSO buttons.
- Authenticated app renders lists and selected list tasks.
- Empty list state appears when there are no tasks.
- Task form validates required title.
- Status quick-change calls API and updates UI.
- Search/filter controls update task query.
- Notification batch renders in notification UI.
- Dismiss action sends WebSocket `ack`.

Use MSW to mock HTTP APIs and a lightweight mock WebSocket for notification behavior.

### 12.3 End-to-end smoke test

Optional but useful:

- Start backend, frontend, and database.
- Use test auth mode.
- Create list.
- Create task due today.
- Verify task appears.
- Verify WebSocket notification appears.
- Logout.

## 13. Seed data

Provide one of:

- `backend/scripts/seed.py`
- `POST /api/dev/seed` enabled only in local/test mode
- README manual steps

Recommended seed script:

- Creates one demo user only in local/test mode.
- Creates lists:
  - Work
  - Personal
  - Learning
- Creates tasks:
  - One overdue high-priority task.
  - One due-soon medium-priority task.
  - One completed task.
  - One task without due date.

Seed data must not bypass production authentication unless test/local mode is explicitly enabled.

## 14. Containerization

Containerization is optional in the source requirements, but recommended.

Recommended `docker-compose.yml` services:

- `postgres`
- `backend`
- `frontend`

For local developer speed, it is acceptable to run only PostgreSQL in Docker and run backend/frontend directly on the host.

Minimum database service:

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: todo
      POSTGRES_PASSWORD: todo
      POSTGRES_DB: todo
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## 15. README requirements

The final `README.md` must include:

- Project overview.
- Stack summary.
- Prerequisites.
- Environment variable setup.
- PostgreSQL startup instructions.
- Backend install, migration, seed, and run commands.
- Frontend install and run commands.
- Google OAuth setup:
  - OAuth consent screen basics.
  - Client id/secret.
  - Redirect URI: `http://localhost:8000/auth/google/callback`.
- GitHub OAuth setup:
  - OAuth App creation.
  - Client id/secret.
  - Callback URL: `http://localhost:8000/auth/github/callback`.
- WebSocket endpoint.
- Client-to-server WebSocket message formats.
- Server-to-client WebSocket message formats.
- Notification rules and interval.
- API summary or OpenAPI link.
- Test commands.
- Deletion decision: deleting a list cascades tasks.
- Containerization notes, including whether full Docker setup is provided.

## 16. Acceptance criteria

The implementation is accepted when:

- A new user can log in with Google.
- A new user can log in with GitHub.
- Authenticated session survives page refresh.
- User can log out.
- User can create, rename, and delete lists/projects.
- Deleting a list cascades its tasks after explicit confirmation.
- User can create, edit, delete, and quickly change status for tasks.
- Task fields include title, description, status, due date, and priority.
- User can search by title and description.
- User can filter by status.
- User can filter by priority.
- User can filter by due category: overdue, today, next 7 days, all.
- User cannot access another user's lists/tasks through direct API calls.
- WebSocket connects only for authenticated users.
- Server sends an initial notification batch after WebSocket connection.
- Server periodically sends overdue and due-soon notifications.
- Client sends at least one meaningful WebSocket message that changes server behavior or persisted notification state.
- Notification UI is visible and usable.
- UI is responsive on narrow screens.
- Empty, loading, hover, focus, and validation states are implemented.
- Required automated tests pass locally.
- README lets another developer run the app without guessing.

## 17. Suggested implementation order

1. Create backend project skeleton and settings.
2. Add Docker Compose PostgreSQL service.
3. Add SQLAlchemy models and Alembic migrations.
4. Implement auth session primitives.
5. Implement test-mode auth support.
6. Implement Google and GitHub OAuth flows.
7. Implement `/auth/me` and logout.
8. Implement list/project REST endpoints.
9. Implement task REST endpoints with search and filters.
10. Implement notification service.
11. Implement WebSocket endpoint with `subscribe` and `ack`.
12. Add backend tests for auth, CRUD, authorization, and notifications.
13. Create React app shell, routing, and API client.
14. Build login screen and authenticated layout.
15. Build list sidebar and list CRUD UI.
16. Build task list, filters, create/edit forms, and quick status change.
17. Add WebSocket notification client and notification UI.
18. Add frontend tests.
19. Add seed script and README.
20. Run full local verification from a clean checkout.

## 18. Non-goals for MVP

- Shared lists or tasks.
- Team accounts or organizations.
- Public links.
- Password login.
- Email verification.
- Recurring tasks.
- Calendar integrations.
- Push notifications outside the connected WebSocket session.
- Offline-first support.
- Full-text search ranking.
- File attachments.
- Comments or activity feeds.

## 19. Future enhancements

- User-configurable time zone.
- Drag-and-drop task ordering.
- Saved filter views.
- Full-text search with PostgreSQL GIN indexes.
- Notification preferences persisted per user.
- Browser notifications using the Notifications API.
- Deployment profile for production hosting.
- End-to-end tests with Playwright.
- Rate limiting on auth and mutation endpoints.
- Audit log for sensitive operations.
