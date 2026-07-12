"""
app/schemas/org.py — Pydantic schemas for the org router.
Covers: Department, AssetCategory, Employee directory, role promotion.
"""

from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ── Department ─────────────────────────────────────────────────────────────
class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    parent_department_id: Optional[UUID] = None
    head_employee_id: Optional[UUID] = None
    status: str = "Active"


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    parent_department_id: Optional[UUID] = None
    head_employee_id: Optional[UUID] = None
    status: Optional[str] = None


class DepartmentOut(BaseModel):
    id: UUID
    name: str
    parent_department_id: Optional[UUID] = None
    head_employee_id: Optional[UUID] = None
    status: str

    model_config = {"from_attributes": True}


# ── AssetCategory ──────────────────────────────────────────────────────────
class AssetCategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    custom_fields: dict[str, Any] = Field(default_factory=dict)


class AssetCategoryUpdate(BaseModel):
    name: Optional[str] = None
    custom_fields: Optional[dict[str, Any]] = None


class AssetCategoryOut(BaseModel):
    id: UUID
    name: str
    custom_fields: dict[str, Any]

    model_config = {"from_attributes": True}


# ── Employee directory ─────────────────────────────────────────────────────
class EmployeeCreate(BaseModel):
    """Admin-only employee creation (different from self-signup)."""
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    department_id: Optional[UUID] = None
    role: str = "Employee"


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    department_id: Optional[UUID] = None
    status: Optional[str] = None


class RolePromotionRequest(BaseModel):
    """Admin-only endpoint to change an employee's role."""
    role: str = Field(..., pattern="^(Employee|DepartmentHead|AssetManager|Admin)$")


class EmployeeOut(BaseModel):
    id: UUID
    name: str
    email: str
    department_id: Optional[UUID] = None
    role: str
    status: str

    model_config = {"from_attributes": True}
