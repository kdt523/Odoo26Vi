"""
app/schemas/allocations.py — Pydantic schemas for the allocations router.
Covers: Allocation, TransferRequest, Return flow.
"""

from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Allocation ─────────────────────────────────────────────────────────────
class AllocationCreate(BaseModel):
    asset_id: UUID
    employee_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    allocated_date: date
    expected_return_date: Optional[date] = None
    # TODO (allocations router): before inserting, check asset.status != 'Allocated'
    #      If Allocated, raise 409 and instruct client to use TransferRequest instead.


class AllocationOut(BaseModel):
    id: UUID
    asset_id: UUID
    employee_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    allocated_date: date
    expected_return_date: Optional[date] = None
    actual_return_date: Optional[date] = None
    return_condition_notes: Optional[str] = None
    status: str
    is_overdue: bool = False

    model_config = {"from_attributes": True}


# ── Return flow ────────────────────────────────────────────────────────────
class ReturnRequest(BaseModel):
    actual_return_date: date
    return_condition_notes: Optional[str] = None

class ReturnInitiateRequest(BaseModel):
    condition_check_in_notes: Optional[str] = None

class ReturnRejectRequest(BaseModel):
    reason: str


# ── TransferRequest ────────────────────────────────────────────────────────
class TransferRequestCreate(BaseModel):
    allocation_id: UUID
    target_employee_id: Optional[UUID] = None
    target_department_id: Optional[UUID] = None
    reason: Optional[str] = None


class TransferRequestApproval(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")


class TransferRequestOut(BaseModel):
    id: UUID
    allocation_id: UUID
    requested_by: Optional[UUID] = None
    approved_by: Optional[UUID] = None
    target_employee_id: Optional[UUID] = None
    target_department_id: Optional[UUID] = None
    reason: Optional[str] = None
    status: str

    model_config = {"from_attributes": True}
