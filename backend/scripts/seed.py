import asyncio
import os
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.project_list import ProjectList
from app.models.task import Task
from app.repositories.auth import upsert_user_from_profile
from app.schemas.auth import ProviderProfile


async def main() -> None:
    settings = get_settings()
    if settings.environment not in {"local", "test"}:
        raise SystemExit("Seed script is only allowed in local/test environments")
    engine = create_async_engine(os.getenv("DATABASE_URL", settings.database_url), pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        user = await upsert_user_from_profile(
            session,
            ProviderProfile(
                provider="github",
                provider_user_id="demo-user",
                email="demo@example.com",
                display_name="Demo User",
                avatar_url=None,
            ),
        )
        work = ProjectList(user_id=user.id, name="Work")
        personal = ProjectList(user_id=user.id, name="Personal")
        learning = ProjectList(user_id=user.id, name="Learning")
        session.add_all([work, personal, learning])
        await session.flush()
        today = date.today()
        session.add_all(
            [
                Task(
                    user_id=user.id,
                    list_id=work.id,
                    title="Submit overdue report",
                    description="High priority overdue seed task",
                    status="todo",
                    priority="high",
                    due_date=today - timedelta(days=1),
                ),
                Task(
                    user_id=user.id,
                    list_id=work.id,
                    title="Review weekly plan",
                    description="Due soon example",
                    status="in_progress",
                    priority="medium",
                    due_date=today + timedelta(days=2),
                ),
                Task(
                    user_id=user.id,
                    list_id=personal.id,
                    title="Buy groceries",
                    description="Completed seed task",
                    status="done",
                    priority="low",
                    due_date=today,
                ),
                Task(
                    user_id=user.id,
                    list_id=learning.id,
                    title="Read FastAPI docs",
                    description="No due date example",
                    status="todo",
                    priority="medium",
                    due_date=None,
                ),
            ]
        )
        await session.commit()
    await engine.dispose()
    print("Seed data created for demo@example.com")


if __name__ == "__main__":
    asyncio.run(main())

