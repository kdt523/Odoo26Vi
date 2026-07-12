"""
app/schemas/bookings.py — Pydantic schemas for the bookings router.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class BookingCreate(BaseModel):
    asset_id: UUID
    department_id: Optional[UUID] = None
    start_time: datetime
    end_time: datetime
    # TODO (bookings router): before inserting, query for overlapping bookings:
    #      SELECT 1 FROM bookings
    #      WHERE asset_id = :asset_id
    #        AND status IN ('Upcoming', 'Ongoing')
    #        AND start_time < :end_time AND end_time > :start_time
    #      LIMIT 1
    #      → raise 409 Conflict if any row returned.

    @model_validator(mode="after")
    def end_after_start(self) -> "BookingCreate":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class BookingUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class BookingOut(BaseModel):
    id: UUID
    asset_id: UUID
    employee_id: UUID
    department_id: Optional[UUID] = None
    start_time: datetime
    end_time: datetime
    status: str

    model_config = {"from_attributes": True}


class CalendarParams(BaseModel):
    """Query params for calendar view."""
    asset_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    from_date: datetime
    to_date: datetime
