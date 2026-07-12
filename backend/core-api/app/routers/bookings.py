"""
app/routers/bookings.py — Resource booking router (fully implemented).

Status flow:
  Upcoming → Ongoing → Completed
  Upcoming → Cancelled

Endpoints:
  GET    /                  — List bookings for current user / asset / department
  POST   /                  — Create booking  ← OVERLAP CHECK enforced
  GET    /calendar          — Calendar view (date-range query)
  GET    /{id}              — Booking detail
  POST   /{id}/cancel       — Cancel a booking
  PUT    /{id}/reschedule   — Reschedule (time window update + overlap re-check)
"""

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_authenticated
from app.db import get_db
from app.services.activity_log import log_activity
from app.models.asset import Asset
from app.models.booking import Booking
from app.models.employee import Employee
from app.schemas.bookings import BookingCreate, BookingOut, BookingUpdate
from app.services.notifications import create_notification

router = APIRouter(prefix="/bookings", tags=["bookings"])


# ── Helper ─────────────────────────────────────────────────────────────────

async def _resolve_user(current_user=Depends(get_current_user)) -> Employee:
    """Always return Employee ORM object."""
    return current_user


async def _check_overlap(
    db: AsyncSession,
    asset_id: uuid.UUID,
    start_time: datetime,
    end_time: datetime,
    exclude_booking_id: Optional[uuid.UUID] = None,
) -> None:
    """
    Raises 409 if any Active/Upcoming/Ongoing booking for the asset overlaps
    the requested [start_time, end_time) window.
    """
    stmt = select(Booking).where(
        Booking.asset_id == asset_id,
        Booking.status.in_(["Upcoming", "Ongoing"]),
        Booking.start_time < end_time,
        Booking.end_time > start_time,
    )
    if exclude_booking_id:
        stmt = stmt.where(Booking.id != exclude_booking_id)

    result = await db.execute(stmt)
    conflicting = result.scalar_one_or_none()
    if conflicting:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "BookingOverlap",
                "message": "Asset is already booked for part or all of the requested time slot.",
                "conflicting_booking_id": str(conflicting.id),
                "conflicting_start": conflicting.start_time.isoformat(),
                "conflicting_end": conflicting.end_time.isoformat(),
            },
        )


