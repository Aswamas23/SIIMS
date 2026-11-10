from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    value_type = Column(String(50), default="string", nullable=False)  # 'string', 'integer', 'float', 'boolean', 'json'
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)  # 'thresholds', 'smtp', 'monitoring', 'general'
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_system_settings_key", "key"),
        Index("ix_system_settings_category", "category"),
    )
