"""
app/models/employee.py — Employee entity (platform user).

Role is enforced at the application layer:
  - Signup always creates role='Employee'.
  - Promotion to DepartmentHead / AssetManager / Admin is Admin-only.
"""

import uuid
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(1024), nullable=False)

    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )

    role: Mapped[str] = mapped_column(
        SAEnum(
            "Employee",
            "DepartmentHead",
            "AssetManager",
            "Admin",
            name="employee_role_enum",
        ),
        nullable=False,
        default="Employee",
    )

    status: Mapped[str] = mapped_column(
        SAEnum("Active", "Inactive", name="employee_status_enum"),
        nullable=False,
        default="Active",
    )

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── Relationships ──────────────────────────────────────────────────────
    department: Mapped[Optional["Department"]] = relationship(  # type: ignore[name-defined]
        "Department",
        back_populates="employees",
        foreign_keys=[department_id],
    )
    allocations: Mapped[list["Allocation"]] = relationship(  # type: ignore[name-defined]
        "Allocation", back_populates="employee", foreign_keys="Allocation.employee_id"
    )
    bookings: Mapped[list["Booking"]] = relationship(  # type: ignore[name-defined]
        "Booking", back_populates="employee"
    )
    maintenance_requests: Mapped[list["MaintenanceRequest"]] = relationship(  # type: ignore[name-defined]
        "MaintenanceRequest", back_populates="raised_by_employee", foreign_keys="MaintenanceRequest.raised_by"
    )
    notifications: Mapped[list["Notification"]] = relationship(  # type: ignore[name-defined]
        "Notification", back_populates="user"
    )
    activity_logs: Mapped[list["ActivityLog"]] = relationship(  # type: ignore[name-defined]
        "ActivityLog", back_populates="user"
    )

    def __repr__(self) -> str:
        return f"<Employee id={self.id} email={self.email!r} role={self.role!r}>"
