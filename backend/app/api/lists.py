from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.lists import ListCreate, ListDeleteResponse, ListRead, ListUpdate
from app.services.lists import create_list, delete_list, list_user_lists, rename_list

router = APIRouter(prefix="/api/lists", tags=["lists"])


@router.get("", response_model=list[ListRead])
async def list_lists(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ListRead]:
    return await list_user_lists(session, current_user.id)


@router.post("", response_model=ListRead, status_code=201)
async def create_project_list(
    payload: ListCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ListRead:
    project_list = await create_list(session, current_user.id, payload)
    return ListRead(
        id=project_list.id,
        name=project_list.name,
        task_count=0,
        open_task_count=0,
        created_at=project_list.created_at,
        updated_at=project_list.updated_at,
    )


@router.patch("/{list_id}", response_model=ListRead)
async def update_project_list(
    list_id: str,
    payload: ListUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ListRead:
    project_list = await rename_list(session, current_user.id, list_id, payload)
    return ListRead(
        id=project_list.id,
        name=project_list.name,
        task_count=0,
        open_task_count=0,
        created_at=project_list.created_at,
        updated_at=project_list.updated_at,
    )


@router.delete("/{list_id}", response_model=ListDeleteResponse)
async def remove_project_list(
    list_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ListDeleteResponse:
    deleted_tasks = await delete_list(session, current_user.id, list_id)
    return ListDeleteResponse(deleted_tasks=deleted_tasks)

