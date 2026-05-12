# Tasks: History UI — Styled Table and Change Detail Modal

**Input**: Design documents from `specs/002-history-ui-table-modal/`
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅

**Tests**: Included — constitution Principle III mandates Vitest + Testing Library tests for all frontend features. Follow Red-Green-Refactor: write tests first, confirm they fail, then implement.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no incomplete dependencies)
- **[Story]**: Which user story this task belongs to ([US1], [US2])

---

## Phase 1: Setup

**Purpose**: Confirm baseline before touching any production files.

- [X] T001 Run `cd frontend && npm test` to confirm all existing tests pass before changes

**Checkpoint**: All existing tests green → safe to proceed

---

## Phase 3: User Story 1 — Styled History Table (Priority: P1) 🎯 MVP

**Goal**: Replace unstyled Tailwind-class rendering in the history table with proper CSS classes; add scrollable body with sticky header; apply blue-grey header background and consistent padding.

**Independent Test**: Open the history panel for any task → verify a bordered table with bold blue-grey headers (When / Changed By / Fields Changed) is rendered; verify rows scroll vertically when more than ~5 entries exist.

### Tests for User Story 1 ⚠️ Write first — must FAIL before T004

- [X] T002 [US1] Extend `frontend/src/features/tasks/TaskHistory.test.tsx` — add: (a) test that the table is wrapped in an element with class `history-table-wrapper`; (b) test that the `<table>` has class `history-table`; (c) test that header cells contain text "When", "Changed By", "Fields Changed" (already present — keep); (d) remove any assertion expecting `TaskHistoryModal` to render inside `TaskHistory`

### Implementation for User Story 1

- [X] T003 [P] [US1] Add `.history-table-wrapper`, `.history-table`, `.history-table-head`, `.history-table-body`, `.history-table-row`, column-width rules (`th/td:nth-child` proportions 38/28/34%), `thead th` background `#eef4f7`, `tbody tr` hover and divider styles, and `td` padding/nowrap rules to `frontend/src/styles/global.css` — full CSS block per plan.md Phase 1 Design section
- [X] T004 [US1] Refactor `frontend/src/features/tasks/TaskHistory.tsx` — wrap `<table>` in `<div className="history-table-wrapper">`; set `className="history-table"` on `<table>`; set `className="history-table-head"` on `<thead>`, `className="history-table-body"` on `<tbody>`, `className="history-table-row"` on each data `<tr>`; remove all Tailwind utility class names; keep existing fetch logic and empty/loading states unchanged (depends on T002 tests failing, T003 CSS in place)

**Checkpoint**: `npm test` — TaskHistory tests pass; open browser → history table has blue-grey bold header, padded rows, thin dividers, and scrolls when overflow

---

## Phase 4: User Story 2 — Change Detail Modal (Priority: P2)

**Goal**: Fix the modal so it renders as a true fixed full-screen overlay (not inline); apply CSS classes; lift modal state to `TaskBoard`; update modal header to show author + timestamp.

**Independent Test**: Click any history table row → a centered modal appears with semi-transparent overlay; modal header shows author and timestamp; Field/Was/Became table renders change details; modal closes via ×, backdrop click, and Escape.

### Tests for User Story 2 ⚠️ Write first — must FAIL before T008-T010

- [X] T005 [P] [US2] Extend `frontend/src/features/tasks/TaskHistoryModal.test.tsx` — add: (a) test that the backdrop element has class `history-modal-backdrop`; (b) test that the dialog has class `history-modal`; (c) test that modal header displays `entry.changed_by_name`; (d) confirm existing close-via-×, close-via-backdrop, close-via-Escape tests are present (already there — keep); (e) confirm Field/Was/Became table rows render correctly (already there — keep)
- [X] T006 [P] [US2] Add tests to `frontend/src/features/tasks/TaskBoard.test.tsx` — (a) clicking a history entry row causes `TaskHistoryModal` to appear in the DOM; (b) triggering `onClose` on the modal removes it from the DOM; mock `api.taskHistory` and `api.tasks` as needed

### Implementation for User Story 2

