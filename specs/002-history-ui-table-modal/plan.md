# Implementation Plan: History UI — Styled Table and Change Detail Modal

**Branch**: `002-history-ui-table-modal` | **Date**: 2026-05-12 | **Spec**: [spec.md](./spec.md)

## Summary

Replace the current unstyled Tailwind-class-based rendering in `TaskHistory` and `TaskHistoryModal`
with properly styled components using the project's native CSS approach (custom classes in `global.css`).
The history table gains a bordered, scrollable layout with a blue-grey header; clicking a row opens
a true fixed-position modal overlay with a comparison table showing Field / Was / Became changes.

## Technical Context

**Language/Version**: TypeScript 5.4 / React 18  
**Primary Dependencies**: React, Vite — no new dependencies required  
**Storage**: N/A (frontend-only change)  
**Testing**: Vitest + Testing Library (existing test files for both components)  
**Target Platform**: Web desktop (Chrome/Firefox/Safari, ≥1024 px viewport)  
**Project Type**: Web application — frontend feature only  
**Performance Goals**: No specific targets; standard DOM rendering  
**Constraints**: No Tailwind CSS installed — all styling via `global.css` custom classes  
**Scale/Scope**: 2 components (`TaskHistory`, `TaskHistoryModal`), 1 CSS file (`global.css`)

## Root Cause

`TaskHistory.tsx` and `TaskHistoryModal.tsx` were written using Tailwind utility classes (e.g.,
`fixed inset-0 z-50`, `divide-y divide-gray-100`, `bg-black/40`). Tailwind is **not installed**
in this project (`package.json` has no `tailwindcss` dependency, no `postcss.config`). As a result:

- The history table renders with zero visual styling (no border, no header background, no padding).
- `TaskHistoryModal` renders as an inline block element (not a fixed overlay) because `fixed` and
  `inset-0` have no effect without Tailwind.

The fix is to replace all Tailwind class names in both components with CSS custom classes defined
in `global.css`, following the same pattern used by every other component in the project.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Layered Architecture | ✅ PASS | Frontend-only change; no route handlers or services touched |
| II. Security by Design | ✅ PASS | No auth, ownership, or cookie logic involved |
| III. Test-First | ✅ PASS | Existing test files for both components; tests must be updated / extended before implementation |
| IV. Schema Discipline | ✅ PASS | No ORM models or Pydantic schemas changed; no migration needed |
| V. Simplicity (YAGNI) | ✅ PASS | No new dependencies; uses existing CSS pattern; no new abstractions |

**Post-design re-check**: Same — no new scope introduced.

## Project Structure

### Documentation (this feature)

```text
specs/002-history-ui-table-modal/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output (minimal; no new data shapes)
└── tasks.md             ← Phase 2 output (/speckit-tasks)
```

### Source Code (affected files)

```text
frontend/
├── src/
│   ├── features/tasks/
│   │   ├── TaskHistory.tsx            ← replace Tailwind classes with CSS classes; add scroll
│   │   ├── TaskHistory.test.tsx       ← update/extend tests for styled table
│   │   ├── TaskHistoryModal.tsx       ← replace Tailwind classes with CSS classes; fix modal header
│   │   └── TaskHistoryModal.test.tsx  ← update/extend tests for modal header, overlay
│   └── styles/
│       └── global.css                 ← add .history-table, .history-modal-* CSS rules
```

## Phase 0: Research

*All unknowns resolved through code inspection. No external research needed.*

### research.md findings summary

See [research.md](./research.md) for full record. Key decisions:

| Decision | Rationale |
|----------|-----------|
| Use `global.css` custom classes | Tailwind not installed; all other components use this pattern |
| Add `.history-table-*` class family | Follows existing naming pattern (`.task-modal`, `.history-panel`) |
| Add `.history-modal-*` class family | Reuse visual language of `.task-modal` and `.modal-backdrop` |
| Modal rendered at document level via React portal | Avoids `.history-panel { overflow: hidden }` clipping; ensures true overlay |
| Max-height scroll on `<tbody>` | Fulfils FR-005a; uses `display: block` on tbody with `overflow-y: auto` |

## Phase 1: Design

### Component changes

#### `TaskHistory.tsx`

Replace the `<table>` block. Key changes:

