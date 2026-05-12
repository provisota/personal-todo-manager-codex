from sqlalchemy import ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class TaskChangeRecord(TimestampMixin, Base):
    __tablename__ = "task_history"
    __table_args__ = (Index("ix_task_history_task_created", "task_id", "created_at"),)

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=new_uuid)
    task_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tasks.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    user = relationship("User")
    fields: Mapped[list["FieldChange"]] = relationship(
        "FieldChange", back_populates="history", cascade="all, delete-orphan"
    )


class FieldChange(Base):
    __tablename__ = "task_history_fields"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=new_uuid)
    history_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("task_history.id", ondelete="CASCADE"),
        index=True,
    )
    field_name: Mapped[str] = mapped_column(String(50), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)

    history: Mapped["TaskChangeRecord"] = relationship("TaskChangeRecord", back_populates="fields")
