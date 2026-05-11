# Implementation Plan: Task Change History

**Branch**: `001-task-history` | **Date**: 2026-05-11 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `specs/001-task-history/spec.md`

## Summary

Add per-task change history to the Personal To-Do Manager. Every time a task is updated, a history record is written atomically (same transaction). Users access history via a new button (between Edit and Delete) that reveals an inline list of change events; clicking any entry opens a modal showing WAS → BECAME diffs for each changed field, along with who made the change.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript + React 18+ (frontend)  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 async, Alembic, Pydantic v2 (backend); Vite, Vitest + Testing Library, lucide-react (frontend)  
**Storage**: PostgreSQL (production), in-memory SQLite (tests)  
**Testing**: pytest with in-memory SQLite via `conftest.py` (backend); Vitest + Testing Library (frontend)  
**Target Platform**: Linux server (backend), modern web browser (frontend)  
**Project Type**: web-service (backend) + web-app (frontend)  
**Performance Goals**: History list renders within 2 seconds; new history entry visible within 1 second of task save  
**Constraints**: All history records loaded at once (no pagination); cascade delete with task; no new external dependencies  
**Scale/Scope**: Single personal user; tasks expected to have tens to low hundreds of history entries at most

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Layered Architecture | PASS | History endpoint: thin router → `services/history.py`. History capture: called from `services/tasks.py`. No DB calls in routers. |
| II. Security by Design | PASS | `GET /api/tasks/{task_id}/history` enforces `user_id` ownership. Unauthorized access returns 404, not 403. |
| III. Test-First | PASS | pytest tests written before backend implementation; Vitest tests before frontend implementation. Red-green-refactor mandatory. |
| IV. Schema Discipline | PASS | Two new ORM models (`TaskChangeRecord`, `FieldChange`) with `TimestampMixin`. New Pydantic schemas (`TaskHistoryRead`, `FieldChangeRead`) separate from ORM. `check-migration` agent run after model changes. |
| V. Simplicity (YAGNI) | PASS | No new dependencies. History capture inline in `update_task()` / `update_task_status()`. Two new tables, one new endpoint, two new frontend components. |

**No violations. Gate passed.**

## Project Structure

### Documentation (this feature)

```text
specs/001-task-history/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── contracts/
│   └── api.md           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks - NOT created here)
```

### Source Code Changes

```text
backend/
├── app/
│   ├── models/
│   │   └── task_history.py        # NEW: TaskChangeRecord + FieldChange ORM models
│   ├── db/
│   │   └── base.py                # MODIFIED: import TaskChangeRecord for Alembic detection
│   ├── schemas/
│   │   └── history.py             # NEW: TaskHistoryRead + FieldChangeRead Pydantic schemas
│   ├── services/
│   │   ├── history.py             # NEW: get_task_history() service function
│   │   └── tasks.py               # MODIFIED: capture history in update_task() + update_task_status()
│   └── api/
│       └── tasks.py               # MODIFIED: add GET /{task_id}/history route
└── alembic/versions/
    └── 0004_add_task_history.py   # NEW: migration for task_history + task_history_fields tables

backend/tests/
└── test_task_history.py           # NEW: pytest tests (written first)

frontend/src/
├── types/
│   └── domain.ts                  # MODIFIED: add TaskHistoryEntry + FieldChange types
├── api/
│   └── client.ts                  # MODIFIED: add taskHistory() method
└── features/tasks/
    ├── TaskBoard.tsx               # MODIFIED: history button + panel state
    ├── TaskHistory.tsx             # NEW: inline history list panel
    ├── TaskHistory.test.tsx        # NEW: Vitest tests (written first)
    ├── TaskHistoryModal.tsx        # NEW: field-diff detail modal
    └── TaskHistoryModal.test.tsx   # NEW: Vitest tests (written first)
```

**Structure Decision**: Web application (Option 2) — existing `backend/` + `frontend/` layout; this feature adds files to existing directories without creating new top-level directories.

## Complexity Tracking

No constitution violations — table is empty.
