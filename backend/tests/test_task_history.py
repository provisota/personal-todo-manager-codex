from httpx import AsyncClient

from tests.conftest import login


async def _setup(client: AsyncClient) -> tuple[str, str]:
    """Login, create list, create task. Returns (list_id, task_id)."""
    await login(client)
    list_r = await client.post("/api/lists", json={"name": "History Test"})
    assert list_r.status_code == 201, list_r.text
    list_id = list_r.json()["id"]
    task_r = await client.post(
        "/api/tasks",
        json={
            "list_id": list_id,
            "title": "Original Title",
            "description": "Original description",
            "status": "todo",
            "priority": "low",
            "due_date": None,
        },
    )
    assert task_r.status_code == 201, task_r.text
    return list_id, task_r.json()["id"]


# ---------------------------------------------------------------------------
# T007 — History Capture (US3)
# ---------------------------------------------------------------------------


async def test_history_single_field_update_creates_one_record(client: AsyncClient):
    _, task_id = await _setup(client)

    patch = await client.patch(f"/api/tasks/{task_id}", json={"title": "Updated Title"})
    assert patch.status_code == 200, patch.text

    r = await client.get(f"/api/tasks/{task_id}/history")
    assert r.status_code == 200, r.text
    history = r.json()
    assert len(history) == 1
    assert len(history[0]["fields"]) == 1
    field = history[0]["fields"][0]
    assert field["field_name"] == "Title"
    assert field["old_value"] == "Original Title"
    assert field["new_value"] == "Updated Title"


async def test_history_multi_field_update_creates_one_record_multiple_field_changes(
    client: AsyncClient,
):
    _, task_id = await _setup(client)

    patch = await client.patch(
        f"/api/tasks/{task_id}",
        json={"title": "New Title", "priority": "high", "description": "New desc"},
    )
    assert patch.status_code == 200, patch.text

    r = await client.get(f"/api/tasks/{task_id}/history")
    assert r.status_code == 200, r.text
    history = r.json()
    assert len(history) == 1
    field_names = {f["field_name"] for f in history[0]["fields"]}
    assert field_names == {"Title", "Priority", "Description"}


async def test_history_no_op_update_creates_no_record(client: AsyncClient):
    _, task_id = await _setup(client)

    patch = await client.patch(f"/api/tasks/{task_id}", json={"title": "Original Title"})
    assert patch.status_code == 200, patch.text

    r = await client.get(f"/api/tasks/{task_id}/history")
    assert r.status_code == 200, r.text
    assert r.json() == []


async def test_history_status_patch_creates_record(client: AsyncClient):
    _, task_id = await _setup(client)

    patch = await client.patch(f"/api/tasks/{task_id}/status", json={"status": "in_progress"})
    assert patch.status_code == 200, patch.text

    r = await client.get(f"/api/tasks/{task_id}/history")
    assert r.status_code == 200, r.text
    history = r.json()
    assert len(history) == 1
    field = history[0]["fields"][0]
    assert field["field_name"] == "Status"
    assert field["old_value"] == "To Do"
    assert field["new_value"] == "In Progress"


async def test_history_deleted_with_task_cascade(client: AsyncClient):
    _, task_id = await _setup(client)

    await client.patch(f"/api/tasks/{task_id}", json={"title": "Will Be Deleted"})
    r = await client.get(f"/api/tasks/{task_id}/history")
    assert len(r.json()) == 1

    delete = await client.delete(f"/api/tasks/{task_id}")
    assert delete.status_code == 200, delete.text

    gone = await client.get(f"/api/tasks/{task_id}/history")
    assert gone.status_code == 404


# ---------------------------------------------------------------------------
# T011 — GET /api/tasks/{task_id}/history endpoint (US1)
# ---------------------------------------------------------------------------


async def test_history_endpoint_returns_list_with_metadata(client: AsyncClient):
    await login(client)
    list_r = await client.post("/api/lists", json={"name": "Meta Test"})
    list_id = list_r.json()["id"]
    task_r = await client.post(
        "/api/tasks",
        json={"list_id": list_id, "title": "Task A", "status": "todo", "priority": "medium"},
    )
    task_id = task_r.json()["id"]

    await client.patch(f"/api/tasks/{task_id}", json={"title": "Task A Updated"})

    r = await client.get(f"/api/tasks/{task_id}/history")
    assert r.status_code == 200
    entry = r.json()[0]
    assert "id" in entry
    assert "task_id" in entry
    assert "changed_by_name" in entry
    assert "created_at" in entry
    assert "fields" in entry
    assert entry["changed_by_name"] == "User user-1"


async def test_history_endpoint_empty_for_unedited_task(client: AsyncClient):
    _, task_id = await _setup(client)

    r = await client.get(f"/api/tasks/{task_id}/history")
    assert r.status_code == 200
    assert r.json() == []


async def test_history_endpoint_returns_404_for_wrong_user(client: AsyncClient):
    _, task_id = await _setup(client)

    await client.post("/auth/logout")
    await login(client, "user-2", "u2@example.com")

    r = await client.get(f"/api/tasks/{task_id}/history")
    assert r.status_code == 404


async def test_history_endpoint_returns_401_unauthenticated(client: AsyncClient):
    _, task_id = await _setup(client)

    await client.post("/auth/logout")

    r = await client.get(f"/api/tasks/{task_id}/history")
    assert r.status_code == 401


async def test_history_endpoint_reverse_chronological_order(client: AsyncClient):
    _, task_id = await _setup(client)

    await client.patch(f"/api/tasks/{task_id}", json={"title": "Update 1"})
    await client.patch(f"/api/tasks/{task_id}", json={"title": "Update 2"})
    await client.patch(f"/api/tasks/{task_id}", json={"title": "Update 3"})

    r = await client.get(f"/api/tasks/{task_id}/history")
    assert r.status_code == 200
    entries = r.json()
    assert len(entries) == 3
    timestamps = [e["created_at"] for e in entries]
    assert timestamps == sorted(timestamps, reverse=True)
