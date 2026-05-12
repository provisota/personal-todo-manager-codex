# Feature Specification: Task Change History

**Feature Branch**: `001-task-history`  
**Created**: 2026-05-11  
**Status**: Draft  
**Input**: User description: "adding task history - Each task should store a history of its changes. Accordingly, a button for viewing this history should be added to the UI (between the task edit and delete buttons). Clicking this button should open a list of the change history (with a brief list of the fields that were changed). Clicking on each line in the history should open a modal window with a more detailed description of the changed fields, in the WAS->BECAME format."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Task Change History List (Priority: P1)

A user wants to understand what changes have been made to a task over time. They click the history button on a task row (positioned between the edit and delete buttons) and see a list of all past changes, each showing when it occurred and which fields were affected.

**Why this priority**: This is the entry point for the entire feature. Without the history list, no other part of the feature is accessible. It also provides the most value on its own — the user immediately knows what changed and when.

**Independent Test**: Can be fully tested by clicking the history button on a task that has been edited at least once, and verifying that a list of change entries appears with timestamps, author name, and field summaries.

**Acceptance Scenarios**:

1. **Given** a task that has been edited at least once, **When** the user clicks the history button, **Then** a panel or inline list opens showing all change entries in reverse chronological order (most recent first).
2. **Given** the history list is open, **When** the user reviews each entry, **Then** each entry displays the date/time of the change, the name of the user who made it, and a brief summary of which fields were modified (e.g., "Status, Priority changed").
3. **Given** a newly created task with no edits, **When** the user clicks the history button, **Then** the list displays a message indicating there are no recorded changes.

---

### User Story 2 - View Detailed Field Diff in Modal (Priority: P2)

A user wants to see exactly what value a field had before and after a specific change. They click a history entry in the list and a modal opens showing each changed field with its old value (WAS) and new value (BECAME) side by side.

**Why this priority**: Provides the core investigative value of the feature. The list (P1) tells the user *that* something changed; the detail modal tells them *what* it changed from and to.

**Independent Test**: Can be fully tested by clicking any entry in the history list and verifying that the resulting modal shows WAS and BECAME values for each field that was modified in that change.

**Acceptance Scenarios**:

1. **Given** the history list is open, **When** the user clicks any history entry, **Then** a modal opens showing a table of modified fields with their previous (WAS) and new (BECAME) values (no timestamp header in the modal — the timestamp is already visible in the history list row).
2. **Given** the detail modal is open, **When** multiple fields were changed in that event, **Then** all changed fields are displayed, each on its own row with clearly labeled WAS and BECAME columns.
3. **Given** the detail modal is open, **When** the user closes it (via the X button, clicking outside the modal, or pressing Escape), **Then** the modal closes and the history list panel remains visible.

---

### User Story 3 - History Captured Automatically on Task Edit (Priority: P3)

Every time a user modifies and saves a task, the system automatically records what changed. No additional action is required from the user — the history grows silently in the background.

**Why this priority**: This is the prerequisite for P1 and P2, but is classified P3 here because it has no direct UI and its value is only visible through the history list. From a testing standpoint it can be validated through the list view.

**Independent Test**: Can be fully tested by editing a task field, saving it, then opening the history list and confirming a new entry appears reflecting the change.

**Acceptance Scenarios**:

1. **Given** a task with existing history, **When** the user edits one or more fields and saves, **Then** a new history entry appears at the top of the history list.
2. **Given** a task edit that touches multiple fields simultaneously, **When** the user saves, **Then** all changed fields are captured in a single history entry (not separate entries per field).
3. **Given** a task where the user opens the edit form but makes no changes and saves, **When** the history list is opened, **Then** no new history entry is added.

---

### Edge Cases

