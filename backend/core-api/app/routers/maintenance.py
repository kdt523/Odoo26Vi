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
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_asset_manager, require_authenticated
from app.db import get_db
from app.schemas.maintenance import (
    MaintenanceApproval,
    MaintenanceRequestCreate,
    MaintenanceRequestOut,
    MaintenanceStatusUpdate,
    TechnicianAssignment,
)

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@router.get("/", response_model=List[MaintenanceRequestOut])
async def list_maintenance_requests(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_authenticated),
    status_filter: Optional[str] = Query(None, alias="status"),
    asset_id: Optional[uuid.UUID] = Query(None),
    priority: Optional[str] = Query(None),
):
    # TODO: employees see only their own requests; managers see all
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/", response_model=MaintenanceRequestOut, status_code=201)
async def raise_maintenance_request(body: MaintenanceRequestCreate,
                                     db: AsyncSession = Depends(get_db),
                                     current_user=Depends(require_authenticated)):
    """
    Any employee can raise a maintenance request.
    TODO: insert MaintenanceRequest(raised_by=current_user.id, status='Pending')
    TODO: write Notification to all AssetManagers (type=... TODO define notification type)
    TODO: write ActivityLog entry
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/{request_id}", response_model=MaintenanceRequestOut)
async def get_maintenance_request(request_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                                   _=Depends(require_authenticated)):
    # TODO: fetch by id → 404
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/{request_id}/approve", response_model=MaintenanceRequestOut,
             dependencies=[Depends(require_asset_manager)])
async def approve_maintenance(request_id: uuid.UUID, body: MaintenanceApproval,
                               db: AsyncSession = Depends(get_db)):
    """
    Approve or reject a Pending maintenance request.
    TODO (approve): set status = 'Approved', approved_by = current_user.id
    TODO (approve): set asset.status = 'UnderMaintenance'
    TODO: write Notification to requester (type='MaintenanceApproved'/'MaintenanceRejected')
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/{request_id}/assign-technician", response_model=MaintenanceRequestOut,
             dependencies=[Depends(require_asset_manager)])
async def assign_technician(request_id: uuid.UUID, body: TechnicianAssignment,
                             db: AsyncSession = Depends(get_db)):
    """
    TODO: verify request.status == 'Approved'
    TODO: set request.technician = body.technician, status = 'TechnicianAssigned'
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/{request_id}/update-status", response_model=MaintenanceRequestOut,
             dependencies=[Depends(require_asset_manager)])
async def update_maintenance_status(request_id: uuid.UUID, body: MaintenanceStatusUpdate,
                                     db: AsyncSession = Depends(get_db)):
    """
    Move a request to InProgress or Resolved.
    TODO (Resolved): set asset.status = 'Available' (or back to 'Allocated' if it was allocated)
    TODO: write ActivityLog entry
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")
