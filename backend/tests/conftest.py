import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.main import create_app
from app.models.base import Base


@pytest.fixture
async def client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False})
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_session():
        async with session_factory() as session:
            yield session

    def override_settings() -> Settings:
        return Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            session_secret="test-secret",
            test_auth_enabled=True,
            ws_notification_interval_seconds=30,
            cors_allowed_origins="http://testserver",
        )

    app = create_app()
    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_settings] = override_settings

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as test_client:
        test_client.app = app  # type: ignore[attr-defined]
        yield test_client

    app.dependency_overrides.clear()
    await engine.dispose()


async def login(client: AsyncClient, provider_user_id: str = "user-1", email: str = "u1@example.com"):
    response = await client.post(
        "/auth/test-login",
        json={
            "provider": "github",
            "provider_user_id": provider_user_id,
            "email": email,
            "display_name": f"User {provider_user_id}",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()
