"""
app/routers/bookings.py — Resource booking router.

Endpoints:
  GET    /                  — List bookings for current user / asset / department
  POST   /                  — Create booking  ← OVERLAP CHECK HERE
  GET    /calendar          — Calendar view (date-range query)
  GET    /{id}              — Booking detail
  POST   /{id}/cancel       — Cancel a booking
  PUT    /{id}/reschedule   — Reschedule (cancel + re-create equivalent)
"""

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_authenticated
from app.db import get_db
from app.schemas.bookings import BookingCreate, BookingOut, BookingUpdate

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("/", response_model=List[BookingOut])
async def list_bookings(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_authenticated),
    asset_id: Optional[uuid.UUID] = Query(None),
    department_id: Optional[uuid.UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
):
    # TODO: filter by caller's employee_id, or by asset_id / department_id for managers
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/", response_model=BookingOut, status_code=201)
async def create_booking(body: BookingCreate, db: AsyncSession = Depends(get_db),
                          current_user=Depends(require_authenticated)):
    """
    Book a bookable asset for a time slot.

    ─────────────────────────────────────────────────
    TODO: OVERLAP CHECK — implement before inserting:
      SELECT 1 FROM bookings
      WHERE asset_id = :asset_id
        AND status IN ('Upcoming', 'Ongoing')
        AND start_time < :end_time
        AND end_time   > :start_time
      LIMIT 1

      → If any row exists:
           raise HTTPException(409, detail={
             "error": "BookingOverlap",
             "message": "Asset is already booked for part or all of the requested time slot."
           })
    ─────────────────────────────────────────────────

    After passing overlap check:
      TODO: verify asset.is_bookable == True → 422 if not
      TODO: insert Booking(status='Upcoming', employee_id=current_user.id, ...)
      TODO: write Notification(type='BookingCreated', user_id=current_user.id)
      TODO: write ActivityLog entry
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/calendar")
async def calendar_view(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_authenticated),
    from_date: datetime = Query(...),
    to_date: datetime = Query(...),
    asset_id: Optional[uuid.UUID] = Query(None),
    department_id: Optional[uuid.UUID] = Query(None),
):
    """
    Return bookings within a date range for calendar display.
    TODO: query bookings where start_time < to_date AND end_time > from_date,
          filtered by optional asset_id / department_id.
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/{booking_id}", response_model=BookingOut)
async def get_booking(booking_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                       _=Depends(require_authenticated)):
    # TODO: fetch by id → 404
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/{booking_id}/cancel", response_model=BookingOut)
async def cancel_booking(booking_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                          current_user=Depends(require_authenticated)):
    """
    Cancel an Upcoming booking.
    TODO: only the booking owner or a manager can cancel.
    TODO: set booking.status = 'Cancelled'
    TODO: write Notification(type='BookingCancelled')
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.put("/{booking_id}/reschedule", response_model=BookingOut)
async def reschedule_booking(booking_id: uuid.UUID, body: BookingUpdate,
                              db: AsyncSession = Depends(get_db),
                              current_user=Depends(require_authenticated)):
    """
    Reschedule a booking's time window.
    TODO: run the same OVERLAP CHECK as create_booking (exclude current booking_id from query).
    TODO: update start_time / end_time.
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")
