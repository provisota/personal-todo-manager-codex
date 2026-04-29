from datetime import date, timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import select

from app.db.session import get_session
from app.models.notification_ack import NotificationAck
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


async def test_websocket_notifications_initial_batch_ack_and_invalid_message(app: FastAPI):
    with TestClient(app) as client:
        login_response = client.post(
            "/auth/test-login",
            json={
                "provider": "github",
                "provider_user_id": "ws-user",
                "email": "ws@example.com",
                "display_name": "WS User",
            },
        )
        assert login_response.status_code == 200, login_response.text
        user = login_response.json()

        list_response = client.post("/api/lists", json={"name": "WebSocket"})
        assert list_response.status_code == 201, list_response.text
        list_id = list_response.json()["id"]

        task_response = client.post(
            "/api/tasks",
            json={
                "list_id": list_id,
                "title": "WebSocket overdue task",
                "priority": "high",
                "due_date": (date.today() - timedelta(days=1)).isoformat(),
            },
        )
        assert task_response.status_code == 201, task_response.text
        task_id = task_response.json()["id"]

        with client.websocket_connect("/ws/notifications") as websocket:
            initial = websocket.receive_json()
            assert initial["type"] == "notification_batch"
            notifications = initial["payload"]["notifications"]
            assert len(notifications) == 1
            assert notifications[0]["task_id"] == task_id
            assert notifications[0]["list_id"] == list_id
            assert notifications[0]["type"] == "overdue"

            websocket.send_json(
                {
                    "type": "subscribe",
                    "payload": {
                        "enabled_types": ["overdue"],
                        "interval_seconds": 30,
                        "include_acknowledged": False,
                    },
                }
            )
            websocket.send_json(
                {
                    "type": "ack",
                    "payload": {"notification_id": notifications[0]["id"]},
                }
            )
            ack = websocket.receive_json()
            assert ack == {
                "type": "ack_ok",
                "payload": {"notification_id": notifications[0]["id"]},
            }

            websocket.send_json({"type": "unknown", "payload": {}})
            error = websocket.receive_json()
            assert error["type"] == "error"
            assert error["payload"]["code"] == "invalid_message"

    override = app.dependency_overrides[get_session]
    async for session in override():
        result = await session.execute(
            select(NotificationAck).where(
                NotificationAck.user_id == user["id"],
                NotificationAck.task_id == task_id,
                NotificationAck.notification_type == "overdue",
            )
        )
        assert result.scalar_one_or_none() is not None