# ── GET / ──────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[BookingOut])
async def list_bookings(
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(_resolve_user),
    asset_id: Optional[uuid.UUID] = Query(None),
    department_id: Optional[uuid.UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
):
    """
    Returns bookings visible to the current user:
    - Employees see only their own bookings.
    - Managers/Admins see all bookings (filterable by asset / department / status).
    """
    stmt = select(Booking)

    if current_user.role == "Employee":
        stmt = stmt.where(Booking.employee_id == current_user.id)

    if asset_id:
        stmt = stmt.where(Booking.asset_id == asset_id)
    if department_id:
        stmt = stmt.where(Booking.department_id == department_id)
    if status_filter:
        stmt = stmt.where(Booking.status == status_filter)

    stmt = stmt.order_by(Booking.start_time.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


# ── POST / ─────────────────────────────────────────────────────────────────

@router.post("/", response_model=BookingOut, status_code=201)
async def create_booking(
    body: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(_resolve_user),
):
    """
    Book a bookable asset for a time slot.
    Enforces overlap check and is_bookable guard.
    Fires a BookingCreated notification.
    """
    # Verify asset exists and is bookable
    asset = await db.get(Asset, body.asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    if not getattr(asset, "is_bookable", True):
        raise HTTPException(
            status_code=422,
            detail="Asset is not configured as bookable.",
        )

    # Overlap check
    await _check_overlap(db, body.asset_id, body.start_time, body.end_time)

    booking = Booking(
        asset_id=body.asset_id,
        employee_id=current_user.id,
        department_id=body.department_id,
        start_time=body.start_time,
        end_time=body.end_time,
        status="Upcoming",
    )
    db.add(booking)

    # ── Notification: BookingCreated ───────────────────────────────────────
    await create_notification(
        db=db,
        user_id=current_user.id,
        type_="BookingCreated",
        message=(
            f"Your booking for asset '{asset.name}' from "
            f"{body.start_time.strftime('%Y-%m-%d %H:%M')} to "
            f"{body.end_time.strftime('%Y-%m-%d %H:%M')} is confirmed."
        ),
        entity_type="Booking",
        entity_id=str(booking.id),
    )

    # ── Activity log ───────────────────────────────────────────────────────
    await db.flush()
    log_activity(
        db,
        current_user.id,
        "booking_created",
        "Booking",
        str(booking.id),
        details={"asset_id": str(body.asset_id), "asset_name": asset.name},
    )

    await db.commit()
    await db.refresh(booking)
    return booking


# ── GET /calendar ──────────────────────────────────────────────────────────

@router.get("/calendar")
async def calendar_view(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_authenticated),
    from_date: datetime = Query(...),
    to_date: datetime = Query(...),
    asset_id: Optional[uuid.UUID] = Query(None),
    department_id: Optional[uuid.UUID] = Query(None),
):
    """Return bookings within a date range for calendar display."""
    stmt = select(Booking).where(
        Booking.start_time < to_date,
        Booking.end_time > from_date,
    )
    if asset_id:
        stmt = stmt.where(Booking.asset_id == asset_id)
    if department_id:
        stmt = stmt.where(Booking.department_id == department_id)

    result = await db.execute(stmt)
    bookings = result.scalars().all()
    # Return a lightweight calendar-friendly shape
    return [
        {
            "id": str(b.id),
            "asset_id": str(b.asset_id),
            "employee_id": str(b.employee_id),
            "start_time": b.start_time.isoformat(),
            "end_time": b.end_time.isoformat(),
            "status": b.status,
        }
        for b in bookings
    ]


# ── GET /{booking_id} ──────────────────────────────────────────────────────

@router.get("/{booking_id}", response_model=BookingOut)
async def get_booking(
    booking_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(_resolve_user),
):
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    # Employees may only view their own bookings
    if current_user.role == "Employee" and booking.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this booking")
    return booking


# ── POST /{booking_id}/cancel ──────────────────────────────────────────────

@router.post("/{booking_id}/cancel", response_model=BookingOut)
async def cancel_booking(
    booking_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(_resolve_user),
):
    """
    Cancel an Upcoming booking.
    Only the booking owner or a manager can cancel.
    Fires a BookingCancelled notification.
    """
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Authorization: owner or manager
    is_owner = booking.employee_id == current_user.id
    is_manager = current_user.role in ("AssetManager", "Admin", "DepartmentHead")
    if not (is_owner or is_manager):
        raise HTTPException(status_code=403, detail="Not authorized to cancel this booking")

    if booking.status != "Upcoming":
        raise HTTPException(
            status_code=400,
            detail=f"Only Upcoming bookings can be cancelled (current: {booking.status})",
        )

    asset = await db.get(Asset, booking.asset_id)
    asset_name = asset.name if asset else "the asset"

    booking.status = "Cancelled"

    # ── Notification: BookingCancelled ─────────────────────────────────────
    await create_notification(
        db=db,
        user_id=booking.employee_id,
        type_="BookingCancelled",
        message=(
            f"Your booking for '{asset_name}' "
            f"({booking.start_time.strftime('%Y-%m-%d %H:%M')} – "
            f"{booking.end_time.strftime('%Y-%m-%d %H:%M')}) has been cancelled."
        ),
        entity_type="Booking",
        entity_id=str(booking.id),
    )

    # ── Activity log ───────────────────────────────────────────────────────
    log_activity(
        db,
        current_user.id,
        "booking_cancelled",
        "Booking",
        str(booking.id),
        details={"cancelled_by": str(current_user.id), "asset_name": asset_name},
    )

    await db.commit()
    await db.refresh(booking)
    return booking


# ── PUT /{booking_id}/reschedule ───────────────────────────────────────────

@router.put("/{booking_id}/reschedule", response_model=BookingOut)
async def reschedule_booking(
    booking_id: uuid.UUID,
    body: BookingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(_resolve_user),
):
    """
    Reschedule a booking's time window.
    Runs the same overlap check as create_booking (excludes this booking).
    """
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    is_owner = booking.employee_id == current_user.id
    is_manager = current_user.role in ("AssetManager", "Admin", "DepartmentHead")
    if not (is_owner or is_manager):
        raise HTTPException(status_code=403, detail="Not authorized to reschedule this booking")

    if booking.status != "Upcoming":
        raise HTTPException(
            status_code=400,
            detail=f"Only Upcoming bookings can be rescheduled (current: {booking.status})",
        )

    new_start = body.start_time or booking.start_time
    new_end = body.end_time or booking.end_time

    if new_end <= new_start:
        raise HTTPException(status_code=422, detail="end_time must be after start_time")

    # Overlap check excluding this booking
    await _check_overlap(db, booking.asset_id, new_start, new_end, exclude_booking_id=booking_id)

    booking.start_time = new_start
    booking.end_time = new_end

    # ── Activity log ───────────────────────────────────────────────────────
    log_activity(
        db,
        current_user.id,
        "booking_rescheduled",
        "Booking",
        str(booking.id),
        details={"new_start": new_start.isoformat(), "new_end": new_end.isoformat()},
    )

    await db.commit()
    await db.refresh(booking)
    return booking
