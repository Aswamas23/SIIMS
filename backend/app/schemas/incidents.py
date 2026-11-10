from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.incidents import IncidentSeverity, IncidentStatus, IncidentCategory
from app.models.incident_updates import UpdateType


class IncidentCreate(BaseModel):
    computer_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    category: IncidentCategory = IncidentCategory.other
    severity: IncidentSeverity = IncidentSeverity.medium


class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[IncidentCategory] = None
    severity: Optional[IncidentSeverity] = None
    status: Optional[IncidentStatus] = None


class IncidentAssignRequest(BaseModel):
    user_id: int


class IncidentUpdateCreate(BaseModel):
    message: str
    update_type: UpdateType = UpdateType.comment


class IncidentResolveRequest(BaseModel):
    resolution_notes: Optional[str] = None


class IncidentUpdateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    user_id: Optional[int] = None
    update_type: UpdateType
    message: str
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    created_at: datetime


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_number: str
    computer_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    category: IncidentCategory
    severity: IncidentSeverity
    status: IncidentStatus
    created_by_id: Optional[int] = None
    assigned_to_id: Optional[int] = None
    is_auto_created: bool
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    updates: list[IncidentUpdateResponse] = []
