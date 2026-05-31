"""
设备类型API

提供设备类型配置的CRUD操作
"""

from typing import List

from app.core.database import get_db
from app.models.device_type import DEFAULT_DEVICE_TYPES, DeviceTypeConfig
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


class DeviceTypeCreate(BaseModel):
    """设备类型创建请求"""

    type_key: str
    display_name: str
    description: str = None
    category: str = "general"
    icon: str = "device"
    color: str = "#0ea5e9"
    capabilities: List[str] = []
    control_components: List[dict] = []
    data_fields: List[dict] = []
    matter_device_type: int = None
    matter_clusters: List[int] = []


class DeviceTypeUpdate(BaseModel):
    """设备类型更新请求"""

    display_name: str = None
    description: str = None
    category: str = None
    icon: str = None
    color: str = None
    capabilities: List[str] = None
    control_components: List[dict] = None
    data_fields: List[dict] = None
    is_active: bool = None


@router.get("/", response_model=List[dict])
async def get_device_types(
    category: str = None, is_active: bool = True, db: AsyncSession = Depends(get_db)
):
    """
    获取所有设备类型配置

    - **category**: 按分类过滤
    - **is_active**: 是否只返回激活的类型
    """
    query = select(DeviceTypeConfig)

    if category:
        query = query.where(DeviceTypeConfig.category == category)
    if is_active is not None:
        query = query.where(DeviceTypeConfig.is_active == is_active)

    query = query.order_by(DeviceTypeConfig.type_key)

    result = await db.execute(query)
    device_types = result.scalars().all()

    return [dt.to_dict() for dt in device_types]


@router.get("/{type_key}", response_model=dict)
async def get_device_type(type_key: str, db: AsyncSession = Depends(get_db)):
    """获取指定设备类型配置"""
    query = select(DeviceTypeConfig).where(DeviceTypeConfig.type_key == type_key)
    result = await db.execute(query)
    device_type = result.scalar_one_or_none()

    if not device_type:
        raise HTTPException(status_code=404, detail="Device type not found")

    return device_type.to_dict()


@router.post("/", response_model=dict, status_code=201)
async def create_device_type(
    device_type: DeviceTypeCreate, db: AsyncSession = Depends(get_db)
):
    """创建新的设备类型"""
    # 检查是否已存在
    query = select(DeviceTypeConfig).where(
        DeviceTypeConfig.type_key == device_type.type_key
    )
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Device type already exists")

    # 创建新类型
    new_type = DeviceTypeConfig(**device_type.model_dump())
    db.add(new_type)
    await db.commit()
    await db.refresh(new_type)

    return new_type.to_dict()


@router.put("/{type_key}", response_model=dict)
async def update_device_type(
    type_key: str, update_data: DeviceTypeUpdate, db: AsyncSession = Depends(get_db)
):
    """更新设备类型配置"""
    query = select(DeviceTypeConfig).where(DeviceTypeConfig.type_key == type_key)
    result = await db.execute(query)
    device_type = result.scalar_one_or_none()

    if not device_type:
        raise HTTPException(status_code=404, detail="Device type not found")

    # 更新字段
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(device_type, key, value)

    await db.commit()
    await db.refresh(device_type)

    return device_type.to_dict()


@router.delete("/{type_key}", status_code=204)
async def delete_device_type(type_key: str, db: AsyncSession = Depends(get_db)):
    """删除设备类型（软删除，设置为非激活）"""
    query = select(DeviceTypeConfig).where(DeviceTypeConfig.type_key == type_key)
    result = await db.execute(query)
    device_type = result.scalar_one_or_none()

    if not device_type:
        raise HTTPException(status_code=404, detail="Device type not found")

    device_type.is_active = False
    await db.commit()


@router.post("/init-defaults", response_model=dict)
async def initialize_default_types(db: AsyncSession = Depends(get_db)):
    """初始化默认设备类型"""
    created = 0
    skipped = 0

    for type_data in DEFAULT_DEVICE_TYPES:
        query = select(DeviceTypeConfig).where(
            DeviceTypeConfig.type_key == type_data["type_key"]
        )
        result = await db.execute(query)
        if result.scalar_one_or_none():
            skipped += 1
            continue

        new_type = DeviceTypeConfig(**type_data)
        db.add(new_type)
        created += 1

    await db.commit()

    return {"created": created, "skipped": skipped, "total": len(DEFAULT_DEVICE_TYPES)}
