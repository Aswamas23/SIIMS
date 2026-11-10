from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class HardwareMetricCreate(BaseModel):
    cpu_percent: Optional[float] = None
    cpu_freq_mhz: Optional[float] = None
    cpu_count_logical: Optional[int] = None
    cpu_temp_celsius: Optional[float] = None
    ram_total_gb: Optional[float] = None
    ram_used_gb: Optional[float] = None
    ram_percent: Optional[float] = None
    disk_total_gb: Optional[float] = None
    disk_used_gb: Optional[float] = None
    disk_free_gb: Optional[float] = None
    disk_percent: Optional[float] = None
    smart_status: Optional[str] = None
    uptime_seconds: Optional[int] = None
    battery_percent: Optional[float] = None
    battery_plugged: Optional[bool] = None


class HardwareMetricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    computer_id: int
    recorded_at: datetime
    cpu_percent: Optional[float] = None
    cpu_freq_mhz: Optional[float] = None
    cpu_count_logical: Optional[int] = None
    cpu_temp_celsius: Optional[float] = None
    ram_total_gb: Optional[float] = None
    ram_used_gb: Optional[float] = None
    ram_percent: Optional[float] = None
    disk_total_gb: Optional[float] = None
    disk_used_gb: Optional[float] = None
    disk_free_gb: Optional[float] = None
    disk_percent: Optional[float] = None
    smart_status: Optional[str] = None
    uptime_seconds: Optional[int] = None
    battery_percent: Optional[float] = None
    battery_plugged: Optional[bool] = None


class ThresholdUpdate(BaseModel):
    cpu_warning_percent: Optional[float] = None
    ram_warning_percent: Optional[float] = None
    disk_warning_percent: Optional[float] = None
    disk_critical_percent: Optional[float] = None
    offline_timeout_minutes: Optional[int] = None
    heartbeat_interval_seconds: Optional[int] = None
    software_scan_interval_hours: Optional[int] = None
    data_retention_days: Optional[int] = None


class ThresholdResponse(BaseModel):
    cpu_warning_percent: float
    ram_warning_percent: float
    disk_warning_percent: float
    disk_critical_percent: float
    offline_timeout_minutes: int
    heartbeat_interval_seconds: int
    software_scan_interval_hours: int
    data_retention_days: int
