from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_list import ProjectList
from app.models.task import Task
from app.schemas.lists import ListCreate, ListRead, ListUpdate


async def list_user_lists(session: AsyncSession, user_id: str) -> list[ListRead]:
    stmt = (
        select(
            ProjectList,
            func.count(Task.id).label("task_count"),
            func.count(Task.id).filter(Task.status != "done").label("open_task_count"),
        )
        .outerjoin(Task, Task.list_id == ProjectList.id)
        .where(ProjectList.user_id == user_id)
        .group_by(ProjectList.id)
        .order_by(ProjectList.sort_order, ProjectList.created_at)
    )
    rows = (await session.execute(stmt)).all()
    return [
        ListRead(
            id=project_list.id,
            name=project_list.name,
            task_count=task_count,
            open_task_count=open_task_count,
            created_at=project_list.created_at,
            updated_at=project_list.updated_at,
        )
        for project_list, task_count, open_task_count in rows
    ]


async def get_user_list(session: AsyncSession, user_id: str, list_id: str) -> ProjectList:
    result = await session.execute(
        select(ProjectList).where(ProjectList.id == list_id, ProjectList.user_id == user_id)
    )
    project_list = result.scalar_one_or_none()
    if not project_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")
    return project_list


async def create_list(session: AsyncSession, user_id: str, payload: ListCreate) -> ProjectList:
    await _ensure_unique_name(session, user_id, payload.name)
    project_list = ProjectList(user_id=user_id, name=payload.name)
    session.add(project_list)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="List already exists") from exc
    await session.refresh(project_list)
    return project_list


async def rename_list(
    session: AsyncSession, user_id: str, list_id: str, payload: ListUpdate
) -> ProjectList:
    project_list = await get_user_list(session, user_id, list_id)
    await _ensure_unique_name(session, user_id, payload.name, exclude_id=list_id)
    project_list.name = payload.name
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="List already exists") from exc
    await session.refresh(project_list)
    return project_list


async def delete_list(session: AsyncSession, user_id: str, list_id: str) -> int:
    project_list = await get_user_list(session, user_id, list_id)
    deleted_tasks = await session.scalar(
        select(func.count(Task.id)).where(Task.user_id == user_id, Task.list_id == list_id)
    )
    await session.delete(project_list)
    await session.commit()
    return int(deleted_tasks or 0)


async def _ensure_unique_name(
    session: AsyncSession, user_id: str, name: str, exclude_id: str | None = None
) -> None:
    stmt = select(ProjectList).where(
        ProjectList.user_id == user_id,
        func.lower(ProjectList.name) == name.lower(),
    )
    if exclude_id:
        stmt = stmt.where(ProjectList.id != exclude_id)
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="List already exists")
