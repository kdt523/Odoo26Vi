"""
app/routers/assets.py — Asset registry router.

Endpoints:
  GET    /                  — List/search assets (filterable)
  POST   /                  — Register a new asset (AssetManager)
  GET    /{id}              — Asset detail
  PUT    /{id}              — Update asset metadata (AssetManager)
  GET    /{id}/history      — Allocation + maintenance history stub
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.security import require_asset_manager, require_authenticated
from app.db import get_db
from app.schemas.assets import AssetCreate, AssetListResponse, AssetOut, AssetUpdate

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("/", response_model=AssetListResponse)
async def list_assets(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_authenticated),
    tag: Optional[str] = Query(None),
    serial_number: Optional[str] = Query(None),
    category_id: Optional[uuid.UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    department_id: Optional[uuid.UUID] = Query(None),
    location: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Search / filter assets.
    TODO: build dynamic SQLAlchemy query from non-None params.
    TODO: join with allocations to filter by department_id.
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/", response_model=AssetOut, status_code=201,
             dependencies=[Depends(require_asset_manager)])
async def register_asset(body: AssetCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new asset.
    TODO: auto-generate asset_tag in AF-XXXX format (query MAX tag, increment).
    TODO: insert Asset ORM object.
    TODO: write ActivityLog entry.
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/{asset_id}", response_model=AssetOut)
async def get_asset(asset_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                    _=Depends(require_authenticated)):
    """
    TODO: fetch asset by id → 404 if not found.
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.put("/{asset_id}", response_model=AssetOut,
            dependencies=[Depends(require_asset_manager)])
async def update_asset(asset_id: uuid.UUID, body: AssetUpdate,
                        db: AsyncSession = Depends(get_db)):
    """
    TODO: fetch → apply non-None fields → commit.
    TODO: write ActivityLog entry.
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/{asset_id}/history")
async def get_asset_history(asset_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                             _=Depends(require_authenticated)):
    """
    Return combined allocation + maintenance history for an asset.
    TODO: join allocations + transfer_requests + maintenance_requests for asset_id.
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")
