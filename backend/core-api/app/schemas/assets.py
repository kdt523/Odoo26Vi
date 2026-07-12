"""
app/schemas/assets.py — Pydantic schemas for the assets router.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AssetHistoryItem(BaseModel):
    id: UUID
    type: str  # "allocation" or "maintenance"
    date: datetime
    status: str
    details: dict[str, Any]
    
    model_config = {"from_attributes": True}


class AssetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category_id: UUID
    serial_number: Optional[str] = None
    acquisition_date: Optional[date] = None
    acquisition_cost: Optional[Decimal] = None
    condition: str = "New"
    location: Optional[str] = None
    is_bookable: bool = False
    photo_ref: Optional[str] = None
    document_ref: Optional[str] = None
    # asset_tag is auto-generated — not accepted from client


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[UUID] = None
    serial_number: Optional[str] = None
    acquisition_date: Optional[date] = None
    acquisition_cost: Optional[Decimal] = None
    condition: Optional[str] = None
    location: Optional[str] = None
    is_bookable: Optional[bool] = None
    photo_ref: Optional[str] = None
    document_ref: Optional[str] = None


class AssetOut(BaseModel):
    id: UUID
    name: str
    asset_tag: str
    category_id: UUID
    serial_number: Optional[str] = None
    acquisition_date: Optional[date] = None
    acquisition_cost: Optional[Decimal] = None
    condition: str
    location: Optional[str] = None
    is_bookable: bool
    status: str
    photo_ref: Optional[str] = None
    document_ref: Optional[str] = None

    model_config = {"from_attributes": True}


class AssetSearchParams(BaseModel):
    """Query params for asset search/filter."""
    tag: Optional[str] = None
    serial_number: Optional[str] = None
    category_id: Optional[UUID] = None
    status: Optional[str] = None
    department_id: Optional[UUID] = None
    location: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class AssetListResponse(BaseModel):
    items: list[AssetOut]
    total: int
    page: int
    page_size: int
