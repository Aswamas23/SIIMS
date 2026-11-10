from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class LocationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[str] = None


class LocationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[str] = None


class LocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[str] = None
    created_at: datetime
    updated_at: datetime
