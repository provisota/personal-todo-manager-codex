from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, new_uuid, utc_now


class NotificationAck(TimestampMixin, Base):
    __tablename__ = "notification_acks"
    __table_args__ = (
        UniqueConstraint("user_id", "task_id", "notification_type", name="uq_notification_ack"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    notification_type: Mapped[str] = mapped_column(String(30))
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
