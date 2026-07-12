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
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_asset_manager, require_authenticated, get_current_user
from app.db import get_db
from app.schemas.allocations import (
    AllocationCreate,
    AllocationOut,
    ReturnRequest,
    TransferRequestApproval,
    TransferRequestCreate,
    TransferRequestOut,
)
from app.models.allocation import Allocation
from app.models.activity_log import ActivityLog
from app.models.asset import Asset
from app.models.employee import Employee
from app.models.transfer_request import TransferRequest
from app.services.notifications import create_notification

router = APIRouter(prefix="/allocations", tags=["allocations"])

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

# ── Allocations ────────────────────────────────────────────────────────────

@router.get("/", response_model=List[AllocationOut])
async def list_allocations(db: AsyncSession = Depends(get_db), _=Depends(require_authenticated)):
    result = await db.scalars(select(Allocation))
    allocs = result.all()
    
    out_list = []
    today = date.today()
    for a in allocs:
        # Compute is_overdue dynamically
        is_overdue = False
        if a.expected_return_date and a.actual_return_date is None:
            if a.expected_return_date < today and a.status == 'Active':
                is_overdue = True
                
        # SQLAlchemy models converted to Pydantic natively, but we need to inject computed fields
        a_dict = {
            "id": a.id,
            "asset_id": a.asset_id,
            "employee_id": a.employee_id,
            "department_id": a.department_id,
            "allocated_date": a.allocated_date,
            "expected_return_date": a.expected_return_date,
            "actual_return_date": a.actual_return_date,
            "return_condition_notes": None, # not on model scaffold, but on schema
            "status": a.status,
            "is_overdue": is_overdue
        }
        out_list.append(a_dict)
        
    return out_list


@router.post("/", response_model=AllocationOut, status_code=201, dependencies=[Depends(require_asset_manager)])
async def allocate_asset(body: AllocationCreate, db: AsyncSession = Depends(get_db)):
    # CONFLICT CHECK: AIRTIGHT ROW LOCK
    # We lock the asset row to prevent concurrent allocations to the same asset
    result = await db.execute(
        select(Asset).where(Asset.id == body.asset_id).with_for_update()
    )
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    if asset.status in ("Allocated", "Reserved"):
        # Fetch current holder to return in the 409 body
        alloc_res = await db.execute(
            select(Allocation)
            .where(Allocation.asset_id == asset.id)
            .where(Allocation.status == 'Active')
        )
        current_alloc = alloc_res.scalar_one_or_none()
        
        holder_name = "Unknown"
        if current_alloc and current_alloc.employee_id:
            emp = await db.get(Employee, current_alloc.employee_id)
            holder_name = emp.name if emp else "Unknown Employee"
            
        await db.rollback()
        raise HTTPException(status_code=409, detail={
            "error": "AssetAlreadyAllocated",
            "message": f"Currently held by {holder_name}",
            "current_allocation_id": str(current_alloc.id) if current_alloc else None
        })
        
    if asset.status not in ("Available",):
        await db.rollback()
        raise HTTPException(status_code=422, detail="Asset is not in an allocatable state.")
        
    # Proceed with allocation
    asset.status = "Allocated"
    new_alloc = Allocation(
        asset_id=body.asset_id,
        employee_id=body.employee_id,
        department_id=body.department_id,
        allocated_date=body.allocated_date,
        expected_return_date=body.expected_return_date,
        status="Active"
    )
    db.add(new_alloc)

    # ── Notification: AssetAssigned ────────────────────────────────────────
    await create_notification(
        db=db,
        user_id=body.employee_id,
        type_="AssetAssigned",
        message=f"Asset '{asset.name}' has been allocated to you.",
        entity_type="Allocation",
        entity_id=str(new_alloc.id),
    )

    # ── Activity log ───────────────────────────────────────────────────────
    db.add(ActivityLog(
        user_id=body.employee_id,
        action="asset_allocated",
        entity_type="Allocation",
        entity_id=str(new_alloc.id),
        details={"asset_id": str(body.asset_id), "asset_name": asset.name},
    ))

    await db.commit()
    await db.refresh(new_alloc)

    # Return mapping
    return {
        "id": new_alloc.id,
        "asset_id": new_alloc.asset_id,
        "employee_id": new_alloc.employee_id,
        "department_id": new_alloc.department_id,
        "allocated_date": new_alloc.allocated_date,
        "expected_return_date": new_alloc.expected_return_date,
        "actual_return_date": new_alloc.actual_return_date,
        "status": new_alloc.status,
        "is_overdue": False
    }


