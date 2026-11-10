from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date
from app.models.software_licences import LicenceStatus


class LicenceCreate(BaseModel):
    software_name: str
    version: Optional[str] = None
    licence_key: Optional[str] = None
    licence_type: Optional[str] = None
    vendor: Optional[str] = None
    seats: Optional[int] = None
    purchase_date: Optional[date] = None
    expiry_date: Optional[date] = None
    cost: Optional[int] = None
    notes: Optional[str] = None


class LicenceUpdate(BaseModel):
    software_name: Optional[str] = None
    version: Optional[str] = None
    licence_key: Optional[str] = None
    licence_type: Optional[str] = None
    vendor: Optional[str] = None
    seats: Optional[int] = None
    purchase_date: Optional[date] = None
    expiry_date: Optional[date] = None
    cost: Optional[int] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class LicenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    software_name: str
    version: Optional[str] = None
    licence_type: Optional[str] = None
    vendor: Optional[str] = None
    seats: Optional[int] = None
    purchase_date: Optional[date] = None
    expiry_date: Optional[date] = None
    cost: Optional[int] = None
    notes: Optional[str] = None
    status: LicenceStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime
    assignments_count: Optional[int] = None


class LicenceAssignRequest(BaseModel):
    computer_id: int
