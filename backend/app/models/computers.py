from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text,
    ForeignKey, Enum as SAEnum, BigInteger, Index
)
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class ComputerStatus(str, enum.Enum):
    online = "online"
    offline = "offline"
    warning = "warning"
    critical = "critical"
    maintenance = "maintenance"
    unknown = "unknown"


class Computer(Base):
    __tablename__ = "computers"

    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String(255), nullable=False, unique=True)
    ip_address = Column(String(45), nullable=True, index=True)
    mac_address = Column(String(17), nullable=True, unique=True)
    manufacturer = Column(String(255), nullable=True)
    model = Column(String(255), nullable=True)
    processor = Column(String(255), nullable=True)
    ram_gb = Column(Integer, nullable=True)
    storage_gb = Column(BigInteger, nullable=True)
    operating_system = Column(String(255), nullable=True)
    os_version = Column(String(255), nullable=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True, index=True)
    department = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    status = Column(SAEnum(ComputerStatus), default=ComputerStatus.unknown, nullable=False, index=True)
    notes = Column(Text, nullable=True)
    registered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_seen = Column(DateTime(timezone=True), nullable=True, index=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    location = relationship("Location", back_populates="computers")
    agent_credentials = relationship("AgentCredential", back_populates="computer", cascade="all, delete-orphan")
    hardware_metrics = relationship("HardwareMetric", back_populates="computer", cascade="all, delete-orphan")
    network_metrics = relationship("NetworkMetric", back_populates="computer", cascade="all, delete-orphan")
    installed_software = relationship("InstalledSoftware", back_populates="computer", cascade="all, delete-orphan")
    licence_assignments = relationship("LicenceAssignment", back_populates="computer", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="computer")
    maintenance_records = relationship("MaintenanceRecord", back_populates="computer", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="computer", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_computers_location_id", "location_id"),
        Index("ix_computers_status", "status"),
        Index("ix_computers_is_active", "is_active"),
        Index("ix_computers_last_seen", "last_seen"),
        Index("ix_computers_ip_address", "ip_address"),
    )
