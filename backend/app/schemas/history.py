from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FieldChangeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    field_name: str
    old_value: str | None
    new_value: str | None


class TaskHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
    changed_by_name: str
    created_at: datetime
    fields: list[FieldChangeRead]
