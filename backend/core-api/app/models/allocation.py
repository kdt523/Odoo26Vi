"""
app/models/allocation.py — Allocation entity.

An Allocation links an Asset to an Employee and/or Department for a period.

TODO (allocations router): enforce conflict rule —
  if asset.status == 'Allocated', reject new allocation and direct
  the requester to create a TransferRequest instead.
"""

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db import Base


class Allocation(Base):
    __tablename__ = "allocations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Either employee or department (or both) must be set at business-logic layer
    employee_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )

    allocated_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_return_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    actual_return_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    return_condition_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        SAEnum(
            "Active",
            "Returned",
            "TransferPending",
            "Transferred",
            name="allocation_status_enum",
        ),
        nullable=False,
        default="Active",
    )

    overdue_alert_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ──────────────────────────────────────────────────────
    asset: Mapped["Asset"] = relationship("Asset", back_populates="allocations")  # type: ignore[name-defined]
    employee: Mapped[Optional["Employee"]] = relationship(  # type: ignore[name-defined]
        "Employee", back_populates="allocations", foreign_keys=[employee_id]
    )
    department: Mapped[Optional["Department"]] = relationship("Department")  # type: ignore[name-defined]
    transfer_requests: Mapped[list["TransferRequest"]] = relationship(  # type: ignore[name-defined]
        "TransferRequest", back_populates="allocation"
    )

    def __repr__(self) -> str:
        return f"<Allocation id={self.id} asset_id={self.asset_id} status={self.status!r}>"
