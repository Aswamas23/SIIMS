from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date
from app.models.maintenance_records import MaintenanceType


class MaintenanceCreate(BaseModel):
    computer_id: int
    maintenance_type: MaintenanceType = MaintenanceType.preventive
    title: str
    description: Optional[str] = None
    scheduled_date: Optional[date] = None
    cost: Optional[int] = None
    notes: Optional[str] = None


class MaintenanceUpdate(BaseModel):
    maintenance_type: Optional[MaintenanceType] = None
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_date: Optional[date] = None
    completed_date: Optional[date] = None
    cost: Optional[int] = None
    notes: Optional[str] = None


class MaintenanceCompleteRequest(BaseModel):
    notes: Optional[str] = None
    completed_date: Optional[date] = None


class MaintenanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    computer_id: int
    performed_by_id: Optional[int] = None
    maintenance_type: MaintenanceType
    title: str
    description: Optional[str] = None
    scheduled_date: Optional[date] = None
    completed_date: Optional[date] = None
    cost: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
