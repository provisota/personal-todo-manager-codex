# Tasks: Task Change History

**Input**: Design documents from `specs/001-task-history/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/api.md ✅

**Tests**: Included — required by project constitution (Principle III: Test-First is NON-NEGOTIABLE). Backend pytest tests and frontend Vitest tests must be written before implementation and must fail (red) before implementation begins.

**Organization**: Tasks grouped by user story. Phase 2 (US3 — history capture) is listed before US1/US2 because US1 and US2 require captured data to be meaningful.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no incomplete dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths included in every task description

---

## Phase 1: Foundational — Data Layer & Shared Infrastructure

**Purpose**: ORM models, migration, Pydantic schemas, TypeScript types, and API client method. All user stories depend on this phase.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T001 Create `TaskChangeRecord` and `FieldChange` ORM models in `backend/app/models/task_history.py` (fields, FK constraints, indexes — see data-model.md)
- [X] T002 Import `TaskChangeRecord` in `backend/app/db/base.py` so Alembic autogenerate detects both new models
- [X] T003 [P] Create `FieldChangeRead` and `TaskHistoryRead` Pydantic schemas in `backend/app/schemas/history.py` (see contracts/api.md for field list)
- [X] T004 Run `check-migration` agent then generate migration with `alembic revision --autogenerate -m "add_task_history"` — output file goes to `backend/alembic/versions/`
- [X] T005 [P] Add `FieldChange` and `TaskHistoryEntry` TypeScript interfaces to `frontend/src/types/domain.ts` (see contracts/api.md for shape)
- [X] T006 [P] Add `taskHistory(taskId: string)` method to the `api` object in `frontend/src/api/client.ts` — calls `GET /api/tasks/{taskId}/history`

**Checkpoint**: Data layer ready — migration exists, models importable, TypeScript types defined, API client method ready.

---

## Phase 2: User Story 3 — Automatic History Capture (P3)

**Goal**: Every task save that modifies at least one field produces a `TaskChangeRecord` with `FieldChange` rows, written atomically in the same transaction.

**Note**: Although P3 in the spec (no direct UI), this phase must precede US1 and US2 to produce data for them.

**Independent Test**: Edit a task field, save it, then query `GET /api/tasks/{task_id}/history` and confirm a history entry appears with the correct WAS/BECAME values.

### Tests for User Story 3 (write first — must fail before T008)

- [X] T007 [US3] Write pytest tests for history capture in `backend/tests/test_task_history.py`:
  - Login, create task, update one field → assert one history record with one `FieldChange`
  - Update multiple fields at once → assert single record with multiple `FieldChange` rows
  - Open edit form, save without changes → assert no new history record created
  - Update via `PATCH /api/tasks/{task_id}/status` → assert history record created
  - Delete task → assert history records are gone (cascade)

### Implementation for User Story 3

- [X] T008 [US3] Add `_capture_history()` helper and call it in `update_task()` in `backend/app/services/tasks.py` — compare old vs new field values, create `TaskChangeRecord` + `FieldChange` rows in the same transaction (see data-model.md for field serialization rules)
- [X] T009 [US3] Call the same `_capture_history()` helper in `update_task_status()` in `backend/app/services/tasks.py`
- [X] T010 [US3] Run `cd backend && pytest tests/test_task_history.py` and confirm T007 tests pass (green)

**Checkpoint**: History is captured on every task update. Backend tests pass. US1 and US2 now have data to display.

---

## Phase 3: User Story 1 — View Task History List (P1) 🎯 MVP

**Goal**: Users click a history button (between Edit and Delete) on a task row and see a list of all change events, each showing timestamp, author name, and a brief field summary.

**Independent Test**: Open a task that has been edited at least once → click the history button → a panel appears listing change entries in reverse chronological order, each with timestamp, author, and changed field names.

### Tests for User Story 1 — Backend (write first — must fail before T012)

- [X] T011 [US1] Write pytest tests for `GET /api/tasks/{task_id}/history` in `backend/tests/test_task_history.py`:
  - Authenticated owner → `200` with history list including `changed_by_name`, `created_at`, `fields`
  - Task with no history → `200` with empty list `[]`
  - Wrong user → `404` (ownership enforced)
  - Unauthenticated → `401`
  - List is in reverse chronological order (most recent first)

### Implementation for User Story 1 — Backend

- [X] T012 [US1] Create `get_task_history()` in `backend/app/services/history.py` — first verify the task exists and belongs to `user_id` (follow the same ownership check pattern as `get_task()` in `tasks.py`; return `None` if not found so the route handler can return 404); then query `TaskChangeRecord` rows for `(task_id, user_id)` with eager-loaded `fields` and joined `user.display_name`, ordered by `created_at DESC`
- [X] T013 [US1] Add `GET /api/tasks/{task_id}/history` route in `backend/app/api/tasks.py` — thin handler delegating to `get_task_history()`, returns `list[TaskHistoryRead]`
- [X] T014 [US1] Run `cd backend && pytest tests/test_task_history.py` and confirm T011 tests pass (green)

### Tests for User Story 1 — Frontend (write first — must fail before T016)

- [X] T015 [P] [US1] Write Vitest tests for `TaskHistory` component in `frontend/src/features/tasks/TaskHistory.test.tsx`:
  - Renders a list of history entries (timestamp, author, field summary)
  - Shows empty-state message when history array is empty
  - Each entry is clickable (onClick prop fires)
  - Calls `api.taskHistory(taskId)` on mount

### Implementation for User Story 1 — Frontend

- [X] T016 [US1] Create `TaskHistory` component in `frontend/src/features/tasks/TaskHistory.tsx` — fetches `api.taskHistory(task.id)`, renders each `TaskHistoryEntry` as a clickable row showing `created_at` (formatted), `changed_by_name`, and comma-joined `field_name` list; shows empty-state when list is empty
- [X] T017 [US1] Modify `frontend/src/features/tasks/TaskBoard.tsx`: add `historyTask` state, render a `History` (lucide-react) icon button between the `Pencil` and `Trash2` buttons for each task row, toggle `TaskHistory` panel on click
- [X] T018 [US1] Run `cd frontend && npm test` and confirm T015 tests pass (green)

**Checkpoint**: History button visible in task row, panel opens, list rendered. US1 fully functional.

---

## Phase 4: User Story 2 — View Field Diff in Modal (P2)

**Goal**: Clicking a history list entry opens a modal showing a WAS → BECAME table for every changed field in that event.

**Independent Test**: Open history panel for a task with at least one edit → click any entry → modal opens showing each changed field with WAS and BECAME values clearly labeled; closing modal returns to the list.

### Tests for User Story 2 — Frontend (write first — must fail before T020)

- [X] T019 [US2] Write Vitest tests for `TaskHistoryModal` in `frontend/src/features/tasks/TaskHistoryModal.test.tsx`:
  - Renders modal with correct `created_at`, `changed_by_name`
  - Renders a row per `FieldChange` with `field_name`, `old_value` (WAS), `new_value` (BECAME)
  - Displays `—` or "empty" indicator for null `old_value` or `new_value`
  - Calls `onClose` when close button clicked
  - Calls `onClose` when backdrop clicked

### Implementation for User Story 2 — Frontend

- [X] T020 [US2] Create `TaskHistoryModal` component in `frontend/src/features/tasks/TaskHistoryModal.tsx` — receives a `TaskHistoryEntry` prop, renders an overlay modal with header (timestamp + author), a table of field changes with WAS and BECAME columns, a close button; clicking backdrop closes modal
- [X] T021 [US2] Wire `TaskHistoryModal` into `TaskHistory.tsx` — add `selectedEntry` state, pass `onEntryClick` callback that sets `selectedEntry`, render `<TaskHistoryModal>` when `selectedEntry` is non-null
- [X] T022 [US2] Run `cd frontend && npm test` and confirm T019 tests pass (green)

**Checkpoint**: History list entries clickable, modal opens with WAS → BECAME diff. US2 fully functional.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Full pre-commit validation and manual end-to-end check.

- [X] T023 Run full check suite: `cd backend && pytest` (all tests), `cd frontend && npm test && npm run build` — all must pass
- [X] T024 [P] Run `check-migration` agent to confirm migration is in sync with current models
- [X] T025 [P] Manual browser validation: start app → edit a task → open history → verify entry appears with correct author, timestamp, and fields → click entry → verify modal shows WAS/BECAME for each changed field → close modal → delete task → confirm task (and history) gone

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Foundational)**: No dependencies — start immediately
- **Phase 2 (US3 Capture)**: Depends on Phase 1 (needs ORM models + Pydantic schemas) — BLOCKS US1 and US2 having meaningful test data
- **Phase 3 (US1 List)**: Depends on Phase 1 + Phase 2
- **Phase 4 (US2 Modal)**: Depends on Phase 3 (reuses `TaskHistoryEntry` type and modal is opened from `TaskHistory`)
- **Phase 5 (Polish)**: Depends on all implementation phases complete

### User Story Dependencies

- **US3 (Capture)**: Only depends on foundational models — no UI dependency
- **US1 (List)**: Depends on US3 having captured at least one record to make tests meaningful; also depends on backend endpoint
- **US2 (Modal)**: Depends on US1 (modal is launched from the history list component)

### Within Each Phase

- Backend tests (T007, T011) written **before** implementation — must fail first (red)
- Frontend tests (T015, T019) written **before** implementation — must fail first (red)
- ORM models before service logic; service logic before route handlers
- Types and API client (T005, T006) can be created in parallel with backend work

### Parallel Opportunities

- T003, T005, T006 can run in parallel with T001/T002 (different files)
- T015 (frontend test) can be written in parallel with T011–T013 (different stack)
- T019 (modal test) can be written in parallel with T016–T017 (different component)

---

## Parallel Example: Phase 3 (US1)

```bash
# Backend and frontend test writing can proceed in parallel:
Task T011: Write pytest tests for GET /api/tasks/{task_id}/history in backend/tests/test_task_history.py
Task T015: Write Vitest tests for TaskHistory in frontend/src/features/tasks/TaskHistory.test.tsx

