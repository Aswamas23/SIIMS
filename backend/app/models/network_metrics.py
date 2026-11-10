from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, Boolean, DateTime, ForeignKey, String, BigInteger, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class NetworkMetric(Base):
    __tablename__ = "network_metrics"

    id = Column(Integer, primary_key=True, index=True)
    computer_id = Column(Integer, ForeignKey("computers.id", ondelete="CASCADE"), nullable=False, index=True)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Interface info
    interface_name = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    mac_address = Column(String(17), nullable=True)
    is_up = Column(Boolean, nullable=True)

    # Connectivity
    gateway_reachable = Column(Boolean, nullable=True)
    dns_resolves = Column(Boolean, nullable=True)
    server_reachable = Column(Boolean, nullable=True)

    # Performance
    latency_ms = Column(Float, nullable=True)
    packet_loss_percent = Column(Float, nullable=True)

    # Throughput
    bytes_sent = Column(BigInteger, nullable=True)
    bytes_recv = Column(BigInteger, nullable=True)

    # Relationships
    computer = relationship("Computer", back_populates="network_metrics")

    __table_args__ = (
        Index("ix_network_metrics_computer_id", "computer_id"),
        Index("ix_network_metrics_recorded_at", "recorded_at"),
        Index("ix_network_metrics_computer_recorded", "computer_id", "recorded_at"),
    )
