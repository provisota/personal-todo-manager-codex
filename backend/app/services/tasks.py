from datetime import UTC, date, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_list import ProjectList
from app.models.task import Task, TaskPriority, TaskStatus
from app.schemas.tasks import TaskCreate, TaskUpdate


async def _ensure_list_owned(session: AsyncSession, user_id: str, list_id: str) -> ProjectList:
    result = await session.execute(
        select(ProjectList).where(ProjectList.id == list_id, ProjectList.user_id == user_id)
    )
    project_list = result.scalar_one_or_none()
    if not project_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")
    return project_list


async def get_user_task(session: AsyncSession, user_id: str, task_id: str) -> Task:
    result = await session.execute(select(Task).where(Task.id == task_id, Task.user_id == user_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


async def list_tasks(
    session: AsyncSession,
    user_id: str,
    list_id: str,
    search: str | None = None,
    status_filter: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    due: str = "all",
) -> list[Task]:
    await _ensure_list_owned(session, user_id, list_id)
    today = date.today()
    stmt = select(Task).where(Task.user_id == user_id, Task.list_id == list_id)
    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(or_(Task.title.ilike(pattern), Task.description.ilike(pattern)))
    if status_filter:
        stmt = stmt.where(Task.status == status_filter.value)
    if priority:
        stmt = stmt.where(Task.priority == priority.value)
    if due == "overdue":
        stmt = stmt.where(Task.status != TaskStatus.done.value, Task.due_date < today)
    elif due == "today":
        stmt = stmt.where(Task.due_date == today)
    elif due == "next_7_days":
        stmt = stmt.where(Task.due_date >= today, Task.due_date <= today + timedelta(days=7))
    elif due != "all":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid due filter")
    stmt = stmt.order_by(Task.due_date.is_(None), Task.due_date, Task.created_at.desc())
    return list((await session.execute(stmt)).scalars().all())


async def create_task(session: AsyncSession, user_id: str, payload: TaskCreate) -> Task:
    await _ensure_list_owned(session, user_id, payload.list_id)
    completed_at = datetime.now(UTC) if payload.status == TaskStatus.done else None
    task = Task(
        user_id=user_id,
        list_id=payload.list_id,
        title=payload.title,
        description=payload.description,
        status=payload.status.value,
        priority=payload.priority.value,
        due_date=payload.due_date,
        completed_at=completed_at,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


def _apply_status_transition(task: Task, next_status: TaskStatus) -> None:
    if next_status == TaskStatus.done and task.status != TaskStatus.done.value:
        task.completed_at = datetime.now(UTC)
    elif next_status != TaskStatus.done:
        task.completed_at = None
    task.status = next_status.value


async def update_task(session: AsyncSession, user_id: str, task_id: str, payload: TaskUpdate) -> Task:
    task = await get_user_task(session, user_id, task_id)
    data = payload.model_dump(exclude_unset=True)
    if "list_id" in data and data["list_id"] is not None and data["list_id"] != task.list_id:
        await _ensure_list_owned(session, user_id, data["list_id"])
        task.list_id = data["list_id"]
    if "title" in data and data["title"] is not None:
        task.title = data["title"]
    if "description" in data:
        task.description = data["description"] or ""
    if "priority" in data and data["priority"] is not None:
        task.priority = data["priority"].value
    if "due_date" in data:
        task.due_date = data["due_date"]
    if "status" in data and data["status"] is not None:
        _apply_status_transition(task, data["status"])
    await session.commit()
    await session.refresh(task)
    return task


async def update_task_status(
    session: AsyncSession, user_id: str, task_id: str, next_status: TaskStatus
) -> Task:
    task = await get_user_task(session, user_id, task_id)
    _apply_status_transition(task, next_status)
    await session.commit()
    await session.refresh(task)
    return task


async def delete_task(session: AsyncSession, user_id: str, task_id: str) -> None:
    task = await get_user_task(session, user_id, task_id)
    await session.delete(task)
    await session.commit()

