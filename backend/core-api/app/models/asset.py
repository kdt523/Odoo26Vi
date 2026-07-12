"""
app/models/asset.py — Asset entity.

asset_tag is auto-generated (AF-XXXX format) — generation logic is a TODO
in the router layer; the column is unique + nullable=False at rest.

Status lifecycle (implement transitions in allocations/maintenance routers):
  Available ↔ Allocated ↔ Reserved ↔ UnderMaintenance
  Available → Lost | Retired | Disposed

TODO (allocations router): block re-allocation when status == 'Allocated';
     require TransferRequest instead.
"""

import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("asset_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Auto-generated tag e.g. AF-0001
    asset_tag: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)

    acquisition_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    acquisition_cost: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )

    condition: Mapped[str] = mapped_column(
        SAEnum("New", "Good", "Fair", "Poor", "Damaged", name="asset_condition_enum"),
        nullable=False,
        default="New",
    )

    location: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    is_bookable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    status: Mapped[str] = mapped_column(
        SAEnum(
            "Available",
            "Allocated",
            "Reserved",
            "UnderMaintenance",
            "Lost",
            "Retired",
            "Disposed",
            name="asset_status_enum",
        ),
        nullable=False,
        default="Available",
    )

    # File reference fields (store paths/URLs; actual files managed externally)
    photo_ref: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    document_ref: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────
    category: Mapped["AssetCategory"] = relationship(  # type: ignore[name-defined]
        "AssetCategory", back_populates="assets"
    )
    allocations: Mapped[list["Allocation"]] = relationship(  # type: ignore[name-defined]
        "Allocation", back_populates="asset"
    )
    bookings: Mapped[list["Booking"]] = relationship(  # type: ignore[name-defined]
        "Booking", back_populates="asset"
    )
    maintenance_requests: Mapped[list["MaintenanceRequest"]] = relationship(  # type: ignore[name-defined]
        "MaintenanceRequest", back_populates="asset"
    )
    audit_items: Mapped[list["AuditItem"]] = relationship(  # type: ignore[name-defined]
        "AuditItem", back_populates="asset"
    )

    def __repr__(self) -> str:
        return f"<Asset id={self.id} tag={self.asset_tag!r} status={self.status!r}>"
