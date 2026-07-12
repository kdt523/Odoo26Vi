"""
app/routers/activity_log.py — Activity log read endpoint.

Endpoints:
  GET /activity-log — filterable by user_id, date range, entity_type
                      paginated with page / page_size
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_asset_manager
from app.db import get_db
from app.models.activity_log import ActivityLog
from app.schemas.activity_log import ActivityLogListOut, ActivityLogOut

router = APIRouter(prefix="/activity-log", tags=["activity-log"])


@router.get(
    "/",
    response_model=ActivityLogListOut,
    summary="List activity log entries (AssetManager / Admin only)",
    dependencies=[Depends(require_asset_manager)],
)
async def list_activity_log(
    db: AsyncSession = Depends(get_db),
    user_id: Optional[uuid.UUID] = Query(None, description="Filter by acting user"),
    from_date: Optional[datetime] = Query(None, description="Earliest timestamp (inclusive)"),
    to_date: Optional[datetime] = Query(None, description="Latest timestamp (inclusive)"),
    entity_type: Optional[str] = Query(None, description="e.g. Allocation, Booking, MaintenanceRequest"),
    page: int = Query(1, ge=1, description="1-indexed page number"),
    page_size: int = Query(50, ge=1, le=200, description="Results per page"),
):
    """
    Returns a paginated list of activity log entries.

    Filters are all optional and combinable:
    - `user_id`     — only entries created by this employee
    - `from_date`   — entries at or after this timestamp (ISO 8601)
    - `to_date`     — entries at or before this timestamp (ISO 8601)
    - `entity_type` — e.g. `Allocation`, `TransferRequest`, `Booking`, `MaintenanceRequest`, `AuditCycle`
    """
    base_stmt = select(ActivityLog)

    if user_id is not None:
        base_stmt = base_stmt.where(ActivityLog.user_id == user_id)
    if from_date is not None:
        base_stmt = base_stmt.where(ActivityLog.timestamp >= from_date)
    if to_date is not None:
        base_stmt = base_stmt.where(ActivityLog.timestamp <= to_date)
    if entity_type is not None:
        base_stmt = base_stmt.where(ActivityLog.entity_type == entity_type)

    # Total count (for pagination metadata)
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # Paginated results, newest first
    offset = (page - 1) * page_size
    paged_stmt = (
        base_stmt
        .order_by(ActivityLog.timestamp.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(paged_stmt)
    logs = result.scalars().all()

    return ActivityLogListOut(
        items=[ActivityLogOut.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
    )
