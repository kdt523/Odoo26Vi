"""
app/models/maintenance_request.py — MaintenanceRequest entity.

Status flow (implement in maintenance router):
  Pending → Approved → TechnicianAssigned → InProgress → Resolved
  Pending → Rejected

When status moves to Approved / TechnicianAssigned, asset.status
should transition to UnderMaintenance (TODO in maintenance router).
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db import Base


class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    raised_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
    )

    issue_description: Mapped[str] = mapped_column(Text, nullable=False)

    priority: Mapped[str] = mapped_column(
        SAEnum("Low", "Medium", "High", "Critical", name="maintenance_priority_enum"),
        nullable=False,
        default="Medium",
    )

    photo_ref: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
    )

    # The technician assigned to carry out the maintenance
    technician: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    status: Mapped[str] = mapped_column(
        SAEnum(
            "Pending",
            "Approved",
            "Rejected",
            "TechnicianAssigned",
            "InProgress",
            "Resolved",
            name="maintenance_status_enum",
        ),
        nullable=False,
        default="Pending",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────────────
    asset: Mapped["Asset"] = relationship("Asset", back_populates="maintenance_requests")  # type: ignore[name-defined]
    raised_by_employee: Mapped[Optional["Employee"]] = relationship(  # type: ignore[name-defined]
        "Employee",
        back_populates="maintenance_requests",
        foreign_keys=[raised_by],
    )

    def __repr__(self) -> str:
        return f"<MaintenanceRequest id={self.id} status={self.status!r}>"
