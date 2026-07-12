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
    auditor_ids: Optional[list[UUID]] = None


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
    result: str = Field(..., pattern="^(Verified|Missing|Damaged)$")
    notes: Optional[str] = None


class AuditItemOut(BaseModel):
    id: UUID
    audit_cycle_id: UUID
    asset_id: UUID
    result: Optional[str] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Detailed Cycle ─────────────────────────────────────────────────────────

# We need to import AssetOut if not already done, but to avoid circular imports, we can define a simplified version or use forward references. 
# Better yet, since we need Asset data, let's define a minimal Asset schema here or assume the router will assemble it.
# Assuming we can just use a dictionary or import AssetOut from app.schemas.assets.
# For now, let's define a simple asset representation for the detail view.

class AuditCycleAssetOut(BaseModel):
    id: UUID
    name: str
    asset_tag: str
    department_id: Optional[UUID] = None
    location: Optional[str] = None
    status: str

    model_config = {"from_attributes": True}

class AuditCycleDetailItemOut(BaseModel):
    asset: AuditCycleAssetOut
    audit_item: Optional[AuditItemOut] = None

class AuditCycleDetailOut(BaseModel):
    cycle: AuditCycleOut
    assets: list[AuditCycleDetailItemOut]


# ── Close Response ─────────────────────────────────────────────────────────

class AuditDiscrepancyReportItem(BaseModel):
    asset_id: UUID
    asset_name: str
    asset_tag: str
    result: str
    notes: Optional[str] = None

class AuditCycleCloseOut(BaseModel):
    cycle: AuditCycleOut
    discrepancy_report: list[AuditDiscrepancyReportItem]
