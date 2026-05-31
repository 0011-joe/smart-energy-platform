from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID
import logging

from app.core.database import get_db, get_influx_write_api, get_influx_query_api
from app.core.config import settings
from app.models.energy_reading import EnergyReading
from app.models.device import Device
from app.schemas.reading import (
    EnergyReadingCreate,
    EnergyReadingResponse,
    EnergyReadingBatch,
    DeviceReadingSummary,
    ReadingQueryParams
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=EnergyReadingResponse, status_code=201)
async def create_reading(
    reading: EnergyReadingCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建单条能耗读数

    - **device_id**: 设备唯一标识
    - **power_watts**: 瞬时功率(瓦)，必须大于等于0
    - **energy_kwh**: 累计电量(千瓦时)
    - **voltage**: 电压(伏)
    - **current_amps**: 电流(安)
    """
    try:
        # 检查设备是否存在，不存在则自动创建
        device_query = select(Device).where(Device.device_id == reading.device_id)
        result = await db.execute(device_query)
        device = result.scalar_one_or_none()

        if not device:
            device = Device(
                device_id=reading.device_id,
                name=f"Device {reading.device_id}",
                device_type="appliance"
            )
            db.add(device)
            await db.flush()

        # 创建PostgreSQL记录
        db_reading = EnergyReading(
            device_id=reading.device_id,
            timestamp=reading.timestamp or datetime.utcnow(),
            power_watts=reading.power_watts,
            energy_kwh=reading.energy_kwh,
            voltage=reading.voltage,
            current_amps=reading.current_amps,
            frequency_hz=reading.frequency_hz,
            power_factor=reading.power_factor,
            metadata=reading.metadata
        )
        db.add(db_reading)
        await db.flush()
        await db.refresh(db_reading)

        # 写入InfluxDB时序数据
        try:
            write_api = get_influx_write_api()
            point = {
                "measurement": "energy_reading",
                "tags": {
                    "device_id": reading.device_id,
                    "device_type": device.device_type.value if device.device_type else "unknown"
                },
                "fields": {
                    "power_watts": reading.power_watts,
                    "energy_kwh": reading.energy_kwh or 0.0,
                    "voltage": reading.voltage or 0.0,
                    "current_amps": reading.current_amps or 0.0,
                    "frequency_hz": reading.frequency_hz or 50.0,
                    "power_factor": reading.power_factor or 1.0
                },
                "time": db_reading.timestamp
            }
            write_api.write(
                bucket=settings.INFLUXDB_BUCKET,
                org=settings.INFLUXDB_ORG,
                record=point
            )
        except Exception as e:
            logger.warning(f"Failed to write to InfluxDB: {e}")

        # 更新设备最后在线时间
        device.last_seen = datetime.utcnow()
        await db.commit()

        return db_reading

    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating reading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=dict, status_code=201)
async def create_readings_batch(
    batch: EnergyReadingBatch,
    db: AsyncSession = Depends(get_db)
):
    """
    批量创建能耗读数

    - **readings**: 读数列表，最多1000条
    """
    try:
        created_count = 0
        errors = []

        for i, reading in enumerate(batch.readings):
            try:
                db_reading = EnergyReading(
                    device_id=reading.device_id,
                    timestamp=reading.timestamp or datetime.utcnow(),
                    power_watts=reading.power_watts,
                    energy_kwh=reading.energy_kwh,
                    voltage=reading.voltage,
                    current_amps=reading.current_amps,
                    frequency_hz=reading.frequency_hz,
                    power_factor=reading.power_factor,
                    metadata=reading.metadata
                )
                db.add(db_reading)
                created_count += 1
            except Exception as e:
                errors.append({"index": i, "error": str(e)})

        await db.commit()

        return {
            "created": created_count,
            "errors": errors,
            "total": len(batch.readings)
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[EnergyReadingResponse])
async def get_readings(
    device_id: Optional[str] = Query(None, description="设备ID筛选"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=10000, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: AsyncSession = Depends(get_db)
):
    """
    查询能耗读数列表

    - **device_id**: 按设备ID筛选
    - **start_time**: 开始时间
    - **end_time**: 结束时间
    - **limit**: 返回数量限制(1-10000)
    - **offset**: 偏移量
    """
    query = select(EnergyReading)

    if device_id:
        query = query.where(EnergyReading.device_id == device_id)
    if start_time:
        query = query.where(EnergyReading.timestamp >= start_time)
    if end_time:
        query = query.where(EnergyReading.timestamp <= end_time)

    query = query.order_by(EnergyReading.timestamp.desc())
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    readings = result.scalars().all()

    return readings


@router.get("/device/{device_id}/summary", response_model=DeviceReadingSummary)
async def get_device_summary(
    device_id: str,
    hours: int = Query(24, ge=1, le=720, description="统计时间范围(小时)"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取设备能耗汇总统计

    - **device_id**: 设备ID
    - **hours**: 统计时间范围，默认24小时
    """
    start_time = datetime.utcnow() - timedelta(hours=hours)

    query = select(
        func.count(EnergyReading.id).label("total_readings"),
        func.avg(EnergyReading.power_watts).label("avg_power"),
        func.max(EnergyReading.power_watts).label("max_power"),
        func.min(EnergyReading.power_watts).label("min_power"),
        func.sum(EnergyReading.energy_kwh).label("total_energy"),
        func.min(EnergyReading.timestamp).label("first_reading"),
        func.max(EnergyReading.timestamp).label("last_reading")
    ).where(
        EnergyReading.device_id == device_id,
        EnergyReading.timestamp >= start_time
    )

    result = await db.execute(query)
    row = result.one()

    if row.total_readings == 0:
        raise HTTPException(status_code=404, detail="No readings found for this device")

    return DeviceReadingSummary(
        device_id=device_id,
        total_readings=row.total_readings,
        avg_power=round(row.avg_power or 0, 2),
        max_power=round(row.max_power or 0, 2),
        min_power=round(row.min_power or 0, 2),
        total_energy_kwh=round(row.total_energy or 0, 4),
        first_reading=row.first_reading,
        last_reading=row.last_reading
    )


@router.get("/device/{device_id}", response_model=List[EnergyReadingResponse])
async def get_device_readings(
    device_id: str,
    hours: int = Query(24, ge=1, le=720),
    limit: int = Query(100, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """获取指定设备的最近读数"""
    start_time = datetime.utcnow() - timedelta(hours=hours)

    query = select(EnergyReading).where(
        EnergyReading.device_id == device_id,
        EnergyReading.timestamp >= start_time
    ).order_by(
        EnergyReading.timestamp.desc()
    ).limit(limit)

    result = await db.execute(query)
    readings = result.scalars().all()

    return readings


@router.delete("/{reading_id}", status_code=204)
async def delete_reading(
    reading_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """删除指定读数"""
    query = select(EnergyReading).where(EnergyReading.id == reading_id)
    result = await db.execute(query)
    reading = result.scalar_one_or_none()

    if not reading:
        raise HTTPException(status_code=404, detail="Reading not found")

    await db.delete(reading)
    await db.commit()


@router.get("/health")
async def readings_health():
    """读数服务健康检查"""
    return {"status": "healthy", "service": "readings"}