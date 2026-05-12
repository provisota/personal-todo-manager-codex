# Data Model: History UI — Styled Table and Change Detail Modal

**Branch**: `002-history-ui-table-modal` | **Date**: 2026-05-12

## Summary

This feature is a pure UI restyling task. No new data types, API endpoints, or data shapes are
introduced. The existing domain types in `frontend/src/types/domain.ts` are sufficient.

## Existing types used (unchanged)

### `TaskHistoryEntry`

Represents a single recorded change event for a task.

| Field | Type | Notes |
|-------|------|-------|
| `id` | `string` | Unique entry identifier |
| `task_id` | `string` | Reference to the parent task |
| `changed_by_name` | `string` | Display name of the user who made the change |
| `created_at` | `string` | ISO 8601 timestamp of the change |
| `fields` | `FieldChange[]` | List of individual field changes |

### `FieldChange`

Represents a single field within a `TaskHistoryEntry`.

| Field | Type | Notes |
|-------|------|-------|
| `field_name` | `string` | Human-readable field name (e.g., "Status", "Priority") |
| `old_value` | `string \| null` | Previous value; `null` renders as "—" in the UI |
| `new_value` | `string \| null` | New value; `null` renders as "—" in the UI |

## Component state changes

The only state change is in `TaskBoard.tsx`:

| New state | Type | Purpose |
|-----------|------|---------|
| `selectedHistoryEntry` | `TaskHistoryEntry \| null` | Tracks which history entry's modal is open; `null` = modal closed |

`TaskHistory.tsx` loses its internal `selectedEntry` state (lifted to `TaskBoard`).

## No new backend types, API contracts, or migrations needed.
