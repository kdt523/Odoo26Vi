"""
app/schemas/notifications.py — Pydantic schemas for the notifications router.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: UUID
    user_id: UUID
    type: str
    message: str
    is_read: bool
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListOut(BaseModel):
    """Envelope returned by GET /notifications."""
    items: List[NotificationOut]
    unread_count: int
    total: int