@router.get("/{allocation_id}", response_model=AllocationOut)
async def get_allocation(allocation_id: uuid.UUID, db: AsyncSession = Depends(get_db), _=Depends(require_authenticated)):
    a = await db.get(Allocation, allocation_id)
    if not a:
        raise HTTPException(status_code=404, detail="Allocation not found")
        
    is_overdue = False
    if a.expected_return_date and a.actual_return_date is None:
        if a.expected_return_date < date.today() and a.status == 'Active':
            is_overdue = True
            
    return {
        "id": a.id, "asset_id": a.asset_id, "employee_id": a.employee_id, "department_id": a.department_id,
        "allocated_date": a.allocated_date, "expected_return_date": a.expected_return_date,
        "actual_return_date": a.actual_return_date, "status": a.status, "is_overdue": is_overdue
    }


@router.post("/{allocation_id}/return", response_model=AllocationOut)
async def return_asset(allocation_id: uuid.UUID, body: ReturnRequest, db: AsyncSession = Depends(get_db), _=Depends(require_authenticated)):
    alloc = await db.get(Allocation, allocation_id)
    if not alloc:
        raise HTTPException(status_code=404, detail="Allocation not found")
    if alloc.status != "Active":
        raise HTTPException(status_code=400, detail="Allocation is not active")

    asset = await db.get(Asset, alloc.asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Detect overdue BEFORE changing status
    was_overdue = (
        alloc.expected_return_date is not None
        and alloc.expected_return_date < date.today()
    )

    alloc.status = "Returned"
    alloc.actual_return_date = body.actual_return_date
    asset.status = "Available"

    # ── Notification: OverdueReturnAlert (only if actually overdue) ────────
    if was_overdue:
        await create_notification(
            db=db,
            user_id=alloc.employee_id,
            type_="OverdueReturnAlert",
            message=(
                f"Asset '{asset.name}' was returned late "
                f"(expected {alloc.expected_return_date}, returned {body.actual_return_date})."
            ),
            entity_type="Allocation",
            entity_id=str(alloc.id),
        )

    # ── Activity log ───────────────────────────────────────────────────────
    db.add(ActivityLog(
        user_id=alloc.employee_id,
        action="asset_returned",
        entity_type="Allocation",
        entity_id=str(alloc.id),
        details={"asset_id": str(alloc.asset_id), "was_overdue": was_overdue},
    ))

    await db.commit()
    await db.refresh(alloc)

    return {
        "id": alloc.id, "asset_id": alloc.asset_id, "employee_id": alloc.employee_id, "department_id": alloc.department_id,
        "allocated_date": alloc.allocated_date, "expected_return_date": alloc.expected_return_date,
        "actual_return_date": alloc.actual_return_date, "status": alloc.status, "is_overdue": False
    }


# ── Transfer Requests ──────────────────────────────────────────────────────

@router.get("/transfers", response_model=List[TransferRequestOut])
async def list_transfers(db: AsyncSession = Depends(get_db), _=Depends(require_authenticated)):
    result = await db.scalars(select(TransferRequest))
    return result.all()


@router.post("/transfers", response_model=TransferRequestOut, status_code=201)
async def create_transfer_request(body: TransferRequestCreate, db: AsyncSession = Depends(get_db), user: Employee = Depends(get_current_employee)):
    alloc = await db.get(Allocation, body.allocation_id)
    if not alloc:
        raise HTTPException(status_code=404, detail="Target allocation not found")
    if alloc.status != "Active":
        raise HTTPException(status_code=400, detail="Can only request transfers for Active allocations")
        
    tr = TransferRequest(
        allocation_id=body.allocation_id,
        requested_by=user.id,
        target_employee_id=body.target_employee_id,
        target_department_id=body.target_department_id,
        reason=body.reason,
        status="Requested"
    )
    
    db.add(tr)
    await db.commit()
    await db.refresh(tr)
    return tr


@router.get("/transfers/{transfer_id}", response_model=TransferRequestOut)
async def get_transfer(transfer_id: uuid.UUID, db: AsyncSession = Depends(get_db), _=Depends(require_authenticated)):
    tr = await db.get(TransferRequest, transfer_id)
    if not tr:
        raise HTTPException(status_code=404, detail="Transfer Request not found")
    return tr


@router.post("/transfers/{transfer_id}/approve", response_model=TransferRequestOut, dependencies=[Depends(require_asset_manager)])
async def approve_transfer(transfer_id: uuid.UUID, body: TransferRequestApproval, db: AsyncSession = Depends(get_db)):
    tr = await db.get(TransferRequest, transfer_id)
    if not tr:
        raise HTTPException(status_code=404, detail="Transfer Request not found")
        
    if body.action == "reject":
        tr.status = "Rejected"

        # ── Activity log ───────────────────────────────────────────────────
        db.add(ActivityLog(
            user_id=tr.requested_by,
            action="transfer_rejected",
            entity_type="TransferRequest",
            entity_id=str(tr.id),
        ))

        await db.commit()
        await db.refresh(tr)
        return tr
        
    if body.action == "approve":
        if tr.status != "Requested":
            raise HTTPException(status_code=400, detail="Transfer must be Requested to approve")

        old_alloc = await db.get(Allocation, tr.allocation_id)
        if not old_alloc:
            raise HTTPException(status_code=404, detail="Linked allocation not found")

        asset = await db.get(Asset, old_alloc.asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        # Atomic transfer operation
        tr.status = "Approved"
        old_alloc.status = "Transferred"
        old_alloc.actual_return_date = date.today()

        new_alloc = Allocation(
            asset_id=old_alloc.asset_id,
            employee_id=tr.target_employee_id,
            department_id=tr.target_department_id,
            allocated_date=date.today(),
            status="Active"
        )
        db.add(new_alloc)

        # ── Notification: TransferApproved → requester ─────────────────────
        if tr.requested_by:
            await create_notification(
                db=db,
                user_id=tr.requested_by,
                type_="TransferApproved",
                message=(
                    f"Your transfer request for asset '{asset.name}' has been approved."
                ),
                entity_type="TransferRequest",
                entity_id=str(tr.id),
            )

        # ── Notification: AssetAssigned → the new holder ───────────────────
        if tr.target_employee_id:
            await create_notification(
                db=db,
                user_id=tr.target_employee_id,
                type_="AssetAssigned",
                message=f"Asset '{asset.name}' has been transferred and allocated to you.",
                entity_type="Allocation",
                entity_id=str(new_alloc.id),
            )

        # ── Activity log ───────────────────────────────────────────────────
        db.add(ActivityLog(
            user_id=tr.requested_by,
            action="transfer_approved",
            entity_type="TransferRequest",
            entity_id=str(tr.id),
            details={
                "asset_id": str(old_alloc.asset_id),
                "asset_name": asset.name,
                "from_allocation": str(old_alloc.id),
                "to_employee": str(tr.target_employee_id),
            },
        ))

        # Asset remains Allocated
        await db.commit()
        await db.refresh(tr)
        return tr
