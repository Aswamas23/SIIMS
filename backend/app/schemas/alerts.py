from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.alerts import AlertSeverity, AlertStatus, AlertType


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    computer_id: int
    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus
    title: str
    message: Optional[str] = None
    metric_value: Optional[float] = None
    threshold_value: Optional[float] = None
    is_acknowledged: bool
    acknowledged_by_id: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class AlertAcknowledgeRequest(BaseModel):
    notes: Optional[str] = None
