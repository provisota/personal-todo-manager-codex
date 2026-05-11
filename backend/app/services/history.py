from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.task import Task
from app.models.task_history import FieldChange, TaskChangeRecord
from app.models.user import User


async def get_task_history(
    session: AsyncSession, user_id: str, task_id: str
) -> list[TaskChangeRecord] | None:
    task_result = await session.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user_id)
    )
    if not task_result.scalar_one_or_none():
        return None

    result = await session.execute(
        select(TaskChangeRecord)
        .where(TaskChangeRecord.task_id == task_id)
        .options(
            joinedload(TaskChangeRecord.fields),
            joinedload(TaskChangeRecord.user),
        )
        .order_by(TaskChangeRecord.created_at.desc())
    )
    records = result.unique().scalars().all()
    return list(records)