- What happens when a task has no history yet (newly created)? The history list displays an empty-state message, not an error.
- How does the system handle a task being deleted? All history records for that task are permanently deleted along with the task (cascade delete); no orphaned records are retained.
- What if the history list grows very large? All history entries are loaded and displayed at once with scrolling; no pagination, truncation, or auto-purging is applied.
- Only one history panel may be visible at a time; opening a panel for task B automatically closes any currently open panel for another task.
- What if a field value is empty/null before or after the change? The WAS or BECAME value is displayed as a blank or as a clear "empty" indicator.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST automatically record a change entry each time a task's fields are updated and saved.
- **FR-002**: Each change entry MUST capture the exact date and time the change occurred.
- **FR-003**: Each change entry MUST record which fields were modified, along with their previous (WAS) and new (BECAME) values.
- **FR-004**: When multiple fields are changed in a single save operation, the system MUST group them into a single change entry.
- **FR-005**: No history entry MUST be created when a task is opened and saved without any field modifications.
- **FR-006**: The task row in the UI MUST include a history button positioned between the existing edit and delete buttons.
- **FR-007**: The history button acts as a toggle: clicking it once opens the inline history panel for that task; clicking it again closes the panel.
- **FR-008**: The history list MUST be presented in reverse chronological order (most recent change first).
- **FR-009**: The history list MUST be rendered as a styled table with three columns — When (timestamp), Changed By (author name), and Fields Changed. The Fields Changed cell displays the human-readable field labels that were modified, comma-separated (e.g., "Description, Priority"). Each row represents one change entry. Visual styling MUST conform to the `## Visual Design > History Inline Panel` section.
- **FR-010**: Clicking a history list entry MUST open a modal window displaying the full WAS → BECAME detail for every field changed in that entry.
- **FR-011**: The detail modal MUST present each changed field as a row in a styled table with three clearly labeled columns: Field, Was, and Became. Field names MUST use human-readable English labels (Title, Description, Status, Priority, Due Date). Was and Became cells MUST display the full value; if the value is long, the cell has a fixed max-height with vertical scroll (overflow-y: scroll inside the cell) so the modal size remains predictable. Visual styling MUST conform to the `## Visual Design > Detail Modal` section.
- **FR-014**: The detail modal MUST be dismissible via the close (X) button, clicking the backdrop outside the modal, or pressing the Escape key. Dismissing the detail modal returns the user to the history list panel.
- **FR-012**: Only the owner of a task MAY view that task's change history; unauthorized access returns the same result as a non-existent resource.
- **FR-013**: Task creation MUST NOT generate a history entry; only subsequent modifications are tracked.

### Key Entities

- **Task Change Record**: Represents a single modification event on a task. Linked to a specific task; includes the timestamp of the change, the identity of the user who made it, and one or more field changes.
- **Field Change**: Represents the before/after state of one field within a change record. Includes the field name (human-readable), the previous value (WAS), and the new value (BECAME).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can open the history list for any task and see all past changes within 2 seconds of clicking the history button.
- **SC-002**: Every task save that modifies at least one field results in a corresponding history entry visible in the list within 1 second of the save completing.
- **SC-003**: 100% of editable task fields (title, description, status, priority, due date) are captured in the change record when modified.
- **SC-004**: Users can distinguish the exact before and after state of every changed field without needing any additional context or documentation.
- **SC-005**: No history entry is lost or duplicated; the history list is consistent and complete across all sessions.

## Clarifications

### Session 2026-05-12

- Visual design: User provided reference screenshots; detailed styling requirements for both the history list table and the detail modal have been captured in the `## Visual Design` section. Key points: table has rounded corners, light-gray border, blue-gray header row, bold headers, comfortable padding; modal has dark semi-transparent backdrop, centered white card, soft shadow, X close button top-right, same styled table inside.
- Q: Should the detail modal include a title/timestamp header, or only the Field/Was/Became table? → A: Only the bare Field/Was/Became table with an X close button; no title or timestamp header in the modal (timestamp is already visible in the history list row before opening the modal).
- Q: How is the inline history panel opened and closed? → A: The history button is a toggle — first click opens the panel, second click closes it; the ^ indicator in the panel header is decorative/duplicate.
- Q: If a history panel is already open for task A and the user clicks the history button for task B, what happens? → A: Task A's panel closes automatically; only task B's panel opens (only one panel visible at a time).
- Q: How should field names be displayed in the history list ("Fields Changed" column) and the detail modal ("Field" column)? → A: Human-readable English labels — Title, Description, Status, Priority, Due Date.
- Q: How should long values (e.g., Description) be displayed in the Was/Became cells of the detail modal? → A: Full text preserved; each cell has a fixed max-height with vertical scroll inside the cell (overflow-y: scroll), so the modal dimensions stay predictable.

