"""
app/schemas/upload.py — Pydantic schemas for the uploads router.
"""

from uuid import UUID

from pydantic import BaseModel


class UploadOut(BaseModel):
    file_id: UUID
    filename: str
    url: str

    model_config = {"from_attributes": True}
