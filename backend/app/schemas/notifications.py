from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.notifications import NotificationType


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    message: Optional[str] = None
    notification_type: NotificationType
    related_id: Optional[int] = None
    related_type: Optional[str] = None
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    unread_count: int
    page: int
    pages: int
