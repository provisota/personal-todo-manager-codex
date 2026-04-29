from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification_ack import NotificationAck
from app.models.task import Task, TaskStatus
from app.schemas.ws import NotificationRead


class NotificationService:
    def __init__(self, today: date | None = None):
        self.today = today or date.today()

    async def get_notifications(
        self,
        session: AsyncSession,
        user_id: str,
        enabled_types: list[str] | None = None,
        include_acknowledged: bool = False,
    ) -> list[NotificationRead]:
        enabled = set(enabled_types or ["overdue", "due_soon"])
        notifications: list[NotificationRead] = []
        if "overdue" in enabled:
            notifications.extend(
                await self._query_type(session, user_id, "overdue", include_acknowledged)
            )
        if "due_soon" in enabled:
            notifications.extend(
                await self._query_type(session, user_id, "due_soon", include_acknowledged)
            )
        return notifications

    async def _query_type(
        self,
        session: AsyncSession,
        user_id: str,
        notification_type: str,
        include_acknowledged: bool,
    ) -> list[NotificationRead]:
        stmt = select(Task).where(Task.user_id == user_id, Task.status != TaskStatus.done.value)
        if notification_type == "overdue":
            stmt = stmt.where(Task.due_date < self.today)
        else:
            stmt = stmt.where(
                Task.due_date >= self.today,
                Task.due_date <= self.today + timedelta(days=3),
            )
        if not include_acknowledged:
            acked = select(NotificationAck.task_id).where(
                NotificationAck.user_id == user_id,
                NotificationAck.notification_type == notification_type,
            )
            stmt = stmt.where(Task.id.not_in(acked))
        stmt = stmt.order_by(Task.due_date, Task.priority.desc())
        tasks = (await session.execute(stmt)).scalars().all()
        return [
            NotificationRead(
                id=f"{notification_type}:{task.id}",
                type=notification_type,  # type: ignore[arg-type]
                task_id=task.id,
                list_id=task.list_id,
                title=task.title,
                due_date=task.due_date,
                priority=task.priority,
                message="Task is overdue" if notification_type == "overdue" else "Task is due soon",
            )
            for task in tasks
        ]

    async def acknowledge(self, session: AsyncSession, user_id: str, notification_id: str) -> None:
        try:
            notification_type, task_id = notification_id.split(":", 1)
        except ValueError as exc:
            raise ValueError("Invalid notification id") from exc
        if notification_type not in {"overdue", "due_soon"}:
            raise ValueError("Invalid notification type")
        result = await session.execute(
            select(Task).where(Task.id == task_id, Task.user_id == user_id)
        )
        if not result.scalar_one_or_none():
            raise ValueError("Task not found")
        existing = await session.execute(
            select(NotificationAck).where(
                NotificationAck.user_id == user_id,
                NotificationAck.task_id == task_id,
                NotificationAck.notification_type == notification_type,
            )
        )
        ack = existing.scalar_one_or_none()
        if ack is None:
            session.add(
                NotificationAck(
                    user_id=user_id,
                    task_id=task_id,
                    notification_type=notification_type,
                    acknowledged_at=datetime.now(UTC),
                )
            )
        else:
            ack.acknowledged_at = datetime.now(UTC)
            ack.updated_at = datetime.now(UTC)
        await session.commit()
