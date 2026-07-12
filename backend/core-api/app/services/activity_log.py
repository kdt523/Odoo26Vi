import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.activity_log import ActivityLog

def log_activity(
    db: AsyncSession,
    user_id: Optional[uuid.UUID],
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    details: Optional[dict] = None
) -> None:
    """
    Helper to create an ActivityLog entry and add it to the current DB session.
    The caller is responsible for committing the session.
    """
    log = ActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details
    )
    db.add(log)
