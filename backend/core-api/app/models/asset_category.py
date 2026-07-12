"""
app/models/asset_category.py — Asset Category entity.

custom_fields (JSONB) stores category-specific metadata schemas,
e.g. {"warranty_period": "months", "voltage": "V"}.
"""

import uuid

from sqlalchemy import String, Boolean
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class AssetCategory(Base):
    __tablename__ = "asset_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # ── Relationships ──────────────────────────────────────────────────────
    assets: Mapped[list["Asset"]] = relationship(  # type: ignore[name-defined]
        "Asset", back_populates="category"
    )

    def __repr__(self) -> str:
        return f"<AssetCategory id={self.id} name={self.name!r}>"
