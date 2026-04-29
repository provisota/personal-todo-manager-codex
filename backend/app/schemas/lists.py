from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ListCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("List name is required")
        return value


class ListUpdate(ListCreate):
    pass


class ListRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    task_count: int = 0
    open_task_count: int = 0
    created_at: datetime
    updated_at: datetime


class ListDeleteResponse(BaseModel):
    ok: bool = True
    deleted_tasks: int

