import asyncio
import os

import pytest
from alembic import command
from alembic.config import Config
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.repositories.auth import upsert_user_from_profile
from app.schemas.auth import ProviderProfile
from app.schemas.lists import ListCreate
from app.schemas.tasks import TaskCreate
from app.services.lists import create_list, delete_list
from app.services.tasks import create_task, list_tasks


def test_postgres_migrations_and_authorization_behaviour():
    database_url = os.getenv("POSTGRES_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set POSTGRES_TEST_DATABASE_URL to run PostgreSQL integration tests")

    previous_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url
    get_settings.cache_clear()
    try:
        config = Config("alembic.ini")
        command.downgrade(config, "base")
        command.upgrade(config, "head")
        asyncio.run(_assert_postgres_behaviour(database_url))
    finally:
        if previous_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_url
        get_settings.cache_clear()


async def _assert_postgres_behaviour(database_url: str) -> None:
    engine = create_async_engine(database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        result = await session.execute(
            text(
                """
                select table_name, column_name, data_type
                from information_schema.columns
                where table_schema = 'public'
                  and column_name in ('id', 'user_id', 'list_id', 'task_id')
                  and table_name in (
                    'users',
                    'oauth_identities',
                    'project_lists',
                    'tasks',
                    'notification_acks'
                  )
                """
            )
        )
        assert {row.data_type for row in result} == {"uuid"}

        first_user = await upsert_user_from_profile(
            session,
            ProviderProfile(
                provider="github",
                provider_user_id="pg-user-1",
                email="pg1@example.com",
                display_name="PG One",
            ),
        )
        second_user = await upsert_user_from_profile(
            session,
            ProviderProfile(
                provider="github",
                provider_user_id="pg-user-2",
                email="pg2@example.com",
                display_name="PG Two",
            ),
        )
        project_list = await create_list(session, first_user.id, ListCreate(name="Work"))
        with pytest.raises(HTTPException) as duplicate:
            await create_list(session, first_user.id, ListCreate(name="work"))
        assert duplicate.value.status_code == 409

        await create_task(
            session,
            first_user.id,
            TaskCreate(list_id=project_list.id, title="Owned"),
        )
        with pytest.raises(HTTPException) as cross_user:
            await list_tasks(session, second_user.id, project_list.id)
        assert cross_user.value.status_code == 404

        assert await delete_list(session, first_user.id, project_list.id) == 1
        with pytest.raises(HTTPException):
            await list_tasks(session, first_user.id, project_list.id)
    await engine.dispose()
