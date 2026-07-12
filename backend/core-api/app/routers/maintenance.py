"""
app/routers/maintenance.py — Maintenance request router.

Status workflow:
  Pending → Approved → TechnicianAssigned → InProgress → Resolved
  Pending → Rejected

Endpoints:
  GET    /                      — List maintenance requests (filterable)
  POST   /                      — Raise a new maintenance request (any Employee)
  GET    /{id}                   — Request detail
  POST   /{id}/approve           — Approve or reject (AssetManager)
  POST   /{id}/assign-technician — Assign technician (AssetManager)
  POST   /{id}/update-status     — Move to InProgress or Resolved (AssetManager/technician)
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_asset_manager, require_authenticated, get_current_user
from app.db import get_db
from app.schemas.maintenance import (
    MaintenanceRequestCreate,
    MaintenanceRequestOut,
    TechnicianAssignment,
)
from app.models.maintenance_request import MaintenanceRequest
from app.models.asset import Asset
from app.models.employee import Employee

router = APIRouter(prefix="/maintenance", tags=["maintenance"])

async def get_current_employee(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if isinstance(current_user, dict):
        try:
            user_id = uuid.UUID(current_user.get("sub"))
        except (ValueError, TypeError):
            raise HTTPException(status_code=401, detail="Invalid token subject")
        result = await db.execute(select(Employee).where(Employee.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    return current_user

@router.get("/", response_model=List[MaintenanceRequestOut])
async def list_maintenance_requests(
    db: AsyncSession = Depends(get_db),
    user: Employee = Depends(get_current_employee),
    status_filter: Optional[str] = Query(None, alias="status"),
    asset_id: Optional[uuid.UUID] = Query(None),
    priority: Optional[str] = Query(None),
):
    query = select(MaintenanceRequest)
    
    # Employees only see their own requests; managers see all
    if user.role == "Employee":
        query = query.where(MaintenanceRequest.raised_by == user.id)
        
    if status_filter:
        query = query.where(MaintenanceRequest.status == status_filter)
    if asset_id:
        query = query.where(MaintenanceRequest.asset_id == asset_id)
    if priority:
        query = query.where(MaintenanceRequest.priority == priority)
        
    result = await db.scalars(query)
    return result.all()


@router.post("/", response_model=MaintenanceRequestOut, status_code=201)
async def raise_maintenance_request(
    body: MaintenanceRequestCreate,
    db: AsyncSession = Depends(get_db),
    user: Employee = Depends(get_current_employee)
):
    # Verify asset exists
    asset = await db.get(Asset, body.asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    req = MaintenanceRequest(
        asset_id=body.asset_id,
        raised_by=user.id,
        issue_description=body.issue_description,
        priority=body.priority,
        photo_ref=body.photo_ref,
        status="Pending"
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)
    return req


@router.get("/{request_id}", response_model=MaintenanceRequestOut)
async def get_maintenance_request(
    request_id: uuid.UUID, 
    db: AsyncSession = Depends(get_db),
    user: Employee = Depends(get_current_employee)
):
    req = await db.get(MaintenanceRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    if user.role == "Employee" and req.raised_by != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this request")
    return req


@router.post("/{request_id}/approve", response_model=MaintenanceRequestOut, dependencies=[Depends(require_asset_manager)])
async def approve_maintenance(
    request_id: uuid.UUID, 
    db: AsyncSession = Depends(get_db),
    user: Employee = Depends(get_current_employee)
):
    req = await db.get(MaintenanceRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    if req.status != "Pending":
        raise HTTPException(status_code=400, detail="Only Pending requests can be approved")
        
    asset = await db.get(Asset, req.asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Linked asset not found")
        
    # Atomic update
    req.status = "Approved"
    req.approved_by = user.id
    asset.status = "UnderMaintenance"
    
    await db.commit()
    await db.refresh(req)
    return req


@router.post("/{request_id}/reject", response_model=MaintenanceRequestOut, dependencies=[Depends(require_asset_manager)])
async def reject_maintenance(
    request_id: uuid.UUID, 
    db: AsyncSession = Depends(get_db),
    user: Employee = Depends(get_current_employee)
):
    req = await db.get(MaintenanceRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    if req.status != "Pending":
        raise HTTPException(status_code=400, detail="Only Pending requests can be rejected")
        
    req.status = "Rejected"
    req.approved_by = user.id
    await db.commit()
    await db.refresh(req)
    return req


@router.post("/{request_id}/assign-technician", response_model=MaintenanceRequestOut, dependencies=[Depends(require_asset_manager)])
async def assign_technician(
    request_id: uuid.UUID, 
    body: TechnicianAssignment,
    db: AsyncSession = Depends(get_db)
):
    req = await db.get(MaintenanceRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    if req.status != "Approved":
        raise HTTPException(status_code=400, detail="Request must be Approved before assigning a technician")
        
    req.status = "TechnicianAssigned"
    req.technician = body.technician
    await db.commit()
    await db.refresh(req)
    return req


@router.post("/{request_id}/start", response_model=MaintenanceRequestOut, dependencies=[Depends(require_asset_manager)])
async def start_maintenance(
    request_id: uuid.UUID, 
    db: AsyncSession = Depends(get_db)
):
    req = await db.get(MaintenanceRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    if req.status != "TechnicianAssigned":
        raise HTTPException(status_code=400, detail="Request must have a TechnicianAssigned before starting")
        
    req.status = "InProgress"
    await db.commit()
    await db.refresh(req)
    return req


@router.post("/{request_id}/resolve", response_model=MaintenanceRequestOut, dependencies=[Depends(require_asset_manager)])
async def resolve_maintenance(
    request_id: uuid.UUID, 
    db: AsyncSession = Depends(get_db)
):
    req = await db.get(MaintenanceRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    if req.status != "InProgress":
        raise HTTPException(status_code=400, detail="Request must be InProgress before resolving")
        
    asset = await db.get(Asset, req.asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Linked asset not found")
        
    # Atomic update
    req.status = "Resolved"
    
    # Ideally, we should restore it to 'Allocated' if it was allocated, but Issue #34 explicitly says:
    # "flips Asset status back to Available in the same transaction."
    asset.status = "Available"
    
    await db.commit()
    await db.refresh(req)
    return req
