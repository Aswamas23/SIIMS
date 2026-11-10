from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class SettingUpdate(BaseModel):
    key: str
    value: str


class SettingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    value: Optional[str] = None
    value_type: str
    description: Optional[str] = None
    category: Optional[str] = None
    updated_at: datetime


class BatchSettingUpdate(BaseModel):
    settings: list[SettingUpdate]


class EmailTestResponse(BaseModel):
    success: bool
    message: str
