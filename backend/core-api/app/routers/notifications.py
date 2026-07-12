"""
app/routers/notifications.py — Notification read endpoints.

Endpoints:
  GET  /notifications          — current user's notifications, newest first + unread_count
  POST /notifications/{id}/read — mark a single notification as read
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_authenticated
from app.db import get_db
from app.models.employee import Employee
from app.models.notification import Notification
from app.schemas.notifications import NotificationListOut, NotificationOut

router = APIRouter(prefix="/notifications", tags=["notifications"])


async def _resolve_user(
    current_user=Depends(get_current_user),
) -> Employee:
    """Ensure we always have an Employee ORM object, not a raw dict."""
    return current_user


# ── GET /notifications ─────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=NotificationListOut,
    summary="List current user's notifications (newest first)",
)
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(_resolve_user),
):
    """
    Returns all notifications for the authenticated user, ordered newest-first.
    The envelope also includes:
    - `unread_count`: number of unread notifications
    - `total`: total notification count
    """
    # Fetch all notifications for this user, newest first
    stmt = (
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
    )
    result = await db.execute(stmt)
    notifications = result.scalars().all()

    # Count unread
    unread_stmt = (
        select(func.count())
        .select_from(Notification)
        .where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
    )
    unread_result = await db.execute(unread_stmt)
    unread_count = unread_result.scalar_one()

    return NotificationListOut(
        items=[NotificationOut.model_validate(n) for n in notifications],
        unread_count=unread_count,
        total=len(notifications),
    )


# ── POST /notifications/{id}/read ─────────────────────────────────────────

@router.post(
    "/{notification_id}/read",
    response_model=NotificationOut,
    summary="Mark a notification as read",
)
async def mark_notification_read(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(_resolve_user),
):
    """
    Mark a single notification as read.
    Returns 404 if the notification doesn't exist or doesn't belong to the caller.
    """
    notif = await db.get(Notification, notification_id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    # Ownership check — users may only mark their own notifications
    if notif.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot mark another user's notification as read",
        )

    if not notif.is_read:
        notif.is_read = True
        # Session auto-commits via get_db(); no explicit commit needed here

    return NotificationOut.model_validate(notif)
