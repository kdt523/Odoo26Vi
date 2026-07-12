"""
app/routers/audits.py — Audit cycle router.

Endpoints:
  GET    /                      — List audit cycles
  POST   /                      — Create audit cycle (AssetManager)
  GET    /{id}                   — Cycle detail + items summary
  PUT    /{id}                   — Update cycle metadata
  POST   /{id}/auditors          — Assign auditors to cycle
  DELETE /{id}/auditors/{emp_id} — Remove auditor
  GET    /{id}/items             — List audit items in cycle
  POST   /{id}/items             — Mark asset as Verified/Missing/Damaged
  POST   /{id}/close             — Close an active audit cycle
"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_asset_manager, require_authenticated
from app.db import get_db
from app.schemas.audits import (
    AuditCycleCreate,
    AuditCycleOut,
    AuditCycleUpdate,
    AuditItemMark,
    AuditItemOut,
    AuditorAssignment,
)

router = APIRouter(prefix="/audits", tags=["audits"])


@router.get("/", response_model=List[AuditCycleOut])
async def list_audit_cycles(db: AsyncSession = Depends(get_db), _=Depends(require_authenticated)):
    # TODO: filter by status, department
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/", response_model=AuditCycleOut, status_code=201,
             dependencies=[Depends(require_asset_manager)])
async def create_audit_cycle(body: AuditCycleCreate, db: AsyncSession = Depends(get_db)):
    # TODO: insert AuditCycle(status='Draft')
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/{cycle_id}", response_model=AuditCycleOut)
async def get_audit_cycle(cycle_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                           _=Depends(require_authenticated)):
    # TODO: fetch by id → 404; include item counts
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.put("/{cycle_id}", response_model=AuditCycleOut,
            dependencies=[Depends(require_asset_manager)])
async def update_audit_cycle(cycle_id: uuid.UUID, body: AuditCycleUpdate,
                              db: AsyncSession = Depends(get_db)):
    # TODO: patch non-None fields
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/{cycle_id}/auditors", response_model=AuditCycleOut,
             dependencies=[Depends(require_asset_manager)])
async def assign_auditors(cycle_id: uuid.UUID, body: AuditorAssignment,
                           db: AsyncSession = Depends(get_db)):
    """
    Assign employees as auditors to a cycle.
    TODO: insert rows into audit_cycle_auditors join table.
    TODO: skip duplicates (upsert or pre-filter).
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.delete("/{cycle_id}/auditors/{employee_id}", status_code=204,
               dependencies=[Depends(require_asset_manager)])
async def remove_auditor(cycle_id: uuid.UUID, employee_id: uuid.UUID,
                          db: AsyncSession = Depends(get_db)):
    # TODO: delete from audit_cycle_auditors where cycle_id AND employee_id match
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/{cycle_id}/items", response_model=List[AuditItemOut])
async def list_audit_items(cycle_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                            _=Depends(require_authenticated)):
    # TODO: fetch all AuditItems for cycle_id
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/{cycle_id}/items", response_model=AuditItemOut, status_code=201)
async def mark_audit_item(cycle_id: uuid.UUID, body: AuditItemMark,
                           db: AsyncSession = Depends(get_db),
                           _=Depends(require_authenticated)):
    """
    Record the physical verification result for one asset within this cycle.
    TODO: upsert AuditItem(audit_cycle_id=cycle_id, asset_id=body.asset_id, result=body.result)
    TODO (Missing/Damaged): write Notification(type='AuditDiscrepancyFlagged') to AssetManagers
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/{cycle_id}/close", response_model=AuditCycleOut,
             dependencies=[Depends(require_asset_manager)])
async def close_audit_cycle(cycle_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Close an active audit cycle.
    TODO: verify cycle.status == 'Active'
    TODO: set cycle.status = 'Closed', cycle.end_date = today
    TODO: write ActivityLog entry
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")
