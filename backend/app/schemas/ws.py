from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


NotificationType = Literal["overdue", "due_soon"]


class NotificationRead(BaseModel):
    id: str
    type: NotificationType
    task_id: str
    list_id: str
    title: str
    due_date: date | None
    priority: str
    message: str


class NotificationBatchPayload(BaseModel):
    generated_at: datetime
    notifications: list[NotificationRead]


class NotificationBatchMessage(BaseModel):
    type: Literal["notification_batch"] = "notification_batch"
    payload: NotificationBatchPayload


class SubscribePayload(BaseModel):
    enabled_types: list[NotificationType] = ["overdue", "due_soon"]
    interval_seconds: int = Field(default=60, ge=30, le=300)
    include_acknowledged: bool = False


class SubscribeMessage(BaseModel):
    type: Literal["subscribe"]
    payload: SubscribePayload


class AckPayload(BaseModel):
    notification_id: str


class AckMessage(BaseModel):
    type: Literal["ack"]
    payload: AckPayload


class AckOkPayload(BaseModel):
    notification_id: str


class AckOkMessage(BaseModel):
    type: Literal["ack_ok"] = "ack_ok"
    payload: AckOkPayload


class ErrorPayload(BaseModel):
    code: str
    message: str


class ErrorMessage(BaseModel):
    type: Literal["error"] = "error"
    payload: ErrorPayload

