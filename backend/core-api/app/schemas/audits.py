"""
app/schemas/audits.py — Pydantic schemas for the audits router.
"""

from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── AuditCycle ─────────────────────────────────────────────────────────────
class AuditCycleCreate(BaseModel):
    scope_department_id: Optional[UUID] = None
    location: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None


class AuditCycleUpdate(BaseModel):
    end_date: Optional[date] = None
    status: Optional[str] = None


class AuditCycleOut(BaseModel):
    id: UUID
    scope_department_id: Optional[UUID] = None
    location: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    status: str

    model_config = {"from_attributes": True}


# ── Auditor assignment ─────────────────────────────────────────────────────
class AuditorAssignment(BaseModel):
    employee_ids: list[UUID] = Field(..., min_length=1)


# ── AuditItem ──────────────────────────────────────────────────────────────
class AuditItemMark(BaseModel):
    asset_id: UUID
    result: str = Field(..., pattern="^(Verified|Missing|Damaged)$")
    notes: Optional[str] = None


class AuditItemOut(BaseModel):
    id: UUID
    audit_cycle_id: UUID
    asset_id: UUID
    result: Optional[str] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}
