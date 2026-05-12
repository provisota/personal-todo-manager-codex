# Research: History UI — Styled Table and Change Detail Modal

**Branch**: `002-history-ui-table-modal` | **Date**: 2026-05-12

## Decision 1: Styling approach

**Decision**: Use `global.css` custom CSS classes (no new dependencies).

**Rationale**: Tailwind CSS is not installed in the project. `package.json` lists no `tailwindcss`
dependency and there is no `postcss.config`. Every other component in the project (`TaskBoard`,
`TaskForm`, `NotificationPanel`, `ListSidebar`) uses custom CSS classes from `global.css`. The
existing history components (`TaskHistory`, `TaskHistoryModal`) were written with Tailwind utility
classes that have no effect at runtime — confirming the mismatch.

**Alternatives considered**:
- Install Tailwind CSS — rejected; adds a build-time dependency and requires `postcss` config;
  not justified for a small number of components (YAGNI principle).
- Inline styles — rejected; not maintainable, inconsistent with project conventions.

---

## Decision 2: Modal positioning strategy

**Decision**: Lift `TaskHistoryModal` rendering from `TaskHistory` to `TaskBoard`.

**Rationale**: `.history-panel` in `global.css` has `overflow: hidden`. While `overflow: hidden`
alone does not clip `position: fixed` elements in modern browsers, keeping the modal inside an
ancestor with constrained layout (panel inside task board) risks future clipping if CSS changes.
More importantly, the existing code placed `TaskHistoryModal` inside `TaskHistory` which is inside
`.history-panel` — this means the modal was a sibling of the table, rendering inline without
`position: fixed` applying (because Tailwind's `fixed` class had no effect). Moving the modal
to `TaskBoard` (outside `.history-panel`) correctly places the fixed overlay at document level.

**Alternatives considered**:
- React Portal to `document.body` — valid but adds boilerplate; lifting to `TaskBoard` is simpler
  and consistent with how `TaskForm` is handled (it is also rendered at `TaskBoard` level).

---

## Decision 3: Scrollable table body technique

**Decision**: Use `display: block` on `<tbody>` with `overflow-y: auto` and `max-height`.
Apply `display: table; width: 100%; table-layout: fixed` to both the header `<tr>` and body
`<tr>` elements to keep columns aligned.

**Rationale**: Pure CSS approach; no JavaScript needed. Well-supported in all modern browsers.
The header (`<thead>`) remains visually fixed while body rows scroll.

**Alternatives considered**:
- JavaScript virtual scroll — over-engineered for this feature; history lists are short.
- CSS grid for the table layout — would require changing semantic HTML structure.

---

## Decision 4: Modal header format

**Decision**: Modal header shows author name on the first line and formatted timestamp on the
second line (two lines, not a single "Changes — X by Y" sentence).

**Rationale**: The existing `TaskHistoryModal` already renders author and timestamp as separate
elements. The spec's FR-009 ("Changes — [timestamp] by [author]") describes the conceptual content,
not the exact visual format. Two lines are more readable and match the mockup layout (Image 4).

---

## No NEEDS CLARIFICATION markers remain. All decisions resolved.
