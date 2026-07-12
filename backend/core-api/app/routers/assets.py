"""
app/routers/assets.py — Asset registry router.

Endpoints:
  GET    /                  — List/search assets (filterable)
  POST   /                  — Register a new asset (AssetManager)
  GET    /{id}              — Asset detail
  PUT    /{id}              — Update asset metadata (AssetManager)
  GET    /{id}/history      — Allocation + maintenance history
"""

import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, desc

from app.core.security import require_asset_manager, require_authenticated, require_dept_head
from app.db import get_db
from app.schemas.assets import AssetCreate, AssetListResponse, AssetOut, AssetUpdate, AssetHistoryItem
from app.models.asset import Asset
from app.models.allocation import Allocation
from app.models.maintenance_request import MaintenanceRequest
from app.models.maintenance_request import MaintenanceRequest
from app.models.activity_log import ActivityLog
from app.services.activity_log import log_activity

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
    """
    stmt = select(Asset)
    
    if department_id:
        # Join Allocation where status='Active' to filter by currently allocated department
        stmt = stmt.outerjoin(Allocation, Asset.id == Allocation.asset_id).where(
            Allocation.status == "Active",
            Allocation.department_id == department_id
        )
        
    if tag:
        stmt = stmt.where(Asset.asset_tag.ilike(f"%{tag}%"))
    if serial_number:
        stmt = stmt.where(Asset.serial_number.ilike(f"%{serial_number}%"))
    if category_id:
        stmt = stmt.where(Asset.category_id == category_id)
    if status_filter:
        stmt = stmt.where(Asset.status == status_filter)
    if location:
        stmt = stmt.where(Asset.location.ilike(f"%{location}%"))

    # Count total items
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # Pagination
    stmt = stmt.limit(page_size).offset((page - 1) * page_size)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/", response_model=AssetOut, status_code=201,
             dependencies=[Depends(require_asset_manager)])
async def register_asset(body: AssetCreate, current_user=Depends(require_asset_manager), db: AsyncSession = Depends(get_db)):
    """
    Register a new asset.
    Auto-generates asset_tag in AF-XXXX format securely.
    """
    # Create sequence if not exists (PostgreSQL specific)
    await db.execute(text("CREATE SEQUENCE IF NOT EXISTS asset_tag_seq START 1;"))
    seq_result = await db.execute(text("SELECT nextval('asset_tag_seq');"))
    next_val = seq_result.scalar_one()
    
    generated_tag = f"AF-{next_val:04d}"

    asset = Asset(
        name=body.name,
        asset_tag=generated_tag,
        category_id=body.category_id,
        serial_number=body.serial_number,
        acquisition_date=body.acquisition_date,
        acquisition_cost=body.acquisition_cost,
        condition=body.condition,
        location=body.location,
        is_bookable=body.is_bookable,
        photo_ref=body.photo_ref,
        document_ref=body.document_ref,
        status="Available"
    )
    db.add(asset)
    
    await db.flush()
    log_activity(
        db,
        current_user.id,
        "asset_registered",
        "Asset",
        str(asset.id),
        details={
            "asset_tag": generated_tag,
            "category_id": str(body.category_id)
        }
    )
    
    await db.commit()
    await db.refresh(asset)
    
    return asset


@router.get("/mine", response_model=AssetListResponse)
async def get_my_assets(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_authenticated),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Return assets currently allocated to the calling Employee.
    """
    stmt = select(Asset).join(Allocation, Asset.id == Allocation.asset_id).where(
        Allocation.status == "Active",
        Allocation.employee_id == current_user.id
    )
    
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()
    
    stmt = stmt.limit(page_size).offset((page - 1) * page_size)
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/department", response_model=AssetListResponse)
async def get_department_assets(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_dept_head),
    department_id: Optional[uuid.UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Return assets allocated to a department. 
    Department Heads are locked to their own department. Admins can query any.
    """
    target_dept_id = department_id
    if current_user.role != "Admin":
        target_dept_id = current_user.department_id
        if not target_dept_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You do not belong to a department.")
            
    if not target_dept_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="department_id query parameter is required for Admins.")
        
    stmt = select(Asset).join(Allocation, Asset.id == Allocation.asset_id).where(
        Allocation.status == "Active",
        Allocation.department_id == target_dept_id
    )
    
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()
    
    stmt = stmt.limit(page_size).offset((page - 1) * page_size)
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{asset_id}", response_model=AssetOut)
async def get_asset(asset_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                    _=Depends(require_authenticated)):
    stmt = select(Asset).where(Asset.id == asset_id)
    result = await db.execute(stmt)
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
        
    return asset


@router.put("/{asset_id}", response_model=AssetOut,
            dependencies=[Depends(require_asset_manager)])
async def update_asset(asset_id: uuid.UUID, body: AssetUpdate,
                       current_user=Depends(require_asset_manager),
                       db: AsyncSession = Depends(get_db)):
    stmt = select(Asset).where(Asset.id == asset_id)
    result = await db.execute(stmt)
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
        
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(asset, field, value)
        
    log_activity(
        db,
        current_user.id,
        "asset_updated",
        "Asset",
        str(asset.id),
        details={"updated_fields": list(body.model_dump(exclude_unset=True).keys())}
    )
    
    await db.commit()
    await db.refresh(asset)
    return asset


@router.get("/{asset_id}/history", response_model=List[AssetHistoryItem])
async def get_asset_history(asset_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                             _=Depends(require_authenticated)):
    """
    Return combined allocation + maintenance history for an asset.
    """
    # Verify asset exists
    asset_result = await db.execute(select(Asset).where(Asset.id == asset_id))
    if not asset_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
        
    history = []
    
    # Allocations
    alloc_stmt = select(Allocation).where(Allocation.asset_id == asset_id).order_by(desc(Allocation.created_at))
    alloc_result = await db.execute(alloc_stmt)
    for alloc in alloc_result.scalars().all():
        history.append(AssetHistoryItem(
            id=alloc.id,
            type="allocation",
            date=alloc.created_at,
            status=alloc.status,
            details={
                "employee_id": str(alloc.employee_id) if alloc.employee_id else None,
                "department_id": str(alloc.department_id) if alloc.department_id else None,
                "allocated_date": str(alloc.allocated_date),
                "actual_return_date": str(alloc.actual_return_date) if alloc.actual_return_date else None,
            }
        ))
        
    # Maintenance Requests
    maint_stmt = select(MaintenanceRequest).where(MaintenanceRequest.asset_id == asset_id).order_by(desc(MaintenanceRequest.created_at))
    maint_result = await db.execute(maint_stmt)
    for req in maint_result.scalars().all():
        history.append(AssetHistoryItem(
            id=req.id,
            type="maintenance",
            date=req.created_at,
            status=req.status,
            details={
                "raised_by": str(req.raised_by) if req.raised_by else None,
                "issue_description": req.issue_description,
                "priority": req.priority,
            }
        ))
        
    # Sort combined history newest first
    history.sort(key=lambda x: x.date, reverse=True)
    return history
