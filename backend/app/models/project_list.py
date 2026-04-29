from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class ProjectList(TimestampMixin, Base):
    __tablename__ = "project_lists"
    __table_args__ = (
        Index("ix_project_lists_user_lower_name", "user_id", text("lower(name)"), unique=True),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    sort_order: Mapped[int] = mapped_column(default=0)

    user = relationship("User", back_populates="lists")
    tasks = relationship("Task", back_populates="list", cascade="all, delete-orphan", passive_deletes=True)
