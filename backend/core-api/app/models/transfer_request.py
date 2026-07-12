"""
app/models/transfer_request.py — TransferRequest entity.

A TransferRequest is raised when an already-Allocated asset needs to move
to a different employee/department without first returning it.

Status flow (implement in allocations router):
  Requested → Approved → Reallocated
  Requested → Rejected
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db import Base


class TransferRequest(Base):
    __tablename__ = "transfer_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    allocation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("allocations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    requested_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,  # nullable so employee deletion doesn't break history
    )

    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Optional: who the asset will be transferred to
    target_employee_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )

    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        SAEnum(
            "Requested",
            "Approved",
            "Rejected",
            "Reallocated",
            name="transfer_status_enum",
        ),
        nullable=False,
        default="Requested",
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
    allocation: Mapped["Allocation"] = relationship("Allocation", back_populates="transfer_requests")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<TransferRequest id={self.id} status={self.status!r}>"
