from datetime import date, timedelta
import base64
import json

from fastapi import HTTPException
from httpx import AsyncClient

from app.api.auth import exchange_google_code
from app.core.config import Settings, get_settings
from app.core.security import parse_oauth_state
from app.schemas.auth import ProviderProfile
from tests.conftest import login


async def test_sso_login_success_path_uses_test_provider(client: AsyncClient):
    user = await login(client)
    assert user["email"] == "u1@example.com"

    response = await client.get("/auth/me")
    assert response.status_code == 200
    assert response.json()["id"] == user["id"]


async def test_api_errors_use_spec_envelope(client: AsyncClient):
    unauthorized = await client.get("/auth/me")
    assert unauthorized.status_code == 401
    assert unauthorized.json()["detail"] == {
        "code": "unauthorized",
        "message": "Authentication required",
    }

    await login(client)
    invalid = await client.post("/api/lists", json={"name": "   "})
    assert invalid.status_code == 422
    detail = invalid.json()["detail"]
    assert detail["code"] == "validation_error"
    assert detail["message"] == "Validation failed"
    assert detail["fields"][0]["field"] == "name"


async def test_google_oauth_login_state_keeps_nonce_and_redirect_target(
    client: AsyncClient,
):
    app = client.app

    def override_settings() -> Settings:
        return Settings(
            session_secret="test-secret",
            google_client_id="google-client",
            google_client_secret="google-secret",
            frontend_base_url="http://frontend.test",
            backend_base_url="http://backend.test",
            cors_allowed_origins="http://testserver",
        )

    app.dependency_overrides[get_settings] = override_settings

    response = await client.get("/auth/google/login", params={"next": "/app/lists/list-1"})

    assert response.status_code == 307
    location = response.headers["location"]
    state = response.cookies["ptm_oauth_state"]
    payload = parse_oauth_state(state, "google", override_settings())
    assert payload["redirect_path"] == "/app/lists/list-1"
    assert f"nonce={payload['nonce']}" in location
    assert f"state={state}" in location


async def test_google_oauth_callback_uses_mock_exchange_and_redirect_target(
    client: AsyncClient,
    monkeypatch,
):
    app = client.app

    def override_settings() -> Settings:
        return Settings(
            session_secret="test-secret",
            google_client_id="google-client",
            google_client_secret="google-secret",
            frontend_base_url="http://frontend.test",
            backend_base_url="http://backend.test",
            cors_allowed_origins="http://testserver",
        )

    async def fake_exchange_google_code(
        code: str, settings: Settings, nonce: str
    ) -> ProviderProfile:
        assert code == "oauth-code"
        assert nonce
        return ProviderProfile(
            provider="google",
            provider_user_id="google-user-1",
            email="google@example.com",
            display_name="Google User",
        )

    app.dependency_overrides[get_settings] = override_settings
    monkeypatch.setattr("app.api.auth.exchange_google_code", fake_exchange_google_code)

    login_response = await client.get("/auth/google/login", params={"next": "/app/lists/list-1"})
    state = login_response.cookies["ptm_oauth_state"]
    callback = await client.get(
        "/auth/google/callback",
        params={"code": "oauth-code", "state": state},
    )

    assert callback.status_code == 307
    assert callback.headers["location"] == "http://frontend.test/app/lists/list-1"
    assert callback.cookies["ptm_session"]


async def test_google_exchange_validates_id_token_nonce(monkeypatch):
    claims = {"sub": "google-sub", "nonce": "nonce-1"}
    id_token = _fake_jwt(claims)
    responses = {
        "https://oauth2.googleapis.com/token": {
            "access_token": "access-token",
            "id_token": id_token,
        },
        "https://oauth2.googleapis.com/tokeninfo": {
            "aud": "google-client",
            "sub": "google-sub",
            "nonce": "nonce-1",
        },
        "https://openidconnect.googleapis.com/v1/userinfo": {
            "sub": "google-sub",
            "email": "google@example.com",
            "name": "Google User",
            "picture": "https://example.com/avatar.png",
        },
    }
    monkeypatch.setattr(
        "app.auth.oauth.httpx.AsyncClient",
        lambda timeout: FakeOAuthClient(responses),
    )

    profile = await exchange_google_code("code", _oauth_settings(), "nonce-1")

    assert profile.provider_user_id == "google-sub"
    assert profile.email == "google@example.com"


async def test_google_exchange_rejects_nonce_mismatch(monkeypatch):
    id_token = _fake_jwt({"sub": "google-sub", "nonce": "nonce-1"})
    responses = {
        "https://oauth2.googleapis.com/token": {
            "access_token": "access-token",
            "id_token": id_token,
        },
        "https://oauth2.googleapis.com/tokeninfo": {
            "aud": "google-client",
            "sub": "google-sub",
            "nonce": "different-nonce",
        },
    }
    monkeypatch.setattr(
        "app.auth.oauth.httpx.AsyncClient",
        lambda timeout: FakeOAuthClient(responses),
    )

    try:
        await exchange_google_code("code", _oauth_settings(), "nonce-1")
    except HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail["code"] == "oauth_invalid_token"
    else:
        raise AssertionError("Expected nonce mismatch to fail")


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
    cross_user_status = await client.patch(
        f"/api/tasks/{task_id}/status",
        json={"status": "done"},
    )
    assert cross_user_status.status_code == 404
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

    in_progress = await client.get(
        "/api/tasks",
        params={"list_id": list_id, "status": "in_progress"},
    )
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


async def test_patch_list_returns_current_task_counts(client: AsyncClient):
    await login(client)
    list_response = await client.post("/api/lists", json={"name": "Counts"})
    list_id = list_response.json()["id"]
    await client.post("/api/tasks", json={"list_id": list_id, "title": "Open task"})
    await client.post(
        "/api/tasks",
        json={"list_id": list_id, "title": "Done task", "status": "done"},
    )

    response = await client.patch(f"/api/lists/{list_id}", json={"name": "Renamed counts"})

    assert response.status_code == 200, response.text
    assert response.json()["task_count"] == 2
    assert response.json()["open_task_count"] == 1


class FakeOAuthResponse:
    is_success = True

    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload


class FakeOAuthClient:
    def __init__(self, responses):
        self.responses = responses

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return None

    async def post(self, url, **kwargs):
        return FakeOAuthResponse(self.responses[url])

    async def get(self, url, **kwargs):
        return FakeOAuthResponse(self.responses[url])


def _fake_jwt(payload: dict) -> str:
    header = {"alg": "none"}
    segments = [
        _urlsafe_json(header),
        _urlsafe_json(payload),
        "",
    ]
    return ".".join(segments)


def _urlsafe_json(value: dict) -> str:
    encoded = json.dumps(value, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(encoded).decode().rstrip("=")


def _oauth_settings() -> Settings:
    return Settings(
        google_client_id="google-client",
        google_client_secret="google-secret",
        backend_base_url="http://backend.test",
    )
