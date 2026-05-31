from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EnergyReadingCreate(BaseModel):
    """能耗数据创建请求模型"""

    device_id: str = Field(..., description="设备唯一标识", examples=["device_001"])
    timestamp: Optional[datetime] = Field(
        default_factory=datetime.utcnow, description="数据时间戳"
    )
    power_watts: float = Field(..., ge=0, description="瞬时功率(瓦)", examples=[1500.5])
    energy_kwh: Optional[float] = Field(None, ge=0, description="累计电量(千瓦时)")
    voltage: Optional[float] = Field(None, ge=0, le=500, description="电压(伏)")
    current_amps: Optional[float] = Field(None, ge=0, description="电流(安)")
    frequency_hz: Optional[float] = Field(None, ge=45, le=65, description="频率(赫兹)")
    power_factor: Optional[float] = Field(None, ge=-1, le=1, description="功率因数")
    metadata: Optional[Dict] = Field(None, description="额外元数据")

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "device_001",
                "power_watts": 1500.5,
                "energy_kwh": 45.2,
                "voltage": 220.0,
                "current_amps": 6.82,
                "frequency_hz": 50.0,
                "power_factor": 0.95,
                "metadata": {"temperature": 25.5, "humidity": 60}
            }
        }


class EnergyReadingResponse(BaseModel):
    """能耗数据响应模型"""
    id: UUID
    device_id: str
    timestamp: datetime
    power_watts: float
    energy_kwh: Optional[float]
    voltage: Optional[float]
    current_amps: Optional[float]
    frequency_hz: Optional[float]
    power_factor: Optional[float]
    metadata: Optional[Dict]
    created_at: datetime

    class Config:
        from_attributes = True


class EnergyReadingBatch(BaseModel):
    """批量能耗数据请求模型"""
    readings: List[EnergyReadingCreate] = Field(..., min_length=1, max_length=1000)


class DeviceReadingSummary(BaseModel):
    """设备读数汇总"""
    device_id: str
    total_readings: int
    avg_power: float
    max_power: float
    min_power: float
    total_energy_kwh: float
    first_reading: datetime
    last_reading: datetime


class ReadingQueryParams(BaseModel):
    """读数查询参数"""
    device_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=10000)
    offset: int = Field(0, ge=0)