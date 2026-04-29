from datetime import date, timedelta

from httpx import AsyncClient

from tests.conftest import login


async def test_sso_login_success_path_uses_test_provider(client: AsyncClient):
    user = await login(client)
    assert user["email"] == "u1@example.com"

    response = await client.get("/auth/me")
    assert response.status_code == 200
    assert response.json()["id"] == user["id"]


async def test_user_can_create_list_and_task(client: AsyncClient):
    await login(client)
    list_response = await client.post("/api/lists", json={"name": "Work"})
    assert list_response.status_code == 201, list_response.text
    list_id = list_response.json()["id"]

    task_response = await client.post(
        "/api/tasks",
        json={
            "list_id": list_id,
            "title": "Write spec implementation",
            "description": "Backend acceptance test",
            "status": "todo",
            "priority": "high",
            "due_date": "2026-05-01",
        },
    )
    assert task_response.status_code == 201, task_response.text
    task = task_response.json()
    assert task["title"] == "Write spec implementation"
    assert task["priority"] == "high"

    tasks = await client.get("/api/tasks", params={"list_id": list_id, "search": "Backend"})
    assert tasks.status_code == 200
    assert len(tasks.json()) == 1


async def test_user_cannot_access_another_users_list_or_task(client: AsyncClient):
    await login(client, "user-1", "u1@example.com")
    list_response = await client.post("/api/lists", json={"name": "Private"})
    list_id = list_response.json()["id"]
    task_response = await client.post("/api/tasks", json={"list_id": list_id, "title": "Secret"})
    task_id = task_response.json()["id"]

    await client.post("/auth/logout")
    await login(client, "user-2", "u2@example.com")

    assert (await client.get("/api/tasks", params={"list_id": list_id})).status_code == 404
    assert (await client.patch(f"/api/tasks/{task_id}/status", json={"status": "done"})).status_code == 404
    assert (await client.delete(f"/api/lists/{list_id}")).status_code == 404


async def test_task_filters_and_completed_at_transitions(client: AsyncClient):
    await login(client)
    list_response = await client.post("/api/lists", json={"name": "Filters"})
    list_id = list_response.json()["id"]

    yesterday = (date.today() - timedelta(days=1)).isoformat()
    today = date.today().isoformat()
    next_week = (date.today() + timedelta(days=6)).isoformat()

    overdue_response = await client.post(
        "/api/tasks",
        json={
            "list_id": list_id,
            "title": "Ship overdue report",
            "status": "todo",
            "priority": "high",
            "due_date": yesterday,
        },
    )
    assert overdue_response.status_code == 201, overdue_response.text
    overdue_id = overdue_response.json()["id"]

    await client.post(
        "/api/tasks",
        json={
            "list_id": list_id,
            "title": "Today planning",
            "status": "in_progress",
            "priority": "medium",
            "due_date": today,
        },
    )
    await client.post(
        "/api/tasks",
        json={
            "list_id": list_id,
            "title": "Next week review",
            "status": "todo",
            "priority": "low",
            "due_date": next_week,
        },
    )

    overdue = await client.get("/api/tasks", params={"list_id": list_id, "due": "overdue"})
    assert [task["title"] for task in overdue.json()] == ["Ship overdue report"]

    in_progress = await client.get("/api/tasks", params={"list_id": list_id, "status": "in_progress"})
    assert [task["title"] for task in in_progress.json()] == ["Today planning"]

    low_priority = await client.get("/api/tasks", params={"list_id": list_id, "priority": "low"})
    assert [task["title"] for task in low_priority.json()] == ["Next week review"]

    completed = await client.patch(f"/api/tasks/{overdue_id}/status", json={"status": "done"})
    assert completed.status_code == 200, completed.text
    assert completed.json()["completed_at"] is not None

    reopened = await client.patch(f"/api/tasks/{overdue_id}/status", json={"status": "todo"})
    assert reopened.status_code == 200, reopened.text
    assert reopened.json()["completed_at"] is None


async def test_deleting_list_cascades_tasks(client: AsyncClient):
    await login(client)
    list_response = await client.post("/api/lists", json={"name": "Delete me"})
    list_id = list_response.json()["id"]
    await client.post("/api/tasks", json={"list_id": list_id, "title": "Cascaded task"})

    delete_response = await client.delete(f"/api/lists/{list_id}")
    assert delete_response.status_code == 200, delete_response.text
    assert delete_response.json()["deleted_tasks"] == 1
    assert (await client.get("/api/tasks", params={"list_id": list_id})).status_code == 404
