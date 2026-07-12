"""
app/models/booking.py — Booking entity for time-slot resource reservation.

An asset must have is_bookable=True to accept bookings.

TODO (bookings router): enforce overlap rule —
  reject a booking if any other Active/Upcoming booking for the same asset
  has a time window that overlaps [start_time, end_time].
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db import Base


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )

    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    status: Mapped[str] = mapped_column(
        SAEnum(
            "Upcoming",
            "Ongoing",
            "Completed",
            "Cancelled",
            name="booking_status_enum",
        ),
        nullable=False,
        default="Upcoming",
    )

    reminder_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ──────────────────────────────────────────────────────
    asset: Mapped["Asset"] = relationship("Asset", back_populates="bookings")  # type: ignore[name-defined]
    employee: Mapped["Employee"] = relationship("Employee", back_populates="bookings")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<Booking id={self.id} asset_id={self.asset_id} status={self.status!r}>"
