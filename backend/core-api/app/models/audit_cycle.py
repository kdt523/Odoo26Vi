"""
app/models/audit_cycle.py — AuditCycle + AuditCycleAuditor join table.

AuditCycle defines the scope (department or location) and time window.
AuditCycleAuditor is the M2M join between AuditCycle and Employee.
"""

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Column, Date, DateTime, ForeignKey, String, Table, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db import Base


# ── Join table (no ORM class needed) ──────────────────────────────────────
audit_cycle_auditors = Table(
    "audit_cycle_auditors",
    Base.metadata,
    Column(
        "audit_cycle_id",
        UUID(as_uuid=True),
        ForeignKey("audit_cycles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "employee_id",
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class AuditCycle(Base):
    __tablename__ = "audit_cycles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Scope: by department OR by location (at least one should be set)
    scope_department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    location: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    status: Mapped[str] = mapped_column(
        SAEnum("Draft", "Active", "Closed", name="audit_cycle_status_enum"),
        nullable=False,
        default="Draft",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ──────────────────────────────────────────────────────
    auditors: Mapped[list["Employee"]] = relationship(  # type: ignore[name-defined]
        "Employee",
        secondary=audit_cycle_auditors,
        backref="audit_cycles",
    )
    audit_items: Mapped[list["AuditItem"]] = relationship(  # type: ignore[name-defined]
        "AuditItem", back_populates="audit_cycle"
    )

    def __repr__(self) -> str:
        return f"<AuditCycle id={self.id} status={self.status!r}>"


# Re-export the association table for Alembic visibility
AuditCycleAuditor = audit_cycle_auditors