### Session 2026-05-11

- Q: Should each history entry display who made the change (author name)? → A: Yes — store and display the author's name in both the history list and the detail modal.
- Q: When a task is deleted, what happens to its history records? → A: Cascade delete — all history records are permanently removed along with the task.
- Q: How should the history list load when a task has many changes? → A: Load all records at once with scrolling; no pagination or truncation.
- Q: How should history entries be displayed in the list? → A: As a table (not a bullet list) with columns: When, Changed By, Fields Changed. The history panel itself remains an inline panel, not a modal.
- Q: How is the detail modal dismissed? → A: X button, clicking the backdrop outside the modal, or pressing Escape — all three methods must work.

## Visual Design

Visual requirements derived from reference screenshots provided by the user. Implementations MUST match this styling to pass acceptance review.

### History Inline Panel

The history panel is an inline block anchored below the task row, spanning the full content width.

**Panel container:**
- Header: "History [Task Title]" label on the left, a ^ collapse indicator on the right
- White or near-white background
- Subtle border or card-style separation from the task list

**History table (inside the panel):**
- Occupies nearly the full width of the panel with horizontal padding so it does not touch the edges
- Thin light-gray border around the table
- Rounded corners on the table
- **Header row**: light blue-gray background; column labels bold
- **Data rows**: white background; separated by thin horizontal dividers
- **Cell padding**: comfortable (not tight); text must not feel cramped
- **Column sizing**: `When` column wide enough for a full timestamp without wrapping; `Changed By` visually centered in the table; `Fields Changed` allocated remaining space and must be readable without compression

### Detail Modal

**Backdrop**: semi-transparent dark overlay covering the full viewport; application content remains visible but dimmed behind it.

**Modal container:**
- Centered horizontally and vertically on screen
- White or near-white background
- Rounded corners
- Soft drop shadow
- Comfortable internal padding on all sides
- Visual style consistent with the rest of the application (clean, modern)

**Close button:**
- X icon in the top-right corner of the modal
- Small, unobtrusive; no surrounding text or label
- Closes the modal on click

**Modal diff table:**
- Columns: Field | Was | Became
- Takes most of the modal width (with internal padding, not edge-to-edge)
- Thin light-gray border; slightly rounded corners
- **Header row**: light blue-gray or light-gray background; column labels bold
- **Data rows**: white background; separated by thin horizontal and vertical dividers
- Text: dark, high-contrast, readable
- Cell padding: normal; values must not run together
- Long values in Was/Became cells: full text preserved; cell has a fixed max-height with `overflow-y: scroll` inside the cell so the modal size stays predictable

## Assumptions

- Only the task owner can view the history (consistent with the existing authorization model — cross-account access is treated as non-existent).
- All user-editable task fields are tracked: title, description, status, priority, and due date.
- Task creation is not recorded as a history entry; tracking begins from the first edit after creation.
- History entries are retained indefinitely; there is no automatic expiry or purging.
- The history UI is presented as an inline panel anchored to the task row (not a modal and not a separate full-page navigation). The list of change entries is formatted as a table with columns: When, Changed By, Fields Changed. The history button is a toggle: one click opens the panel, a second click closes it. The panel header displays the task name (format: "History [Task Title]") and a ^ collapse indicator.
- The detail modal is a standard blocking overlay (with darkened backdrop) dismissible via X button, backdrop click, or Escape key. It displays changed fields as a table with columns: Field, Was, Became. The modal has no title or timestamp header — the modal contains only the table and the X close button.
- The history feature is scoped to individual tasks; there is no cross-task or list-level change log in this iteration.
