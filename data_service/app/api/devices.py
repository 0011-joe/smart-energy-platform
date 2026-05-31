from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.device import Device, DeviceStatus, DeviceType
from app.models.energy_reading import EnergyReading
from app.schemas.reading import EnergyReadingResponse

router = APIRouter()


@router.get("/", response_model=List[dict])
async def get_devices(
    device_type: Optional[DeviceType] = Query(None, description="设备类型筛选"),
    status: Optional[DeviceStatus] = Query(None, description="设备状态筛选"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    获取设备列表

    - **device_type**: 按设备类型筛选
    - **status**: 按设备状态筛选
    - **is_active**: 按激活状态筛选
    - **limit**: 返回数量限制
    - **offset**: 偏移量
    """
    query = select(Device)

    if device_type:
        query = query.where(Device.device_type == device_type)
    if status:
        query = query.where(Device.status == status)
    if is_active is not None:
        query = query.where(Device.is_active == is_active)

    query = query.order_by(Device.created_at.desc())
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    devices = result.scalars().all()

    return [
        {
            "id": str(device.id),
            "device_id": device.device_id,
            "name": device.name,
            "device_type": device.device_type.value,
            "location": device.location,
            "status": device.status.value,
            "is_active": device.is_active,
            "manufacturer": device.manufacturer,
            "model": device.model,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
            "created_at": device.created_at.isoformat(),
        }
        for device in devices
    ]


@router.get("/{device_id}", response_model=dict)
async def get_device(device_id: str, db: AsyncSession = Depends(get_db)):
    """
    获取单个设备详情

    - **device_id**: 设备唯一标识
    """
    query = select(Device).where(Device.device_id == device_id)
    result = await db.execute(query)
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    return {
        "id": str(device.id),
        "device_id": device.device_id,
        "name": device.name,
        "device_type": device.device_type.value,
        "location": device.location,
        "latitude": device.latitude,
        "longitude": device.longitude,
        "status": device.status.value,
        "is_active": device.is_active,
        "manufacturer": device.manufacturer,
        "model": device.model,
        "firmware_version": device.firmware_version,
        "installation_date": (
            device.installation_date.isoformat() if device.installation_date else None
        ),
        "last_seen": device.last_seen.isoformat() if device.last_seen else None,
        "created_at": device.created_at.isoformat(),
        "updated_at": device.updated_at.isoformat(),
    }


@router.get("/{device_id}/readings", response_model=List[EnergyReadingResponse])
async def get_device_readings(
    device_id: str,
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    获取指定设备的能耗读数（支持时间范围查询）

    - **device_id**: 设备唯一标识
    - **start_time**: 开始时间（ISO格式）
    - **end_time**: 结束时间（ISO格式）
    - **limit**: 返回数量限制
    - **offset**: 偏移量
    """
    # 检查设备是否存在
    device_query = select(Device).where(Device.device_id == device_id)
    device_result = await db.execute(device_query)
    device = device_result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # 构建查询
    query = select(EnergyReading).where(EnergyReading.device_id == device_id)

    if start_time:
        query = query.where(EnergyReading.timestamp >= start_time)
    if end_time:
        query = query.where(EnergyReading.timestamp <= end_time)

    query = query.order_by(EnergyReading.timestamp.desc())
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    readings = result.scalars().all()

    return readings


@router.get("/{device_id}/readings/hourly")
async def get_device_hourly_stats(
    device_id: str,
    hours: int = Query(24, ge=1, le=720),
    db: AsyncSession = Depends(get_db),
):
    """
    获取设备按小时聚合的能耗统计

    - **device_id**: 设备唯一标识
    - **hours**: 统计时间范围（小时）
    """
    start_time = datetime.utcnow() - timedelta(hours=hours)

    query = (
        select(
            func.date_trunc("hour", EnergyReading.timestamp).label("hour"),
            func.avg(EnergyReading.power_watts).label("avg_power"),
            func.max(EnergyReading.power_watts).label("max_power"),
            func.min(EnergyReading.power_watts).label("min_power"),
            func.sum(EnergyReading.energy_kwh).label("total_energy"),
            func.count(EnergyReading.id).label("reading_count"),
        )
        .where(
            EnergyReading.device_id == device_id, EnergyReading.timestamp >= start_time
        )
        .group_by(func.date_trunc("hour", EnergyReading.timestamp))
        .order_by(func.date_trunc("hour", EnergyReading.timestamp).desc())
    )

    result = await db.execute(query)
    stats = result.all()

    return [
        {
            "hour": stat.hour.isoformat(),
            "avg_power": round(float(stat.avg_power or 0), 2),
            "max_power": round(float(stat.max_power or 0), 2),
            "min_power": round(float(stat.min_power or 0), 2),
            "total_energy_kwh": round(float(stat.total_energy or 0), 4),
            "reading_count": stat.reading_count,
        }
        for stat in stats
    ]


@router.get("/{device_id}/readings/daily")
async def get_device_daily_stats(
    device_id: str,
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """
    获取设备按天聚合的能耗统计

    - **device_id**: 设备唯一标识
    - **days**: 统计时间范围（天）
    """
    start_time = datetime.utcnow() - timedelta(days=days)

    query = (
        select(
            func.date_trunc("day", EnergyReading.timestamp).label("day"),
            func.avg(EnergyReading.power_watts).label("avg_power"),
            func.max(EnergyReading.power_watts).label("max_power"),
            func.min(EnergyReading.power_watts).label("min_power"),
            func.sum(EnergyReading.energy_kwh).label("total_energy"),
            func.count(EnergyReading.id).label("reading_count"),
        )
        .where(
            EnergyReading.device_id == device_id, EnergyReading.timestamp >= start_time
        )
        .group_by(func.date_trunc("day", EnergyReading.timestamp))
        .order_by(func.date_trunc("day", EnergyReading.timestamp).desc())
    )

    result = await db.execute(query)
    stats = result.all()

    return [
        {
            "day": stat.day.strftime("%Y-%m-%d"),
            "avg_power": round(float(stat.avg_power or 0), 2),
            "max_power": round(float(stat.max_power or 0), 2),
            "min_power": round(float(stat.min_power or 0), 2),
            "total_energy_kwh": round(float(stat.total_energy or 0), 4),
            "reading_count": stat.reading_count,
        }
        for stat in stats
    ]
