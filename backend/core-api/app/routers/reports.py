import csv
import io
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select, func, desc, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_authenticated
from app.db import get_db
from app.models.asset import Asset
from app.models.asset_category import AssetCategory
from app.models.allocation import Allocation
from app.models.booking import Booking
from app.models.maintenance_request import MaintenanceRequest
from app.models.department import Department

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/asset-utilization")
async def asset_utilization(db: AsyncSession = Depends(get_db), _=Depends(require_authenticated)):
    # Simple utilization: count total allocations per asset
    stmt = (
        select(
            Asset.name,
            func.count(Allocation.id).label("allocation_count")
        )
        .outerjoin(Allocation, Asset.id == Allocation.asset_id)
        .group_by(Asset.id)
        .order_by(desc("allocation_count"))
        .limit(10)
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    data = [{"name": row.name, "allocations": row.allocation_count} for row in rows]
    return data

@router.get("/maintenance-frequency")
async def maintenance_frequency(db: AsyncSession = Depends(get_db), _=Depends(require_authenticated)):
    # Count maintenance requests by category
    stmt = (
        select(
            AssetCategory.name,
            func.count(MaintenanceRequest.id).label("freq")
        )
        .select_from(AssetCategory)
        .outerjoin(Asset, Asset.category_id == AssetCategory.id)
        .outerjoin(MaintenanceRequest, MaintenanceRequest.asset_id == Asset.id)
        .group_by(AssetCategory.id)
        .order_by(desc("freq"))
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    data = [{"category": row.name, "frequency": row.freq} for row in rows]
    return data

@router.get("/allocation-summary")
async def allocation_summary(db: AsyncSession = Depends(get_db), _=Depends(require_authenticated)):
    stmt = (
        select(
            Department.name,
            func.count(Allocation.id).label("active_allocations")
        )
        .outerjoin(Allocation, (Department.id == Allocation.department_id) & (Allocation.status == 'Active'))
        .group_by(Department.id)
        .order_by(desc("active_allocations"))
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    data = [{"department": row.name, "active_allocations": row.active_allocations} for row in rows]
    return data

@router.get("/booking-heatmap")
async def booking_heatmap(db: AsyncSession = Depends(get_db), _=Depends(require_authenticated)):
    # In Postgres: extract('isodow', Booking.start_time)
    stmt = (
        select(
            extract('isodow', Booking.start_time).label('dow'),
            extract('hour', Booking.start_time).label('hour'),
            func.count(Booking.id).label("count")
        )
        .group_by('dow', 'hour')
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    data = [{"day_of_week": row.dow, "hour": row.hour, "count": row.count} for row in rows if row.dow is not None]
    return data

@router.get("/export")
async def export_report(report_type: str = Query("utilization"), db: AsyncSession = Depends(get_db), _=Depends(require_authenticated)):
    if report_type == "utilization":
        stmt = (
            select(Asset.name, func.count(Allocation.id))
            .outerjoin(Allocation, Asset.id == Allocation.asset_id)
            .group_by(Asset.id)
        )
        headers = ["Asset Name", "Allocations"]
    elif report_type == "maintenance":
        stmt = (
            select(AssetCategory.name, func.count(MaintenanceRequest.id))
            .select_from(AssetCategory)
            .outerjoin(Asset, Asset.category_id == AssetCategory.id)
            .outerjoin(MaintenanceRequest, MaintenanceRequest.asset_id == Asset.id)
            .group_by(AssetCategory.id)
        )
        headers = ["Category", "Maintenance Frequency"]
    elif report_type == "allocation":
        stmt = (
            select(Department.name, func.count(Allocation.id))
            .outerjoin(Allocation, (Department.id == Allocation.department_id) & (Allocation.status == 'Active'))
            .group_by(Department.id)
        )
        headers = ["Department", "Active Allocations"]
    else:
        stmt = None
        headers = ["Data"]
        
    if stmt is not None:
        result = await db.execute(stmt)
        rows = result.all()
    else:
        rows = []
        
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
        
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={report_type}_report.csv"}
    )
