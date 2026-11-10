from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, Enum as SAEnum, Index
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class AlertSeverity(str, enum.Enum):
    warning = "warning"
    critical = "critical"
    info = "info"


class AlertStatus(str, enum.Enum):
    active = "active"
    acknowledged = "acknowledged"
    resolved = "resolved"


class AlertType(str, enum.Enum):
    cpu_high = "cpu_high"
    ram_high = "ram_high"
    disk_high = "disk_high"
    disk_critical = "disk_critical"
    smart_failure = "smart_failure"
    computer_offline = "computer_offline"
    network_issue = "network_issue"
    licence_expiring = "licence_expiring"
    licence_expired = "licence_expired"
    battery_low = "battery_low"
    custom = "custom"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    computer_id = Column(Integer, ForeignKey("computers.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_type = Column(SAEnum(AlertType), nullable=False, index=True)
    severity = Column(SAEnum(AlertSeverity), default=AlertSeverity.warning, nullable=False, index=True)
    status = Column(SAEnum(AlertStatus), default=AlertStatus.active, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=True)
    metric_value = Column(Float, nullable=True)  # The value that triggered the alert
    threshold_value = Column(Float, nullable=True)
    is_acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    computer = relationship("Computer", back_populates="alerts")
    acknowledged_by = relationship("User", foreign_keys=[acknowledged_by_id])
    # Note: Incident has FK to alerts, avoid circular relationship definition here

    __table_args__ = (
        Index("ix_alerts_computer_id", "computer_id"),
        Index("ix_alerts_alert_type", "alert_type"),
        Index("ix_alerts_status", "status"),
        Index("ix_alerts_severity", "severity"),
        Index("ix_alerts_created_at", "created_at"),
        Index("ix_alerts_computer_type_status", "computer_id", "alert_type", "status"),
    )
