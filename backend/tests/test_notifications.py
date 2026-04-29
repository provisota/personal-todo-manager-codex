from datetime import date, timedelta

from httpx import AsyncClient
from app.db.session import get_session
from app.services.notifications import NotificationService
from tests.conftest import login


async def test_notification_service_returns_overdue_and_due_soon(client: AsyncClient):
    user = await login(client)
    list_response = await client.post("/api/lists", json={"name": "Work"})
    list_id = list_response.json()["id"]

    await client.post(
        "/api/tasks",
        json={
            "list_id": list_id,
            "title": "Overdue task",
            "priority": "high",
            "due_date": (date.today() - timedelta(days=1)).isoformat(),
        },
    )
    await client.post(
        "/api/tasks",
        json={
            "list_id": list_id,
            "title": "Due soon task",
            "priority": "medium",
            "due_date": (date.today() + timedelta(days=2)).isoformat(),
        },
    )
    await client.post(
        "/api/tasks",
        json={
            "list_id": list_id,
            "title": "Done task",
            "status": "done",
            "priority": "medium",
            "due_date": (date.today() - timedelta(days=1)).isoformat(),
        },
    )

    app = client.app
    override = app.dependency_overrides[get_session]
    async for session in override():
        notifications = await NotificationService().get_notifications(session, user["id"])
        titles = {item.title for item in notifications}
        assert titles == {"Overdue task", "Due soon task"}
        assert {item.type for item in notifications} == {"overdue", "due_soon"}
