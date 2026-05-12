# Quickstart: Task Change History

## Local setup

```bash
# 1. Start the database
docker compose up -d postgres

# 2. Apply all migrations (including 0004_add_task_history)
cd backend && alembic upgrade head

# 3. Start the backend
uvicorn app.main:app --reload

# 4. Start the frontend (separate terminal)
cd frontend && npm run dev
```

Enable the demo login button by adding `TEST_AUTH_ENABLED=true` to `backend/.env`.

## Running the tests

Backend history tests:
```bash
cd backend && source .venv/bin/activate
pytest tests/test_task_history.py -v
```

Frontend history component tests:
```bash
cd frontend
npm test -- TaskHistory
npm test -- TaskHistoryModal
```

Full suite:
```bash
cd backend && pytest
cd frontend && npm test && npm run build
```

## Exercising the feature end-to-end

1. Open `http://localhost:5173` and click **Use local demo login**.
2. Create a list, then create a task inside it.
3. Edit the task (change title, status, priority, or due date) and save. Repeat a few times.
4. Click the **History** (clock icon) button on the task row — it sits between the Edit (pencil) and Delete (trash) buttons.
5. A history panel appears below the task list. It shows a table with columns **When**, **Changed By**, and **Fields Changed**.
6. Click any row in the table to open the detail modal.
7. The modal displays a **Field / Was / Became** table for every field changed in that event.
8. Close the modal via the × button, pressing **Escape**, or clicking the darkened backdrop. The history panel should remain visible after the modal closes.
9. Click the × button in the history panel header to close the panel.

## Key file locations

| File | Purpose |
|------|---------|
| `backend/app/models/task_history.py` | ORM models: `TaskChangeRecord`, `FieldChange` |
| `backend/app/schemas/history.py` | Pydantic response schemas |
| `backend/app/services/tasks.py` | `_capture_history()` — called on every task save |
| `backend/app/services/history.py` | `get_task_history()` — read path |
| `backend/app/api/tasks.py` | `GET /api/tasks/{task_id}/history` route |
| `backend/tests/test_task_history.py` | Backend acceptance tests |
| `alembic/versions/0004_add_task_history.py` | Schema migration |
| `frontend/src/features/tasks/TaskHistory.tsx` | History list panel (table) |
| `frontend/src/features/tasks/TaskHistoryModal.tsx` | Detail modal (Field/Was/Became) |
| `frontend/src/features/tasks/TaskBoard.tsx` | History button + panel toggle |
| `frontend/src/types/domain.ts` | `TaskHistoryEntry`, `FieldChange` types |
| `frontend/src/api/client.ts` | `api.taskHistory()` |
