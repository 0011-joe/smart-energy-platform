import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class EnergyReading(Base):
    """能耗读数表 - PostgreSQL存储元数据"""

    __tablename__ = "energy_readings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(
        String(100), ForeignKey("devices.device_id"), nullable=False, index=True
    )
    timestamp = Column(DateTime, nullable=False, index=True)
    power_watts = Column(Float, nullable=False)  # 瞬时功率(瓦)
    energy_kwh = Column(Float)  # 累计电量(千瓦时)
    voltage = Column(Float)  # 电压(伏)
    current_amps = Column(Float)  # 电流(安)
    frequency_hz = Column(Float)  # 频率(赫兹)
    power_factor = Column(Float)  # 功率因数
    metadata = Column(JSON)  # 额外元数据
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    device = relationship("Device", back_populates="readings")

    def __repr__(self):
        return f"<EnergyReading(device_id={self.device_id}, power={self.power_watts}W)>"
