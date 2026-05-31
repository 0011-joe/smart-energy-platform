import enum
import uuid
from datetime import datetime

from app.core.database import Base
from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class DeviceType(str, enum.Enum):
    """设备类型枚举"""

    SMART_METER = "smart_meter"
    SOLAR_PANEL = "solar_panel"
    BATTERY = "battery"
    EV_CHARGER = "ev_charger"
    HVAC = "hvac"
    LIGHTING = "lighting"
    APPLIANCE = "appliance"


class DeviceStatus(str, enum.Enum):
    """设备状态枚举"""

    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class Device(Base):
    """设备信息表"""

    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    device_type = Column(SQLEnum(DeviceType), nullable=False)
    location = Column(String(500))
    latitude = Column(Float)
    longitude = Column(Float)
    status = Column(SQLEnum(DeviceStatus), default=DeviceStatus.ONLINE)
    is_active = Column(Boolean, default=True)
    manufacturer = Column(String(200))
    model = Column(String(200))
    firmware_version = Column(String(50))
    installation_date = Column(DateTime)
    last_seen = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    readings = relationship("EnergyReading", back_populates="device")

    def __repr__(self):
        return f"<Device(id={self.id}, device_id={self.device_id}, name={self.name})>"
