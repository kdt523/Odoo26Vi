"""
app/routers/allocations.py — Allocation & transfer router.

Endpoints:
  Allocations:
    GET    /                           — List allocations (filterable)
    POST   /                           — Allocate an asset  ← CONFLICT CHECK HERE
    GET    /{id}                        — Allocation detail
    POST   /{id}/return                 — Initiate return flow

  Transfer Requests:
    GET    /transfers                   — List transfer requests
    POST   /transfers                   — Create transfer request
    GET    /transfers/{id}              — Transfer request detail
    POST   /transfers/{id}/approve      — Approve / reject transfer (AssetManager/DeptHead)
"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_asset_manager, require_authenticated
from app.db import get_db
from app.schemas.allocations import (
    AllocationCreate,
    AllocationOut,
    ReturnRequest,
    TransferRequestApproval,
    TransferRequestCreate,
    TransferRequestOut,
)

router = APIRouter(prefix="/allocations", tags=["allocations"])


# ── Allocations ────────────────────────────────────────────────────────────

@router.get("/", response_model=List[AllocationOut])
async def list_allocations(db: AsyncSession = Depends(get_db), _=Depends(require_authenticated)):
    # TODO: filterable by asset_id, employee_id, department_id, status
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/", response_model=AllocationOut, status_code=201,
             dependencies=[Depends(require_asset_manager)])
async def allocate_asset(body: AllocationCreate, db: AsyncSession = Depends(get_db)):
    """
    Allocate an asset to an employee or department.

    ─────────────────────────────────────────────────
    TODO: CONFLICT CHECK — implement before inserting:
      1. Fetch the Asset by body.asset_id.
      2. If asset.status == 'Allocated':
           raise HTTPException(409, detail={
             "error": "AssetAlreadyAllocated",
             "message": "Asset is currently allocated. Create a TransferRequest instead.",
             "current_allocation_id": "<id>"
           })
      3. If asset.status not in ('Available', 'Reserved'):
           raise HTTPException(422, detail="Asset is not in an allocatable state.")
    ─────────────────────────────────────────────────

    After passing conflict check:
      TODO: set asset.status = 'Allocated'
      TODO: insert Allocation(status='Active', ...)
      TODO: write ActivityLog entry
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/{allocation_id}", response_model=AllocationOut)
async def get_allocation(allocation_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                          _=Depends(require_authenticated)):
    # TODO: fetch by id → 404
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/{allocation_id}/return", response_model=AllocationOut)
async def return_asset(allocation_id: uuid.UUID, body: ReturnRequest,
                        db: AsyncSession = Depends(get_db), _=Depends(require_authenticated)):
    """
    Initiate return of an allocated asset.
    TODO: set allocation.status = 'Returned', allocation.actual_return_date = body.actual_return_date
    TODO: set asset.status = 'Available'
    TODO: write ActivityLog entry
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


# ── Transfer Requests ──────────────────────────────────────────────────────

@router.get("/transfers", response_model=List[TransferRequestOut])
async def list_transfers(db: AsyncSession = Depends(get_db), _=Depends(require_authenticated)):
    # TODO: filterable by status, allocation_id, requested_by
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/transfers", response_model=TransferRequestOut, status_code=201)
async def create_transfer_request(body: TransferRequestCreate, db: AsyncSession = Depends(get_db),
                                   current_user=Depends(require_authenticated)):
    """
    Create a transfer request for an already-allocated asset.
    TODO: verify allocation exists and is Active
    TODO: set allocation.status = 'TransferPending'
    TODO: insert TransferRequest
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/transfers/{transfer_id}", response_model=TransferRequestOut)
async def get_transfer(transfer_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                        _=Depends(require_authenticated)):
    # TODO: fetch by id → 404
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/transfers/{transfer_id}/approve", response_model=TransferRequestOut,
             dependencies=[Depends(require_asset_manager)])
async def approve_transfer(transfer_id: uuid.UUID, body: TransferRequestApproval,
                            db: AsyncSession = Depends(get_db)):
    """
    Approve or reject a transfer request.
    TODO (approve path):
      - set transfer.status = 'Approved'
      - close existing allocation (status = 'Transferred')
      - create new Allocation for target employee/department
      - asset.status remains 'Allocated'
    TODO (reject path):
      - set transfer.status = 'Rejected'
      - revert allocation.status = 'Active'
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")
