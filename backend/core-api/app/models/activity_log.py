"""
app/models/activity_log.py — ActivityLog entity (immutable audit trail).

Written by core-api at every significant state change.
Read by reports-api via the activity-log blueprint.

details (JSONB) stores action-specific context, e.g.:
  {"from_status": "Available", "to_status": "Allocated", "allocation_id": "..."}
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────
    user: Mapped[Optional["Employee"]] = relationship(  # type: ignore[name-defined]
        "Employee", back_populates="activity_logs"
    )

    def __repr__(self) -> str:
        return (
            f"<ActivityLog id={self.id} action={self.action!r} "
            f"entity={self.entity_type}/{self.entity_id}>"
        )