- [X] T007 [P] [US2] Add `.history-modal-backdrop`, `.history-modal`, `.history-modal-header`, `.history-modal-title`, `.history-modal-subtitle` CSS rules to `frontend/src/styles/global.css` — full CSS block per plan.md Phase 1 Design section (position: fixed, inset: 0, z-index: 50, flex centering for backdrop; white bg, border-radius 10px, shadow, padding 24px for dialog)
- [X] T008 [P] [US2] Refactor `frontend/src/features/tasks/TaskHistoryModal.tsx` — replace `className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"` with `className="history-modal-backdrop"`; replace inner div Tailwind classes with `className="history-modal"`; replace header div with `<div className="history-modal-header">` containing `<div className="history-modal-title">{entry.changed_by_name}</div>` and `<div className="history-modal-subtitle">{new Date(entry.created_at).toLocaleString()}</div>` and the existing `×` close button; replace internal table Tailwind classes with `className="history-table"` (reuse table CSS from US1); keep Escape-key handler and stopPropagation logic unchanged
- [X] T009 [US2] Update `frontend/src/features/tasks/TaskHistory.tsx` — remove `selectedEntry` state; remove internal `TaskHistoryModal` import and render; ensure `handleEntryClick` only calls `props.onEntryClick(entry)` without setting local state; no other changes (depends on T004 — same file)
- [X] T010 [US2] Update `frontend/src/features/tasks/TaskBoard.tsx` — add `import type { TaskHistoryEntry }` from `../../types/domain`; add `const [selectedHistoryEntry, setSelectedHistoryEntry] = useState<TaskHistoryEntry | null>(null)`; update `<TaskHistory onEntryClick={(entry) => setSelectedHistoryEntry(entry)} />`; add `import { TaskHistoryModal }` from `./TaskHistoryModal`; render `{selectedHistoryEntry && <TaskHistoryModal entry={selectedHistoryEntry} onClose={() => setSelectedHistoryEntry(null)} />}` at the top level of the return, outside `.history-panel` (depends on T009)

**Checkpoint**: `npm test` — all tests pass; open browser → clicking a history row opens a centered modal overlay with semi-transparent backdrop; all three close behaviors work

---

## Phase 5: Polish & Cross-Cutting Concerns

- [X] T011 Run `cd frontend && npm test` — verify all tests pass (0 failures)
- [X] T012 Run `cd frontend && npm run build` — verify TypeScript build completes with no errors

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1 / T001)**: No dependencies — run immediately
- **US1 (Phase 3)**: Depends on T001 completion
- **US2 (Phase 4)**: Depends on US1 (T004) completion — T009 touches the same file (`TaskHistory.tsx`)
- **Polish (Phase 5)**: Depends on all US2 tasks complete

### User Story Dependencies

- **US1 (T002–T004)**: Depends only on T001; no dependency on US2
- **US2 (T005–T010)**: T005/T006/T007/T008 can start after T001; T009 depends on T004; T010 depends on T009

### Within Each User Story

```
US1: T002 (tests, fail) → T003+T004 (implement) → verify green
US2: T005+T006+T007+T008 (parallel) → T009 → T010 → verify green
```

---

## Parallel Examples

### User Story 1

```bash
# Can run in parallel:
Task T002: Update TaskHistory.test.tsx
Task T003: Add history-table CSS to global.css

# Then sequential:
Task T004: Refactor TaskHistory.tsx (depends on T002 + T003)
```

### User Story 2

```bash
# Can run in parallel after T001:
Task T005: Update TaskHistoryModal.test.tsx
Task T006: Update TaskBoard.test.tsx
Task T007: Add history-modal CSS to global.css
Task T008: Refactor TaskHistoryModal.tsx

# Then sequential:
Task T009: Remove internal modal state from TaskHistory.tsx (depends on T004)
Task T010: Update TaskBoard.tsx modal state management (depends on T009)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. T001 — baseline check
2. T002 → T003 + T004 — styled table complete
3. **STOP and VALIDATE**: history panel shows styled table in browser
4. Proceed to US2 when ready

### Incremental Delivery

1. T001 → confirm baseline
2. US1 complete → styled table visible in production
3. US2 complete → modal overlay works correctly
4. T011 + T012 → full test and build validation

---

## Notes

- [P] tasks = different files, no incomplete dependencies
- Red-Green-Refactor: T002 / T005 / T006 tests MUST fail before T004 / T008 / T009 / T010
- Do NOT add Tailwind CSS — all styling via `global.css` custom classes (confirmed in clarifications)
- `TaskHistoryModal` must be rendered outside `.history-panel` in `TaskBoard.tsx` to ensure `position: fixed` works correctly (history-panel has `overflow: hidden`)
- Reuse `.history-table` and `.history-table-wrapper` classes in `TaskHistoryModal` for the Field/Was/Became comparison table (DRY; same visual style)
