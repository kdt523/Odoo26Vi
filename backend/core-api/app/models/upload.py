"""
app/models/upload.py — UploadRecord entity.

Tracks metadata for files stored on the local disk.
"""

import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class UploadRecord(Base):
    __tablename__ = "upload_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)

    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Relationships ──────────────────────────────────────────────────────
    uploader: Mapped["Employee"] = relationship(  # type: ignore[name-defined]
        "Employee", foreign_keys=[uploaded_by]
    )

    def __repr__(self) -> str:
        return f"<UploadRecord id={self.id} filename={self.original_filename!r}>"
