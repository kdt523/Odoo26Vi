"""
app/models/audit_item.py — AuditItem entity.

Each item records the physical verification result of one Asset
within an AuditCycle.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db import Base


class AuditItem(Base):
    __tablename__ = "audit_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    audit_cycle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("audit_cycles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    result: Mapped[Optional[str]] = mapped_column(
        SAEnum("Verified", "Missing", "Damaged", name="audit_result_enum"),
        nullable=True,  # null = not yet checked
    )

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────────────
    audit_cycle: Mapped["AuditCycle"] = relationship("AuditCycle", back_populates="audit_items")  # type: ignore[name-defined]
    asset: Mapped["Asset"] = relationship("Asset", back_populates="audit_items")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<AuditItem id={self.id} result={self.result!r}>"
