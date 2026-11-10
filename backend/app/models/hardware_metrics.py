from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, Boolean, DateTime, ForeignKey, String, BigInteger, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class HardwareMetric(Base):
    __tablename__ = "hardware_metrics"

    id = Column(Integer, primary_key=True, index=True)
    computer_id = Column(Integer, ForeignKey("computers.id", ondelete="CASCADE"), nullable=False, index=True)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # CPU
    cpu_percent = Column(Float, nullable=True)
    cpu_freq_mhz = Column(Float, nullable=True)
    cpu_count_logical = Column(Integer, nullable=True)
    cpu_temp_celsius = Column(Float, nullable=True)  # may be unavailable

    # RAM
    ram_total_gb = Column(Float, nullable=True)
    ram_used_gb = Column(Float, nullable=True)
    ram_percent = Column(Float, nullable=True)

    # Disk (primary/C: drive)
    disk_total_gb = Column(Float, nullable=True)
    disk_used_gb = Column(Float, nullable=True)
    disk_free_gb = Column(Float, nullable=True)
    disk_percent = Column(Float, nullable=True)

    # SMART
    smart_status = Column(String(50), nullable=True)  # 'healthy', 'warning', 'failing', 'unavailable'

    # System
    uptime_seconds = Column(BigInteger, nullable=True)
    boot_time = Column(DateTime(timezone=True), nullable=True)

    # Battery (laptops)
    battery_percent = Column(Float, nullable=True)
    battery_plugged = Column(Boolean, nullable=True)

    # Relationships
    computer = relationship("Computer", back_populates="hardware_metrics")

    __table_args__ = (
        Index("ix_hardware_metrics_computer_id", "computer_id"),
        Index("ix_hardware_metrics_recorded_at", "recorded_at"),
        Index("ix_hardware_metrics_computer_recorded", "computer_id", "recorded_at"),
    )
