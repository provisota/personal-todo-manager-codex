# API Contract: Task Change History

## Endpoint

### GET `/api/tasks/{task_id}/history`

Returns all change records for a task, ordered from most recent to oldest. Each record includes the full list of field changes (WAS → BECAME), allowing the frontend to render both the list view and the detail modal from a single response.

---

**Authorization**: Requires a valid `ptm_session` cookie. The task must be owned by the authenticated user; otherwise returns `404`.

**Path parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | UUID string | ID of the task to retrieve history for |

---

**Success response**: `200 OK`

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "task_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    "changed_by_name": "Demo User",
    "created_at": "2026-05-11T14:32:00Z",
    "fields": [
      {
        "field_name": "Status",
        "old_value": "To Do",
        "new_value": "In Progress"
      },
      {
        "field_name": "Priority",
        "old_value": "Low",
        "new_value": "High"
      }
    ]
  },
  {
    "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "task_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    "changed_by_name": "Demo User",
    "created_at": "2026-05-10T09:15:00Z",
    "fields": [
      {
        "field_name": "Title",
        "old_value": "Buy groceries",
        "new_value": "Buy groceries and cook dinner"
      }
    ]
  }
]
```

**Empty history** (task exists, never edited): `200 OK` with `[]`

---

**Error responses**:

| Status | Condition |
|--------|-----------|
| `401 Unauthorized` | No valid session cookie |
| `404 Not Found` | Task does not exist or belongs to a different user |

---

## Pydantic Schemas

### `FieldChangeRead`

```python
class FieldChangeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    field_name: str
    old_value: str | None
    new_value: str | None
```

### `TaskHistoryRead`

```python
class TaskHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
    changed_by_name: str
    created_at: datetime
    fields: list[FieldChangeRead]
```

Note: `changed_by_name` is resolved by joining `users.display_name` at query time — it is not stored on the history record itself.

---

## Frontend TypeScript Types

```typescript
export interface FieldChange {
  field_name: string;
  old_value: string | null;
  new_value: string | null;
}

export interface TaskHistoryEntry {
  id: string;
  task_id: string;
  changed_by_name: string;
  created_at: string;
  fields: FieldChange[];
}
```

---

## API Client Extension (`api/client.ts`)

```typescript
taskHistory: (taskId: string) =>
  request<TaskHistoryEntry[]>(`/api/tasks/${taskId}/history`),
```
