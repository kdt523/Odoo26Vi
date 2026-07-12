"""
app/services/notifications.py — Shared notification write helper.

Usage (from any async router handler):
    from app.services.notifications import create_notification

    await create_notification(
        db=db,
        user_id=employee.id,
        type_="AssetAssigned",
        message="Laptop #A-042 has been allocated to you.",
        entity_type="Allocation",
        entity_id=str(new_alloc.id),
    )

Supported types (must match the DB enum):
    AssetAssigned | MaintenanceApproved | MaintenanceRejected |
    BookingCreated | BookingCancelled | TransferApproved |
    OverdueReturnAlert | AuditDiscrepancyFlagged

This helper is intentionally simple — it adds the row to the session but
does NOT commit; the calling router owns the transaction boundary.
"""

import uuid
from typing import Optional, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification

NotificationType = Literal[
    "AssetAssigned",
    "MaintenanceApproved",
    "MaintenanceRejected",
    "BookingCreated",
    "BookingCancelled",
    "TransferApproved",
    "OverdueReturnAlert",
    "AuditDiscrepancyFlagged",
]


async def create_notification(
    db: AsyncSession,
    user_id: uuid.UUID,
    type_: NotificationType,
    message: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
) -> Notification:
    """
    Create and stage a Notification row in the current session.

    The caller is responsible for committing (or the session will auto-commit
    via the get_db() dependency after the handler returns successfully).

    Returns the unsaved Notification instance (id is pre-assigned via uuid4
    default so callers can reference it before commit if needed).
    """
    notif = Notification(
        user_id=user_id,
        type=type_,
        message=message,
        entity_type=entity_type,
        entity_id=entity_id,
        is_read=False,
    )
    db.add(notif)
    return notif
