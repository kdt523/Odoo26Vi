import csv
import io
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select, func, desc, extract, and_
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

@router.get("/maintenance-and-retirement-due")
async def maintenance_and_retirement_due(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_authenticated),
    maintenance_window_days: int = Query(30, ge=1, le=365, description="Days ahead to check for due maintenance"),
    retirement_window_days: int = Query(90, ge=1, le=730, description="Days ahead to check for nearing retirement"),
):
    """
    Two-section report:
    - due_for_maintenance: assets where next_maintenance_due_date is within
      `maintenance_window_days` days or already past (null values excluded).
    - nearing_retirement: assets where expected_retirement_date is within
      `retirement_window_days` days or already past (null values excluded).
    """
    today = date.today()
    maintenance_cutoff = today + timedelta(days=maintenance_window_days)
    retirement_cutoff = today + timedelta(days=retirement_window_days)

    # Due for maintenance: date is not null AND date <= cutoff
    maintenance_stmt = (
        select(Asset)
        .where(
            Asset.next_maintenance_due_date.isnot(None),
            Asset.next_maintenance_due_date <= maintenance_cutoff,
        )
        .order_by(Asset.next_maintenance_due_date)
    )
    maintenance_result = await db.execute(maintenance_stmt)
    maintenance_assets = maintenance_result.scalars().all()

    # Nearing retirement: date is not null AND date <= cutoff
    retirement_stmt = (
        select(Asset)
        .where(
            Asset.expected_retirement_date.isnot(None),
            Asset.expected_retirement_date <= retirement_cutoff,
        )
        .order_by(Asset.expected_retirement_date)
    )
    retirement_result = await db.execute(retirement_stmt)
    retirement_assets = retirement_result.scalars().all()

    def _asset_row(a: Asset) -> dict:
        return {
            "id": str(a.id),
            "asset_tag": a.asset_tag,
            "name": a.name,
            "status": a.status,
            "location": a.location,
            "next_maintenance_due_date": str(a.next_maintenance_due_date) if a.next_maintenance_due_date else None,
            "expected_retirement_date": str(a.expected_retirement_date) if a.expected_retirement_date else None,
            "days_until_maintenance": (
                (a.next_maintenance_due_date - today).days if a.next_maintenance_due_date else None
            ),
            "days_until_retirement": (
                (a.expected_retirement_date - today).days if a.expected_retirement_date else None
            ),
        }

    return {
        "maintenance_window_days": maintenance_window_days,
        "retirement_window_days": retirement_window_days,
        "generated_at": str(today),
        "due_for_maintenance": [_asset_row(a) for a in maintenance_assets],
        "nearing_retirement": [_asset_row(a) for a in retirement_assets],
    }


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
    elif report_type == "maintenance-retirement":
        today = date.today()
        stmt = (
            select(
                Asset.asset_tag,
                Asset.name,
                Asset.status,
                Asset.next_maintenance_due_date,
                Asset.expected_retirement_date,
            )
            .where(
                (Asset.next_maintenance_due_date <= today + timedelta(days=30)) |
                (Asset.expected_retirement_date <= today + timedelta(days=90))
            )
        )
        headers = ["Asset Tag", "Name", "Status", "Next Maintenance Due", "Expected Retirement"]
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