# After T011 fails (red) → implement backend:
Task T012: Create get_task_history() in backend/app/services/history.py
Task T013: Add route in backend/app/api/tasks.py

# After T015 fails (red) → implement frontend:
Task T016: Create TaskHistory.tsx in frontend/src/features/tasks/
Task T017: Modify TaskBoard.tsx (history button + panel state)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Foundational)
2. Complete Phase 2 (US3 — Capture, needed for US1 to have data)
3. Complete Phase 3 (US1 — History List)
4. **STOP and VALIDATE**: Open history panel in browser — change events visible
5. Ship if sufficient value delivered

### Incremental Delivery

1. Phase 1 → Foundation ready
2. Phase 2 → History captured (backend only, no UI yet)
3. Phase 3 → History visible in UI (MVP!)
4. Phase 4 → Field-diff modal added
5. Phase 5 → Pre-commit suite passes, browser validated

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks in the same phase
- Constitution Principle III mandates test-first: write tests → confirm red → implement → confirm green
- `check-migration` agent MUST be run after T001/T002 (new ORM models) and again in T024 (final check)
- `_capture_history()` helper must handle null/empty field values gracefully (see data-model.md serialization table)
- `changed_by_name` is resolved via join at read time — not stored on the history record
- The history button uses `History` icon from `lucide-react` (already installed)