- Wrap table in a `<div className="history-table-wrapper">` to apply border/radius/overflow.
- Add `className="history-table"` to `<table>`.
- `<thead>`: use `className="history-table-head"` — gets blue-grey background + bold text.
- `<tbody>`: use `className="history-table-body"` — gets max-height + `overflow-y: auto` + `display: block`.
- `<tr>` (header): `className="history-table-header-row"` (fixes column widths for scroll).
- `<tr>` (data): `className="history-table-row"` (hover, cursor pointer, same column widths).
- `<th>` / `<td>`: use `className="history-table-cell"` with appropriate column variant modifiers.

Remove `selectedEntry` state and internal `TaskHistoryModal` rendering from this component.
The modal is lifted to `TaskBoard` (see below) so the fixed overlay is not a child of `.history-panel`.

#### `TaskHistoryModal.tsx`

Replace Tailwind class names. Key changes:

- Outer overlay div: `className="history-modal-backdrop"` (position: fixed, inset: 0, z-index, semi-transparent).
- Inner dialog: `className="history-modal"` (centered, white bg, rounded, shadow, padding).
- Header: `className="history-modal-header"` showing `"Changes — [timestamp] by [author]"` plus `×` button.
- Table wrapper: `className="history-table-wrapper"` (reuse same class).
- Table, thead, tbody, rows, cells: same CSS classes as `TaskHistory` table.

#### `TaskBoard.tsx`

Lift modal state out of `TaskHistory` into `TaskBoard`:

- Add `selectedHistoryEntry: TaskHistoryEntry | null` state.
- Pass `onEntryClick={(entry) => setSelectedHistoryEntry(entry)}` to `<TaskHistory>`.
- Render `<TaskHistoryModal>` at the top level of `TaskBoard` return (outside `.history-panel`).
- This ensures the fixed overlay is not clipped by any ancestor with `overflow: hidden`.

### CSS changes in `global.css`

New rules to add after existing `.history-panel-title` block:

```css
/* History table */
.history-table-wrapper {
  margin: 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}

.history-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: 0.875rem;
}

.history-table-head tr,
.history-table-body tr {
  display: table;
  width: 100%;
  table-layout: fixed;
}

.history-table-body {
  display: block;
  max-height: 260px;
  overflow-y: auto;
}

.history-table thead th {
  background: #eef4f7;
  font-weight: 700;
  font-size: 0.8rem;
  color: #374151;
  padding: 10px 14px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}

.history-table tbody tr {
  border-bottom: 1px solid #f3f4f6;
  cursor: pointer;
}

.history-table tbody tr:last-child {
  border-bottom: none;
}

.history-table tbody tr:hover {
  background: #f7fafb;
}

.history-table td {
  padding: 10px 14px;
  color: #374151;
  white-space: nowrap;           /* prevents date wrapping */
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-table td:last-child {
  white-space: normal;           /* Fields Changed column can wrap */
  color: #6b7280;
  font-size: 0.82rem;
}

/* History modal */
.history-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 50;
  background: rgba(15, 24, 35, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
}

.history-modal {
  background: white;
  border-radius: 10px;
  box-shadow: 0 24px 80px rgba(10, 20, 32, 0.28);
  padding: 24px;
  width: min(560px, calc(100vw - 32px));
}

.history-modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 18px;
  gap: 12px;
}

.history-modal-title {
  font-size: 0.92rem;
  font-weight: 600;
  color: #172033;
}

.history-modal-subtitle {
  font-size: 0.8rem;
  color: var(--muted);
  margin-top: 2px;
}
```

### CSS column widths

The three-column table uses `table-layout: fixed` with these proportions:

```css
.history-table th:nth-child(1),
.history-table td:nth-child(1) { width: 38%; }

.history-table th:nth-child(2),
.history-table td:nth-child(2) { width: 28%; }

.history-table th:nth-child(3),
.history-table td:nth-child(3) { width: 34%; }
```

The same proportions apply to the modal table's Field / Was / Became columns (adapted as needed).

### Test updates

`TaskHistory.test.tsx` — update or add:
- Test that table wrapper has class `history-table-wrapper`.
- Test that header cells have correct column headers.
- Test that clicking a row calls `onEntryClick`.
- Remove any test expecting `TaskHistoryModal` to render inside `TaskHistory`
  (modal is now in `TaskBoard`).

`TaskHistoryModal.test.tsx` — update or add:
- Test that backdrop has class `history-modal-backdrop`.
- Test that modal header displays author + timestamp text.
- Test that Escape / backdrop click / close button all call `onClose`.
- Test that the Field/Was/Became table renders rows correctly.

`TaskBoard.test.tsx` — update or add:
- Test that clicking a history row renders `TaskHistoryModal`.
- Test that closing the modal removes it from the DOM.

## Complexity Tracking

No constitution violations. No Complexity Tracking required.
