from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_authenticated
from app.db import get_db
from app.models.allocation import Allocation
from app.models.asset import Asset
from app.models.booking import Booking
from app.models.employee import Employee
from app.models.maintenance_request import MaintenanceRequest
from app.models.transfer_request import TransferRequest

router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(require_authenticated)])

@router.get("/summary")
async def get_dashboard_summary(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    
    # Ensure we have the actual ORM object to get department_id
    # If get_current_user is still a stub returning dict, we fetch it here.
    user = current_user
    if isinstance(user, dict):
        import uuid
        from fastapi import HTTPException
        try:
            user_id = uuid.UUID(user.get("sub"))
        except (ValueError, TypeError):
            raise HTTPException(status_code=401, detail="Invalid token subject")
        result = await db.execute(select(Employee).where(Employee.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

    role = user.role
    is_admin = role in ("Admin", "AssetManager")
    is_dept_head = role == "DepartmentHead"
    is_employee = role == "Employee"

    # Base conditions for scoping
    # 1. Assets Allocated
    alloc_scope = True
    if is_dept_head:
        # Allocations belonging to the dept, OR allocated to an employee in the dept
        alloc_scope = or_(
            Allocation.department_id == user.department_id,
            Allocation.employee.has(department_id=user.department_id)
        )
    elif is_employee:
        alloc_scope = Allocation.employee_id == user.id

    # 2. Maintenance Today
    maint_scope = True
    if is_dept_head:
        maint_scope = MaintenanceRequest.raised_by_employee.has(department_id=user.department_id)
    elif is_employee:
        maint_scope = MaintenanceRequest.raised_by == user.id

    # 3. Active Bookings
    booking_scope = True
    if is_dept_head:
        booking_scope = or_(
            Booking.department_id == user.department_id,
            Booking.employee.has(department_id=user.department_id)
        )
    elif is_employee:
        booking_scope = Booking.employee_id == user.id

    # 4. Pending Transfers
    transfer_scope = True
    if is_dept_head:
        transfer_scope = or_(
            TransferRequest.target_department_id == user.department_id,
            TransferRequest.target_employee_id.in_(
                select(Employee.id).where(Employee.department_id == user.department_id)
            ),
            TransferRequest.allocation.has(Allocation.department_id == user.department_id),
            TransferRequest.allocation.has(Allocation.employee.has(department_id=user.department_id))
        )
    elif is_employee:
        transfer_scope = or_(
            TransferRequest.target_employee_id == user.id,
            TransferRequest.allocation.has(Allocation.employee_id == user.id)
        )

    today = date.today()
    next_week = today + timedelta(days=7)

    # Assets Available: Org-wide count for everyone
    q_available = select(func.count()).select_from(Asset).where(Asset.status == "Available")
    
    # Assets Allocated
    q_allocated = select(func.count()).select_from(Allocation).where(
        Allocation.status == "Active",
        alloc_scope
    )
    
    # Maintenance Today
    q_maint = select(func.count()).select_from(MaintenanceRequest).where(
        MaintenanceRequest.status.in_(["Approved", "TechnicianAssigned", "InProgress"]),
        func.date(MaintenanceRequest.updated_at) == today,
        maint_scope
    )
    
    # Active Bookings
    q_bookings = select(func.count()).select_from(Booking).where(
        Booking.status == "Ongoing",
        booking_scope
    )
    
    # Pending Transfers
    q_transfers = select(func.count()).select_from(TransferRequest).where(
        TransferRequest.status == "Requested",
        transfer_scope
    )
    
    # Upcoming Returns (Expected in next 7 days, not returned)
    q_upcoming = select(func.count()).select_from(Allocation).where(
        Allocation.expected_return_date >= today,
        Allocation.expected_return_date <= next_week,
        Allocation.actual_return_date.is_(None),
        Allocation.status == "Active",
        alloc_scope
    )

    # Execute queries concurrently where possible, or sequentially
    val_available = await db.scalar(q_available)
    val_allocated = await db.scalar(q_allocated)
    val_maint = await db.scalar(q_maint)
    val_bookings = await db.scalar(q_bookings)
    val_transfers = await db.scalar(q_transfers)
    val_upcoming = await db.scalar(q_upcoming)

    return {
        "assets_available": val_available or 0,
        "assets_allocated": val_allocated or 0,
        "maintenance_today": val_maint or 0,
        "active_bookings": val_bookings or 0,
        "pending_transfers": val_transfers or 0,
        "upcoming_returns": val_upcoming or 0,
    }


@router.get("/overdue")
async def get_dashboard_overdue(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = current_user
    if isinstance(user, dict):
        import uuid
        from fastapi import HTTPException
        try:
            user_id = uuid.UUID(user.get("sub"))
        except (ValueError, TypeError):
            raise HTTPException(status_code=401, detail="Invalid token subject")
        result = await db.execute(select(Employee).where(Employee.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

    role = user.role
    is_admin = role in ("Admin", "AssetManager")
    is_dept_head = role == "DepartmentHead"
    is_employee = role == "Employee"

    alloc_scope = True
    if is_dept_head:
        alloc_scope = or_(
            Allocation.department_id == user.department_id,
            Allocation.employee.has(department_id=user.department_id)
        )
    elif is_employee:
        alloc_scope = Allocation.employee_id == user.id

    booking_scope = True
    if is_dept_head:
        booking_scope = or_(
            Booking.department_id == user.department_id,
            Booking.employee.has(department_id=user.department_id)
        )
    elif is_employee:
        booking_scope = Booking.employee_id == user.id

    today = date.today()

    # Overdue Allocations
    q_overdue_allocs = select(Allocation).where(
        Allocation.expected_return_date < today,
        Allocation.actual_return_date.is_(None),
        Allocation.status == "Active",
        alloc_scope
    ).limit(50)

    # Overdue Bookings (Ended but not completed/cancelled)
    q_overdue_bookings = select(Booking).where(
        Booking.end_time < func.now(),
        Booking.status.in_(["Upcoming", "Ongoing"]),
        booking_scope
    ).limit(50)

    res_allocs = await db.scalars(q_overdue_allocs)
    res_bookings = await db.scalars(q_overdue_bookings)

    allocs = res_allocs.all()
    bookings = res_bookings.all()

    return {
        "overdue_allocations": [
            {
                "id": str(a.id),
                "asset_id": str(a.asset_id),
                "expected_return_date": a.expected_return_date,
            } for a in allocs
        ],
        "overdue_bookings": [
            {
                "id": str(b.id),
                "asset_id": str(b.asset_id),
                "end_time": b.end_time,
            } for b in bookings
        ]
    }
