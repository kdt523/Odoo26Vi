"""
app/schemas/maintenance.py — Pydantic schemas for the maintenance router.
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MaintenanceRequestCreate(BaseModel):
    asset_id: UUID
    issue_description: str = Field(..., min_length=1)
    priority: str = Field(default="Medium", pattern="^(Low|Medium|High|Critical)$")
    photo_ref: Optional[str] = None


class TechnicianAssignment(BaseModel):
    technician: str = Field(..., min_length=1, max_length=255)


class MaintenanceRequestOut(BaseModel):
    id: UUID
    asset_id: UUID
    raised_by: Optional[UUID] = None
    issue_description: str
    priority: str
    photo_ref: Optional[str] = None
    approved_by: Optional[UUID] = None
    technician: Optional[str] = None
    status: str

    model_config = {"from_attributes": True}
