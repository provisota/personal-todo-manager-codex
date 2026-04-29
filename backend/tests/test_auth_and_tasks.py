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

