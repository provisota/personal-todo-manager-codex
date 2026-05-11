# Data Model: Task Change History

## New Entities

### TaskChangeRecord (`task_history`)

Represents a single modification event on a task. One record is created each time a task is saved with at least one changed field.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID (string) | PK, default `new_uuid()` | |
| `task_id` | UUID (string) | FK → `tasks.id` ON DELETE CASCADE, indexed | Identifies the task that was changed |
| `user_id` | UUID (string) | FK → `users.id` ON DELETE CASCADE, indexed | Who made the change |
| `created_at` | datetime (UTC) | NOT NULL, default `utc_now()` | Timestamp of the change; from TimestampMixin |
| `updated_at` | datetime (UTC) | NOT NULL, default `utc_now()` | From TimestampMixin (will always equal `created_at` — records are immutable) |

**Relationships**:
- `task` → `Task` (many-to-one)
- `user` → `User` (many-to-one; for resolving `display_name` at read time)
- `fields` → `FieldChange[]` (one-to-many, eager-loaded on read)

**Indexes**:
- `(task_id, created_at DESC)` — supports history list queries in reverse chronological order

---

### FieldChange (`task_history_fields`)

Represents the before/after state of a single field within one `TaskChangeRecord`.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID (string) | PK, default `new_uuid()` | |
| `history_id` | UUID (string) | FK → `task_history.id` ON DELETE CASCADE, indexed | Parent change record |
| `field_name` | VARCHAR(50) | NOT NULL | Human-readable name: `"Title"`, `"Description"`, `"Status"`, `"Priority"`, `"Due Date"` |
| `old_value` | TEXT \| NULL | | Previous value serialized as string; NULL means field was empty/unset |
| `new_value` | TEXT \| NULL | | New value serialized as string; NULL means field was cleared |

**Relationships**:
- `history` → `TaskChangeRecord` (many-to-one)

---

## Modified Entities

### Task (no schema changes)

No new columns on the `tasks` table. History records are stored in a separate table. The cascade delete is handled by the FK on `task_history.task_id`.

---

## Field Serialization Convention

All field values are stored as human-readable strings:

| Task field | Serialized form                                                                                    |
|------------|----------------------------------------------------------------------------------------------------|
| `title` | Plain string value                                                                                 |
| `description` | Plain string value (empty string → should be stored as `""`) |
| `status` | Enum label: `"To Do"`, `"In Progress"`, `"Done"`                                                   |
| `priority` | Enum label: `"Low"`, `"Medium"`, `"High"`                                                          |
| `due_date` | ISO 8601 date string: `"2026-05-11"`, or `None` if cleared                                         |

---

## State Transition: History Capture in `update_task()`

```
1. Load existing task (verify ownership)
2. Snapshot current field values
3. Apply payload mutations (existing logic)
4. Compare snapshots — collect changed fields
5. If at least one field changed:
   a. Create TaskChangeRecord (task_id, user_id, auto timestamp)
   b. Create FieldChange row for each changed field (field_name, old_value, new_value)
   c. session.add() both within the same transaction
6. Commit (task update + history records atomically)
```

Note: `update_task_status()` (called by the status dropdown) also modifies task fields and MUST trigger history recording.

---

## Alembic Migration Requirements

- New table: `task_history` with columns and FK to `tasks.id` CASCADE and `users.id` CASCADE
- New table: `task_history_fields` with FK to `task_history.id` CASCADE
- Index on `task_history(task_id, created_at)`
- New model `TaskChangeRecord` must be imported in `backend/app/db/base.py` for autogenerate to detect it
