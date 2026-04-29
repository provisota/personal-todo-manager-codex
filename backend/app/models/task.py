import enum
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class TaskStatus(str, enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class TaskPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Task(TimestampMixin, Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint("status in ('todo', 'in_progress', 'done')", name="ck_tasks_status"),
        CheckConstraint("priority in ('low', 'medium', 'high')", name="ck_tasks_priority"),
        CheckConstraint("length(trim(title)) between 1 and 200", name="ck_tasks_title_length"),
        Index("ix_tasks_user_list", "user_id", "list_id"),
        Index("ix_tasks_user_status", "user_id", "status"),
        Index("ix_tasks_user_priority", "user_id", "priority"),
        Index("ix_tasks_user_due_date", "user_id", "due_date"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    list_id: Mapped[str] = mapped_column(ForeignKey("project_lists.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default=TaskStatus.todo.value)
    priority: Mapped[str] = mapped_column(String(30), default=TaskPriority.medium.value)
    due_date: Mapped[date | None] = mapped_column(Date)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user = relationship("User", back_populates="tasks")
    list = relationship("ProjectList", back_populates="tasks")

