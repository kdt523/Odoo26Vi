"""
app/models/department.py — Department entity.

Self-referential hierarchy (parent_department_id) supports sub-departments.
head_employee_id is a soft FK to employees (set post-insertion to avoid
circular FK issues at DDL time — see relationship note).
"""

import uuid

from sqlalchemy import ForeignKey, String, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Self-referential parent (nullable = top-level dept)
    parent_department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Soft reference to an Employee acting as dept head.
    # FK defined here but Employee model also references Department —
    # use_alter=True avoids circular DDL.
    head_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="SET NULL", use_alter=True, name="fk_dept_head"),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        SAEnum("Active", "Inactive", name="department_status_enum"),
        nullable=False,
        default="Active",
    )

    # ── Relationships ──────────────────────────────────────────────────────
    parent: Mapped["Department | None"] = relationship(
        "Department", remote_side="Department.id", back_populates="children"
    )
    children: Mapped[list["Department"]] = relationship(
        "Department", back_populates="parent"
    )
    employees: Mapped[list["Employee"]] = relationship(  # type: ignore[name-defined]
        "Employee",
        back_populates="department",
        foreign_keys="Employee.department_id",
    )

    def __repr__(self) -> str:
        return f"<Department id={self.id} name={self.name!r}>"
