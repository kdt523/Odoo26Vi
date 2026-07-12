"""
app/models/notification.py — Notification entity.

Written by core-api, read by reports-api.

Notification types (implement delivery in later pass):
  AssetAssigned | MaintenanceApproved | MaintenanceRejected |
  BookingCreated | BookingCancelled | TransferApproved |
  OverdueReturnAlert | AuditDiscrepancyFlagged
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    type: Mapped[str] = mapped_column(
        SAEnum(
            "AssetAssigned",
            "MaintenanceApproved",
            "MaintenanceRejected",
            "BookingCreated",
            "BookingCancelled",
            "TransferApproved",
            "OverdueReturnAlert",
            "AuditDiscrepancyFlagged",
            name="notification_type_enum",
        ),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Optional deep-link reference
    entity_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ──────────────────────────────────────────────────────
    user: Mapped["Employee"] = relationship("Employee", back_populates="notifications")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<Notification id={self.id} type={self.type!r} is_read={self.is_read}>"
