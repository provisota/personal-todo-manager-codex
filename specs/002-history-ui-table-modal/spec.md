# Feature Specification: History UI — Styled Table and Change Detail Modal

**Feature Branch**: `002-history-ui-table-modal`  
**Created**: 2026-05-12  
**Status**: Draft  

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Styled History Table (Priority: P1)

A user opens the task history panel ("History: Task 1") and instead of a plain, unstyled text list, sees a clean, well-structured table with three columns — When, Changed By, and Fields Changed — that visually matches the rest of the application.

**Why this priority**: This is the baseline visual requirement. Without it the history feature looks broken. All interaction scenarios depend on a readable list being present first.

**Independent Test**: Open the history panel for any task and verify that a styled table with headers is rendered.

**Acceptance Scenarios**:

1. **Given** the history panel is open, **When** the user views it, **Then** a table with columns "When", "Changed By", and "Fields Changed" is displayed, with bold headers on a light blue-grey background.
2. **Given** the history table is visible, **When** the user inspects the layout, **Then** rows are separated by thin dividers, cells have comfortable padding, dates do not wrap, and the table fills most of the panel width without touching the edges.
3. **Given** the history panel is open, **When** the user inspects the block, **Then** the panel title ("History: Task 1") and the close button ("×") remain unchanged and visible above the table.

---

### User Story 2 - Change Detail Modal (Priority: P2)

A user clicks a row in the history table and a modal overlay appears in the center of the screen, showing a styled comparison table with columns Field, Was, and Became. The rest of the interface is dimmed but still visible behind the overlay.

**Why this priority**: This is the core interactive feature. Without it, the history table shows only a summary with no way to inspect the actual change values.

**Independent Test**: Click any history row and verify that a modal appears with the correct before/after data in a three-column table.

**Acceptance Scenarios**:

1. **Given** the history table is displayed and the user clicks a row, **When** the row is selected, **Then** a modal opens centered on screen with a semi-transparent backdrop dimming the rest of the interface.
2. **Given** the modal is open, **When** the user inspects it, **Then** it contains a three-column table (Field | Was | Became) listing every changed field with its previous and new value; cells are properly padded and text is readable.
3. **Given** the modal is open, **When** the user clicks the "×" button in the top-right corner, **Then** the modal closes and the history panel is visible again.
4. **Given** the modal is open, **When** the user clicks outside the modal (on the overlay), **Then** the modal closes.

---

### Edge Cases

- What happens when a history entry has only one changed field? The modal table should display a single data row.
- What happens when the "Was" or "Became" value is empty or null? The cell should render as blank, not show "null" or "undefined".
- What happens when the history list is empty? The table should still render with headers and an appropriate empty-state message.
- What happens when the user opens a second row while a modal is already open? The first modal closes and the new one opens.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The history panel MUST display a table with three columns: "When", "Changed By", and "Fields Changed".
- **FR-002**: The table header row MUST have a distinct light blue-grey background with bold column labels.
- **FR-003**: Table rows MUST be separated by thin horizontal dividers; cells MUST have comfortable internal padding.
- **FR-004**: The "When" column MUST display timestamps in a format that does not line-wrap (e.g., "5/11/2026, 6:58:33 PM").
- **FR-005**: The table MUST occupy most of the history panel width without touching the panel edges.
- **FR-005a**: The table body MUST have a fixed maximum height; when entries exceed it, the table body MUST scroll vertically while the header row remains fixed/visible.
- **FR-006**: The existing panel title ("History: [Task Name]") and its close button ("×") MUST remain unchanged and positioned above the table.
- **FR-007**: Clicking a row in the history table MUST open a modal dialog over the rest of the interface.
- **FR-008**: The modal MUST be centered on screen with a semi-transparent dark overlay behind it.
- **FR-009**: The modal MUST display a header line showing "Changes — [timestamp] by [author]" identifying the selected history entry.
- **FR-009a**: Below the header, the modal MUST contain a table with three columns: "Field", "Was", and "Became", listing all changed fields for the selected history entry.
- **FR-010**: The modal table MUST follow the same visual styling rules as the history table (light header, dividers, padding, bordered container).
- **FR-011**: The modal MUST have a "×" close button in its top-right corner that dismisses it.
- **FR-012**: Clicking outside the modal (on the overlay) MUST also dismiss it.
- **FR-012a**: Pressing the Escape key while the modal is open MUST also dismiss it.
- **FR-013**: The current inline/inline-text rendering of change details below the history list MUST be removed.

### Key Entities

- **HistoryEntry**: A single recorded change event — contains timestamp, author name, and a list of changed fields with before/after values.
- **ChangedField**: One field within a HistoryEntry — contains field name, previous value ("Was"), and new value ("Became").

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view the full history of a task in a structured table without any raw or unstyled text being visible in the history panel.
- **SC-002**: Users can open change details for any history entry in under one click (single row click opens modal).
- **SC-003**: Users can close the detail modal in one action (single click on "×" or on the overlay).
- **SC-004**: The history panel and modal are visually consistent with the rest of the application (matching colour palette, typography, border radius, and spacing conventions).
- **SC-005**: No change-detail content is rendered inline inside the history panel as plain text.

## Clarifications

### Session 2026-05-12

- Q: When the history table has many entries (50+), how should it handle overflow? → A: The table has a fixed maximum height and scrolls vertically; all entries remain accessible via scroll.
- Q: Should the Escape key close the change detail modal? → A: Yes — pressing Escape closes the modal (standard keyboard accessibility behaviour).
- Q: Does the modal have a title/header showing which history entry is open? → A: Yes — the modal header shows "Changes — [timestamp] by [author]" for context.
- Q: Should Tailwind CSS be installed, or should existing Tailwind class names be replaced with custom CSS classes in global.css? → A: Replace Tailwind class names with CSS classes in global.css — no new dependencies; consistent with all other components in the project.

## Assumptions

- The existing history API already returns field-level change data (field name, was value, became value) per history entry; no backend changes are needed.
- The current history component already fetches and stores history entries; only the rendering layer is being changed.
- The application uses a component-based frontend framework (React/TypeScript) with custom CSS classes in `global.css` — Tailwind CSS is not installed and will not be added. All styling changes must use the existing `global.css` pattern.
- The visual design tokens (colours, border radius, shadows, spacing) already used in the application will be reused — no new design tokens need to be introduced.
- Mobile/responsive layout is not in scope for this iteration; the table and modal are designed for desktop viewports.
