"""
app/routers/audits.py — Audit cycle router (fully implemented).

Status flow:
  Draft → Active → Closed

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
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_asset_manager, require_authenticated
from app.db import get_db
from app.services.activity_log import log_activity
from app.models.audit_cycle import AuditCycle, audit_cycle_auditors
from app.models.audit_item import AuditItem
from app.models.employee import Employee
from app.schemas.audits import (
    AuditCycleCreate,
    AuditCycleOut,
    AuditCycleUpdate,
    AuditItemMark,
    AuditItemOut,
    AuditorAssignment,
)
from app.services.notifications import create_notification

router = APIRouter(prefix="/audits", tags=["audits"])


async def _resolve_user(current_user=Depends(get_current_user)) -> Employee:
    return current_user


# ── GET / ──────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[AuditCycleOut])
async def list_audit_cycles(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_authenticated),
    status_filter: Optional[str] = Query(None, alias="status"),
    department_id: Optional[uuid.UUID] = Query(None),
):
    stmt = select(AuditCycle)
    if status_filter:
        stmt = stmt.where(AuditCycle.status == status_filter)
    if department_id:
        stmt = stmt.where(AuditCycle.department_id == department_id)
    stmt = stmt.order_by(AuditCycle.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


# ── POST / ─────────────────────────────────────────────────────────────────

@router.post("/", response_model=AuditCycleOut, status_code=201,
             dependencies=[Depends(require_asset_manager)])
async def create_audit_cycle(
    body: AuditCycleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(_resolve_user),
):
    cycle = AuditCycle(
        scope_department_id=body.scope_department_id,
        location=body.location,
        start_date=body.start_date,
        end_date=body.end_date,
        status="Draft",
    )
    db.add(cycle)
    await db.flush()

    log_activity(
        db,
        current_user.id,
        "audit_cycle_created",
        "AuditCycle",
        str(cycle.id),
        details={"scope_department_id": str(body.scope_department_id) if body.scope_department_id else None},
    )

    await db.commit()
    await db.refresh(cycle)
    return cycle


# ── GET /{cycle_id} ────────────────────────────────────────────────────────

@router.get("/{cycle_id}", response_model=AuditCycleOut)
async def get_audit_cycle(
    cycle_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_authenticated),
):
    cycle = await db.get(AuditCycle, cycle_id)
    if not cycle:
        raise HTTPException(status_code=404, detail="Audit cycle not found")
    return cycle


# ── PUT /{cycle_id} ────────────────────────────────────────────────────────

@router.put("/{cycle_id}", response_model=AuditCycleOut,
            dependencies=[Depends(require_asset_manager)])
async def update_audit_cycle(
    cycle_id: uuid.UUID,
    body: AuditCycleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(_resolve_user),
):
    cycle = await db.get(AuditCycle, cycle_id)
    if not cycle:
        raise HTTPException(status_code=404, detail="Audit cycle not found")
    if cycle.status == "Closed":
        raise HTTPException(status_code=400, detail="Cannot update a closed audit cycle")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(cycle, field, value)

    log_activity(db, current_user.id, "audit_cycle_updated", "AuditCycle", str(cycle.id), details={"updated_fields": list(update_data.keys())})

    await db.commit()
    await db.refresh(cycle)
    return cycle


# ── POST /{cycle_id}/auditors ──────────────────────────────────────────────

@router.post("/{cycle_id}/auditors", response_model=AuditCycleOut,
             dependencies=[Depends(require_asset_manager)])
async def assign_auditors(
    cycle_id: uuid.UUID,
    body: AuditorAssignment,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(_resolve_user),
):
    """Assign employees as auditors; skips duplicates."""
    cycle = await db.get(AuditCycle, cycle_id)
    if not cycle:
        raise HTTPException(status_code=404, detail="Audit cycle not found")

    # Fetch existing auditor IDs to avoid duplicates
    existing_stmt = select(audit_cycle_auditors.c.employee_id).where(
        audit_cycle_auditors.c.audit_cycle_id == cycle_id
    )
    existing_result = await db.execute(existing_stmt)
    existing_ids = {row for row in existing_result.scalars()}

    for emp_id in body.employee_ids:
        if emp_id not in existing_ids:
            await db.execute(
                audit_cycle_auditors.insert().values(
                    audit_cycle_id=cycle_id, employee_id=emp_id
                )
            )

    log_activity(db, current_user.id, "auditors_assigned", "AuditCycle", str(cycle.id), details={"auditor_ids": [str(eid) for eid in body.employee_ids]})

    await db.commit()
    await db.refresh(cycle)
    return cycle


# ── DELETE /{cycle_id}/auditors/{employee_id} ─────────────────────────────

@router.delete("/{cycle_id}/auditors/{employee_id}", status_code=204,
               dependencies=[Depends(require_asset_manager)])
async def remove_auditor(
    cycle_id: uuid.UUID,
    employee_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(_resolve_user),
):
    stmt = delete(audit_cycle_auditors).where(
        audit_cycle_auditors.c.audit_cycle_id == cycle_id,
        audit_cycle_auditors.c.employee_id == employee_id,
    )
    await db.execute(stmt)
    log_activity(db, current_user.id, "auditor_removed", "AuditCycle", str(cycle_id), details={"removed_employee_id": str(employee_id)})
    await db.commit()


# ── GET /{cycle_id}/items ──────────────────────────────────────────────────

@router.get("/{cycle_id}/items", response_model=List[AuditItemOut])
async def list_audit_items(
    cycle_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_authenticated),
):
    stmt = select(AuditItem).where(AuditItem.audit_cycle_id == cycle_id)
    result = await db.execute(stmt)
    return result.scalars().all()


# ── POST /{cycle_id}/items ─────────────────────────────────────────────────

@router.post("/{cycle_id}/items", response_model=AuditItemOut, status_code=201)
async def mark_audit_item(
    cycle_id: uuid.UUID,
    body: AuditItemMark,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(_resolve_user),
):
    """
    Record the physical verification result for one asset within this cycle.
    Upserts the AuditItem row.
    Fires AuditDiscrepancyFlagged to all AssetManagers when result is Missing or Damaged.
    """
    cycle = await db.get(AuditCycle, cycle_id)
    if not cycle:
        raise HTTPException(status_code=404, detail="Audit cycle not found")
    if cycle.status not in ("Draft", "Active"):
        raise HTTPException(status_code=400, detail="Audit cycle is not active")

    # Upsert: check if item already exists for this cycle+asset
    existing_stmt = select(AuditItem).where(
        AuditItem.audit_cycle_id == cycle_id,
        AuditItem.asset_id == body.asset_id,
    )
    existing_result = await db.execute(existing_stmt)
    item = existing_result.scalar_one_or_none()

    if item:
        item.result = body.result
        item.notes = body.notes
    else:
        item = AuditItem(
            audit_cycle_id=cycle_id,
            asset_id=body.asset_id,
            result=body.result,
            notes=body.notes,
        )
        db.add(item)

    # ── Notification: AuditDiscrepancyFlagged → all AssetManagers ─────────
    if body.result in ("Missing", "Damaged"):
        managers_stmt = select(Employee).where(
            Employee.role.in_(["AssetManager", "Admin"]),
            Employee.is_deleted.is_(False),
        )
        managers_result = await db.execute(managers_stmt)
        managers = managers_result.scalars().all()

        for mgr in managers:
            await create_notification(
                db=db,
                user_id=mgr.id,
                type_="AuditDiscrepancyFlagged",
                message=(
                    f"Audit discrepancy: asset {body.asset_id} marked as "
                    f"'{body.result}' in cycle (id={cycle_id})."
                ),
                entity_type="AuditItem",
                entity_id=str(item.id),
            )

    # ── Activity log ───────────────────────────────────────────────────────
    await db.flush()
    log_activity(
        db,
        current_user.id,
        "audit_item_marked",
        "AuditItem",
        str(item.id),
        details={
            "cycle_id": str(cycle_id),
            "asset_id": str(body.asset_id),
            "result": body.result,
        },
    )

    await db.commit()
    await db.refresh(item)
    return item


# ── POST /{cycle_id}/close ─────────────────────────────────────────────────

@router.post("/{cycle_id}/close", response_model=AuditCycleOut,
             dependencies=[Depends(require_asset_manager)])
async def close_audit_cycle(
    cycle_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(_resolve_user),
):
    """Close an Active audit cycle."""
    cycle = await db.get(AuditCycle, cycle_id)
    if not cycle:
        raise HTTPException(status_code=404, detail="Audit cycle not found")
    if cycle.status != "Active":
        raise HTTPException(
            status_code=400,
            detail=f"Only Active cycles can be closed (current: {cycle.status})",
        )

    cycle.status = "Closed"
    cycle.end_date = date.today()

    log_activity(
        db,
        current_user.id,
        "audit_cycle_closed",
        "AuditCycle",
        str(cycle.id),
        details={"closed_by": str(current_user.id), "cycle_id": str(cycle.id)},
    )

    await db.commit()
    await db.refresh(cycle)
    return cycle
