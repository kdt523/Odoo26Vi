"""
app/schemas/activity_log.py — Pydantic schemas for the activity-log router.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class ActivityLogOut(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


class ActivityLogListOut(BaseModel):
    """Paginated envelope returned by GET /activity-log."""
    items: List[ActivityLogOut]
    total: int
    page: int
    page_size: int
