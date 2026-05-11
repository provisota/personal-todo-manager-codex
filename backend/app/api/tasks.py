from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_session
from app.models.task import TaskPriority, TaskStatus
from app.models.user import User
from app.schemas.auth import OkResponse
from app.schemas.history import FieldChangeRead, TaskHistoryRead
from app.schemas.tasks import TaskCreate, TaskRead, TaskStatusUpdate, TaskUpdate
from app.services.history import get_task_history
from app.services.tasks import (
    create_task,
    delete_task,
    list_tasks,
    update_task,
    update_task_status,
)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
async def read_tasks(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    list_id: str,
    search: str | None = None,
    status: Annotated[TaskStatus | None, Query(alias="status")] = None,
    priority: TaskPriority | None = None,
    due: str = "all",
) -> list[TaskRead]:
    return await list_tasks(session, current_user.id, list_id, search, status, priority, due)


@router.post("", response_model=TaskRead, status_code=201)
async def create_user_task(
    payload: TaskCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TaskRead:
    return await create_task(session, current_user.id, payload)


@router.patch("/{task_id}", response_model=TaskRead)
async def patch_task(
    task_id: str,
    payload: TaskUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TaskRead:
    return await update_task(session, current_user.id, task_id, payload)


@router.patch("/{task_id}/status", response_model=TaskRead)
async def patch_task_status(
    task_id: str,
    payload: TaskStatusUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TaskRead:
    return await update_task_status(session, current_user.id, task_id, payload.status)


@router.delete("/{task_id}", response_model=OkResponse)
async def remove_task(
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OkResponse:
    await delete_task(session, current_user.id, task_id)
    return OkResponse()


@router.get("/{task_id}/history", response_model=list[TaskHistoryRead])
async def get_history(
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[TaskHistoryRead]:
    records = await get_task_history(session, current_user.id, task_id)
    if records is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return [
        TaskHistoryRead(
            id=r.id,
            task_id=r.task_id,
            changed_by_name=r.user.display_name,
            created_at=r.created_at,
            fields=[FieldChangeRead.model_validate(f) for f in r.fields],
        )
        for r in records
    ]

