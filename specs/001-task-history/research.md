# Research: Task Change History

## Summary

All technology choices are fully determined by the project constitution. This file documents the key design decisions made for the history feature without external research required.

---

## Decision 1: History capture point

**Decision**: Record history inside `services/tasks.py` → `update_task()`, within the same database transaction as the task save.

**Rationale**: Guarantees consistency — either both the task update and the history record are committed, or neither is. No risk of a missed capture if the transaction rolls back.

**Alternatives considered**:
- Post-commit hook / signal — discarded because it runs outside the transaction boundary; a process crash between commit and hook fires would silently drop history.
- Separate async job — discarded (over-engineering for a personal app; adds complexity with no measurable benefit).

---

## Decision 2: History data model shape

**Decision**: Two tables — `task_history` (one row per save event) and `task_history_fields` (one row per changed field per save event).

**Rationale**: Normalised structure keeps queries simple for both list view (fetch `task_history` rows) and detail view (fetch `task_history_fields` for a given history row). Avoids storing JSON blobs, which are harder to query and validate.

**Alternatives considered**:
- Single table with JSON `changes` column — discarded because it prevents indexed queries on specific fields and requires JSON parsing in application code.
- Append-only snapshot per save (store full task state) — discarded (too much redundant data; harder to show a diff).

---

## Decision 3: Cascade delete strategy

**Decision**: `task_history.task_id` has `ondelete="CASCADE"` at the database level. `task_history_fields.history_id` also has `ondelete="CASCADE"`. No application-level cleanup needed.

**Rationale**: Database-enforced cascade is atomic and does not require a service layer change. Consistent with how `Task` itself cascades from `ProjectList` and `User`.

**Alternatives considered**:
- Soft delete (mark as deleted, filter on read) — discarded; the spec explicitly chose cascade delete and the app has no recycle bin.

---

## Decision 4: Author identity storage

**Decision**: Store `user_id` (FK to `users`) on each `task_history` row. Resolve `display_name` via a join at read time (not denormalized).

**Rationale**: Simpler schema. In a personal app the user's display name rarely changes; if it does, showing the current name is acceptable. Joining `users` is a single-row lookup by primary key.

**Alternatives considered**:
- Denormalize `display_name` at write time — would require a snapshot column; adds schema complexity for a very low-frequency update scenario.

---

## Decision 5: API shape

**Decision**: Single endpoint `GET /api/tasks/{task_id}/history` returns a list of history entries, each with its field changes embedded (eager-loaded). No separate endpoint for individual field-change detail.

**Rationale**: The frontend needs both list and detail data; embedding field changes avoids a second round-trip for the modal. The total payload is small (a task rarely has hundreds of changes, each with at most 5 changed fields).

**Alternatives considered**:
- Separate `GET /api/tasks/{task_id}/history/{history_id}` for detail — discarded because it adds a round-trip with no benefit when the full payload is already small.

---

## Decision 6: Frontend component structure

**Decision**: Two new components — `TaskHistory` (inline panel toggled by the history button) and `TaskHistoryModal` (detail overlay). Both live in `features/tasks/`.

**Rationale**: Follows the existing feature-folder pattern (`TaskForm` is already in `features/tasks/`). Keeps all task-related UI co-located. History panel toggled via local state in `TaskBoard` (no global state needed).

**Alternatives considered**:
- Full-page route for history — discarded per spec ("inline panel or dropdown anchored to the task row").
- Single component with conditional rendering — discarded in favour of separation of concerns and independent testability.

---

## Decision 7: History button icon

**Decision**: Use `History` icon from `lucide-react` (already a dependency).

**Rationale**: The `History` icon is semantically correct and available in the existing icon library; no new dependency needed.

---

## Decision 8: History list presentation format

**Decision**: Render history entries in `TaskHistory.tsx` as an HTML `<table>` with column headers **When**, **Changed By**, and **Fields Changed**. Each row is a clickable `<tr>` that opens the detail modal.

**Rationale**: A table aligns timestamps, authors, and field summaries in consistent columns, making the list easier to scan than an unstructured bullet list. The column headers provide immediate context without requiring the user to infer the meaning of each value. This is the format explicitly requested via clarification.

**Alternatives considered**:
- Bullet list (`<ul>/<li>`) — discarded; lacks column alignment and headers; was the original implementation.
- Card grid — discarded; over-engineered for three fields per row.

---

## Decision 9: Detail modal dismissal methods

**Decision**: `TaskHistoryModal.tsx` supports three dismissal methods: (1) click the × button, (2) click the darkened backdrop, (3) press the Escape key. All three must work independently.

**Rationale**: Escape key is the universal keyboard shortcut for closing a modal; omitting it breaks accessibility and keyboard-navigation conventions. Backdrop click and the × button were already implemented. Adding a `keydown` listener via `useEffect` with cleanup covers the keyboard path with no additional dependency.

**Implementation note**: The listener should be attached on mount and removed on unmount (`return () => document.removeEventListener(...)`) to prevent memory leaks.

**Alternatives considered**:
- X button only — discarded; blocks keyboard users.
- Browser `<dialog>` element with native Escape support — discarded; requires a larger refactor of the existing overlay approach and adds no benefit for this single modal.
