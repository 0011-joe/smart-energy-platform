"""
测试配置模块

提供测试夹具（fixtures）和配置
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient, ASGITransport

from app.core.database import Base, get_db
from app.core.config import settings
from main import app


# 测试数据库URL（使用SQLite内存数据库）
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


# 创建测试引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool
)

# 测试会话工厂
test_async_session = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_database():
    """每个测试前创建数据库表，测试后清理"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """覆盖数据库依赖"""
    async with test_async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取测试数据库会话"""
    async with test_async_session() as session:
        yield session


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """获取测试客户端"""
    # 覆盖数据库依赖
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # 清理依赖覆盖
    app.dependency_overrides.clear()


@pytest.fixture
def sample_device_data():
    """示例设备数据"""
    return {
        "device_id": "test_device_001",
        "name": "Test Smart Meter",
        "device_type": "smart_meter",
        "location": "Test Location",
        "is_active": True
    }


@pytest.fixture
def sample_reading_data():
    """示例读数数据"""
    return {
        "device_id": "test_device_001",
        "power_watts": 1500.5,
        "energy_kwh": 45.2,
        "voltage": 220.0,
        "current_amps": 6.82,
        "frequency_hz": 50.0,
        "power_factor": 0.95,
        "timestamp": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_readings_batch():
    """批量读数数据"""
    readings = []
    for i in range(10):
        readings.append({
            "device_id": "test_device_001",
            "power_watts": 1000.0 + i * 100,
            "energy_kwh": 10.0 + i,
            "voltage": 220.0,
            "current_amps": 4.5 + i * 0.5,
            "timestamp": datetime.utcnow().isoformat()
        })
    return {"readings": readings}