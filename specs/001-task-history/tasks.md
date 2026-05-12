# Tasks: Task Change History

**Input**: Design documents from `specs/001-task-history/`  
**Prerequisites**: plan.md ✅ · spec.md ✅ · research.md ✅ · data-model.md ✅ · contracts/api.md ✅ · quickstart.md ✅

**Tests**: Included — Constitution Principle III (Test-First) is NON-NEGOTIABLE for this project.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no pending dependencies)
- **[Story]**: Which user story this task belongs to (US1 / US2 / US3)

---

## Phase 1: Setup

**Purpose**: Register new ORM models so Alembic autogenerate can detect them.

- [X] T001 Register `TaskChangeRecord` and `FieldChange` imports in `backend/app/db/base.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database schema, Pydantic contracts, and TypeScript types — required before any user story can be implemented or tested end-to-end.

**⚠️ CRITICAL**: No user story implementation begins until this phase is complete.

- [X] T002 [P] Create ORM models `TaskChangeRecord` and `FieldChange` in `backend/app/models/task_history.py` — two SQLAlchemy 2.0 async models; `TaskChangeRecord` has FK `task_id → tasks.id CASCADE`, FK `user_id → users.id CASCADE`, inherits `TimestampMixin`; `FieldChange` has FK `history_id → task_history.id CASCADE`, columns `field_name VARCHAR(50)`, `old_value TEXT|NULL`, `new_value TEXT|NULL`; composite index on `(task_id, created_at DESC)` on `task_history` table
- [X] T003 [P] Create Pydantic schemas `FieldChangeRead` and `TaskHistoryRead` in `backend/app/schemas/history.py` — per contracts/api.md: `FieldChangeRead(field_name, old_value, new_value)`, `TaskHistoryRead(id, task_id, changed_by_name, created_at, fields: list[FieldChangeRead])`, both with `model_config = ConfigDict(from_attributes=True)`
- [X] T004 Run `check-migration` agent to verify T001+T002 are detected — then generate migration using `python scripts/new_migration.py add_task_history` producing `backend/alembic/versions/0004_add_task_history.py` with `task_history` and `task_history_fields` tables, FKs, and composite index
- [X] T005 Apply migration: `cd backend && alembic upgrade head` — verify both tables exist in DB
- [X] T006 [P] Add TypeScript types `FieldChange` and `TaskHistoryEntry` to `frontend/src/types/domain.ts` — per contracts/api.md: `FieldChange { field_name, old_value, new_value }`, `TaskHistoryEntry { id, task_id, changed_by_name, created_at, fields: FieldChange[] }`

**Checkpoint**: DB schema applied, Pydantic schemas and TS types defined. User story implementation can now begin.

---

## Phase 3: User Story 1 — View Task Change History List (Priority: P1) 🎯 MVP

**Goal**: History button on each task row opens a styled inline panel showing a table with columns When / Changed By / Fields Changed.

**Independent Test**: Click the history button on a task (even with no changes) → panel appears with table headers and either rows or an empty-state message. Verify toggle: second click closes the panel. Verify single-panel: opening panel for task B closes any open panel.

### Tests for User Story 1

> **Write tests FIRST — they MUST FAIL before implementation begins (Constitution III)**

- [X] T007 [P] [US1] Write pytest tests for `GET /api/tasks/{task_id}/history` in `backend/tests/test_task_history.py` — cover: returns `[]` for task with no history; returns 401 without session; returns 404 for another user's task; returns 200 with correct schema shape for a task with seeded history rows (use direct `session.add()` in test setup to insert `TaskChangeRecord` + `FieldChange` rows)
- [X] T008 [P] [US1] Write Vitest tests for `TaskHistory` component in `frontend/src/features/tasks/TaskHistory.test.tsx` — cover: renders table with headers When / Changed By / Fields Changed; renders one row per history entry; shows empty-state message when entries list is empty; calls `onSelectEntry` with correct entry when a row is clicked; Fields Changed cell shows comma-separated field labels (e.g., "Description, Priority")

### Implementation for User Story 1

- [X] T009 [US1] Implement `get_task_history()` in `backend/app/services/history.py` — async function `(task_id: str, user_id: str, session: AsyncSession) → list[TaskHistoryRead]`; verify task ownership (404 if not found or wrong owner); query `task_history` joined with `users` for `display_name` and eager-load `task_history_fields`; order by `created_at DESC`; return list of `TaskHistoryRead`
- [X] T010 [US1] Add `GET /api/tasks/{task_id}/history` route to `backend/app/api/tasks.py` — thin handler: call `get_task_history(task_id, current_user.id, session)`; return `list[TaskHistoryRead]`; no business logic in handler
- [X] T011 [P] [US1] Add `taskHistory(taskId: string)` method to `frontend/src/api/client.ts` — `request<TaskHistoryEntry[]>(\`/api/tasks/\${taskId}/history\`)` (depends on T006)
- [X] T012 [US1] Implement `TaskHistory` component in `frontend/src/features/tasks/TaskHistory.tsx` — props: `{ taskId: string; taskTitle: string; onSelectEntry: (entry: TaskHistoryEntry) => void; onClose: () => void }`; fetches history via `api.taskHistory(taskId)` on mount; renders panel with header "History [taskTitle]" + close button; styled table per plan.md Visual Design: outer container `rounded-lg border border-gray-200 bg-white mx-2 my-1`; table `w-full border-collapse overflow-hidden rounded-lg`; header row `bg-blue-50` with `<th>` cells `font-semibold text-sm text-gray-700 px-4 py-2 text-left`; data rows `bg-white hover:bg-gray-50 cursor-pointer border-t border-gray-100`; When column `whitespace-nowrap`; Fields Changed cell: join `entry.fields.map(f => f.field_name)` with ", "; empty-state message when entries list is empty; format timestamp using `new Date(entry.created_at).toLocaleString()` matching pattern "5/11/2026, 6:58:32 PM"
- [X] T013 [US1] Add history button and single-panel toggle logic to `frontend/src/features/tasks/TaskBoard.tsx` — add `History` icon button (from `lucide-react`) between the existing edit and delete buttons; track `openHistoryTaskId: string | null` in component state; clicking history button for task X: if `openHistoryTaskId === X` then set to null (close), else set to X (open, implicitly closing any other panel); render `<TaskHistory>` panel below task row when `openHistoryTaskId` matches; pass `onClose={() => setOpenHistoryTaskId(null)}`

**Checkpoint**: History button visible; panel opens/closes as toggle; only one panel at a time; table renders with correct columns and styling; row click calls `onSelectEntry` (modal wired in next phase).

---

## Phase 4: User Story 2 — View Detailed Field Diff in Modal (Priority: P2)

**Goal**: Clicking any history row opens a styled modal overlay with a Field / Was / Became table showing the full diff for that change event.

**Independent Test**: Click any history row → modal appears centered over dimmed backdrop; Field / Was / Became table shows correct values; X button, backdrop click, and Escape all close the modal and return to the history panel (panel stays visible).

### Tests for User Story 2

> **Write tests FIRST — they MUST FAIL before implementation begins (Constitution III)**

- [X] T014 [P] [US2] Write Vitest tests for `TaskHistoryModal` in `frontend/src/features/tasks/TaskHistoryModal.test.tsx` — cover: renders modal with Field / Was / Became columns; each changed field appears as a row with correct field_name, old_value, new_value; X button calls `onClose`; Escape key calls `onClose`; backdrop click calls `onClose`; null/empty values render as blank cell (not error); Was and Became cells have `max-h-24 overflow-y-auto` class

### Implementation for User Story 2

- [X] T015 [US2] Implement `TaskHistoryModal` component in `frontend/src/features/tasks/TaskHistoryModal.tsx` — props: `{ entry: TaskHistoryEntry; onClose: () => void }`; styled per plan.md Visual Design: backdrop `fixed inset-0 bg-black/50 flex items-center justify-center z-50`; modal card `bg-white rounded-xl shadow-lg p-6 w-full max-w-lg mx-4 relative`; X close button `absolute top-3 right-3 text-gray-400 hover:text-gray-600` using `X` icon from `lucide-react`; table `w-full border border-gray-200 rounded-lg overflow-hidden`; header row `bg-gray-50` with `<th>` cells `font-semibold text-sm px-3 py-2 text-left`; data rows `bg-white border-t border-gray-200`; `<td>` cells `px-3 py-2 text-sm text-gray-700 align-top`; Was and Became cells `max-h-24 overflow-y-auto`; no modal title or timestamp header; Escape key listener via `useEffect` with cleanup on unmount; backdrop click on overlay div (not card) calls `onClose`
- [X] T016 [US2] Wire row-click in `TaskHistory.tsx` to open `TaskHistoryModal` — add `selectedEntry: TaskHistoryEntry | null` state to `TaskHistory`; `onSelectEntry` sets `selectedEntry`; render `<TaskHistoryModal entry={selectedEntry} onClose={() => setSelectedEntry(null)} />` when `selectedEntry !== null`; closing modal returns user to history panel (panel stays open)

**Checkpoint**: Full US1 + US2 flow works in browser: panel opens → row click → modal → dismiss → back to panel.

---

## Phase 5: User Story 3 — History Captured Automatically on Task Edit (Priority: P3)

**Goal**: Every call to `update_task()` or `update_task_status()` that changes at least one field creates a `TaskChangeRecord` + `FieldChange` rows atomically in the same DB transaction. No record created if nothing changed.

**Independent Test**: Edit a task field and save → open history panel → new row appears at top. Edit without changing → no new row. Edit multiple fields at once → one row with all changed fields listed. Verify no capture on task creation.

### Tests for User Story 3

> **Write tests FIRST — they MUST FAIL before implementation begins (Constitution III)**

- [X] T017 [P] [US3] Add capture behaviour tests to `backend/tests/test_task_history.py` — cover: editing one field creates exactly one `TaskChangeRecord` with one `FieldChange`; editing multiple fields in one save creates one record with multiple `FieldChange` rows; saving without changes creates no record; task creation creates no history record; `update_task_status()` creates a history record when status changes; old_value and new_value stored per field serialization convention (Title/Description: plain string; Status: "To Do"/"In Progress"/"Done"; Priority: "Low"/"Medium"/"High"; Due Date: ISO 8601 date string or None)

### Implementation for User Story 3

- [X] T018 [US3] Implement `_capture_history()` helper in `backend/app/services/tasks.py` — signature: `async def _capture_history(task_id: str, user_id: str, before: dict, after: dict, session: AsyncSession) → None`; compare `before` vs `after` for keys `title`, `description`, `status`, `priority`, `due_date`; serialize values to strings per data-model.md field serialization convention and human-readable label names (Title, Description, Status, Priority, Due Date); if at least one field differs: create `TaskChangeRecord(task_id=task_id, user_id=user_id)` and one `FieldChange(field_name=..., old_value=..., new_value=...)` per changed field; `session.add()` all within the same transaction; if nothing changed: return without any DB write
- [X] T019 [US3] Integrate `_capture_history()` into `update_task()` in `backend/app/services/tasks.py` — snapshot field values before applying mutations; apply existing update logic; call `_capture_history(task.id, user_id, before, after, session)` before commit
- [X] T020 [US3] Integrate `_capture_history()` into `update_task_status()` in `backend/app/services/tasks.py` — snapshot status before update; call `_capture_history()` with before/after dicts after applying status change

**Checkpoint**: All three user stories fully functional end-to-end. Edit a task → panel shows new entry → click row → modal shows correct Field/Was/Became diff.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T021 Run full test suite — `cd backend && source .venv/bin/activate && pytest` (all pass); then `cd frontend && npm test && npm run build` (all Vitest tests pass, build succeeds with no type errors)
- [X] T022 End-to-end validation per `specs/001-task-history/quickstart.md` — exercise full flow: create task, edit multiple times, verify panel opens with styled table, click row to open modal, verify Field/Was/Became values, verify toggle behavior, verify single-panel constraint, verify all three modal dismissal methods (X / backdrop / Escape)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories
- **Phase 3 (US1 - P1)**: Depends on Phase 2 complete
- **Phase 4 (US2 - P2)**: Depends on Phase 3 complete (needs TaskHistory.tsx to wire modal into)
- **Phase 5 (US3 - P3)**: Depends on Phase 2 complete — backend-only, can run in parallel with Phase 3/4
- **Phase 6 (Polish)**: Depends on all desired stories complete

### User Story Dependencies

| Story | Depends On | Independent Test |
|-------|-----------|-----------------|
| US1 (P1) | Phase 2 | Panel + table visible; toggle works; rows clickable |
| US2 (P2) | US1 (modal wired into TaskHistory.tsx) | Modal appears; diff table correct; all 3 dismiss methods work |
| US3 (P3) | Phase 2 | Backend: editing creates DB records; no spurious records |

> **Note**: US1 and US2 can be demonstrated with manually seeded test data before US3 (capture) is wired. US3 enables real data to flow end-to-end.

### Within Each User Story

1. Write tests (they MUST fail) → implement → tests pass
2. Schemas/types before services
3. Services before endpoint handlers
4. Backend endpoint before frontend API client integration
5. Core component before wiring/integration tasks

### Parallel Opportunities

- T002 + T003 + T006 can run in parallel (different files: ORM models, Pydantic schemas, TS types)
- T007 + T008 can run in parallel (different test files: pytest vs Vitest)
- T011 + T014 can run in parallel with T009/T010 (different files)
- T017 can run in parallel with T012/T013/T015/T016 (backend vs frontend files)

---

## Parallel Example: Phase 2 Foundational

```bash
# Run in parallel (different files):
T002: backend/app/models/task_history.py
T003: backend/app/schemas/history.py
T006: frontend/src/types/domain.ts

# Then sequentially:
T004: check-migration agent → generate 0004_add_task_history.py
T005: alembic upgrade head
```

## Parallel Example: Phase 3 US1

```bash
# Write tests in parallel first:
T007: backend/tests/test_task_history.py
T008: frontend/src/features/tasks/TaskHistory.test.tsx

# Then implement:
T009: services/history.py            (start)
T010: api/tasks.py                   (after T009)
T011: api/client.ts                  (parallel with T009)
T012: TaskHistory.tsx                (after T011)
T013: TaskBoard.tsx                  (after T012)
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Phase 1: Setup (T001)
2. Phase 2: Foundational (T002–T006)
3. Phase 3: US1 (T007–T013)
4. **STOP and VALIDATE**: Panel opens, styled table renders, toggle works
5. Seed a `TaskChangeRecord` manually in tests to verify rows appear

### Incremental Delivery

1. Setup + Foundational → DB schema ready, types defined
2. US1 → history panel with styled table (may show empty list until US3)
3. US2 → detail modal fully functional
4. US3 → real capture wired; full end-to-end flow
5. Polish → full suite passes; quickstart validated

---

## Notes

- [P] tasks operate on different files and have no pending dependency — safe to run concurrently
- Constitution Principle III: tests written and FAILING before implementation in every phase
- Visual styling in T012 and T015 directly references `plan.md § Visual Design Implementation Notes` for Tailwind classes
- After T002 (model change), the `check-migration` agent (T004) MUST run before any migration is created
- Field serialization convention in `data-model.md § Field Serialization Convention`
- T017 modifies the same test file as T007 (adds more tests); ensure T007 is complete before T017 starts
