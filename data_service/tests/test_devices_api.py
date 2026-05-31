"""
设备API测试

测试GET /api/devices和相关端点
"""

from datetime import datetime, timedelta

import pytest


@pytest.mark.asyncio
async def test_get_devices_empty(client):
    """测试获取空设备列表"""
    response = await client.get("/api/devices/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_get_devices_with_data(client, sample_reading_data):
    """测试获取设备列表（有数据）"""
    # 先通过创建读数来自动创建设备
    await client.post("/api/readings/", json=sample_reading_data)

    # 获取设备列表
    response = await client.get("/api/devices/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["device_id"] == sample_reading_data["device_id"]


@pytest.mark.asyncio
async def test_get_device_by_id(client, sample_reading_data):
    """测试通过ID获取设备"""
    # 先创建设备数据
    await client.post("/api/readings/", json=sample_reading_data)

    # 获取设备详情
    response = await client.get(f"/api/devices/{sample_reading_data['device_id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["device_id"] == sample_reading_data["device_id"]


@pytest.mark.asyncio
async def test_get_nonexistent_device(client):
    """测试获取不存在的设备（应返回404）"""
    response = await client.get("/api/devices/nonexistent_device")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_device_readings(client, sample_reading_data):
    """测试获取设备读数"""
    # 先创建读数
    await client.post("/api/readings/", json=sample_reading_data)

    # 获取设备读数
    response = await client.get(
        f"/api/devices/{sample_reading_data['device_id']}/readings"
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_get_device_readings_with_time_range(client, sample_reading_data):
    """测试带时间范围查询设备读数"""
    # 先创建读数
    await client.post("/api/readings/", json=sample_reading_data)

    # 获取设备读数（带时间范围）
    now = datetime.utcnow()
    start_time = (now - timedelta(hours=1)).isoformat()
    end_time = (now + timedelta(hours=1)).isoformat()

    response = await client.get(
        f"/api/devices/{sample_reading_data['device_id']}/readings",
        params={"start_time": start_time, "end_time": end_time, "limit": 100},
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_device_readings_nonexistent(client):
    """测试获取不存在设备的读数（应返回404）"""
    response = await client.get("/api/devices/nonexistent_device/readings")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_device_hourly_stats(client, sample_reading_data):
    """测试获取设备小时统计"""
    # 先创建读数
    await client.post("/api/readings/", json=sample_reading_data)

    # 获取小时统计
    response = await client.get(
        f"/api/devices/{sample_reading_data['device_id']}/readings/hourly",
        params={"hours": 24},
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_device_daily_stats(client, sample_reading_data):
    """测试获取设备日统计"""
    # 先创建读数
    await client.post("/api/readings/", json=sample_reading_data)

    # 获取日统计
    response = await client.get(
        f"/api/devices/{sample_reading_data['device_id']}/readings/daily",
        params={"days": 7},
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_devices_with_type_filter(client, sample_reading_data):
    """测试按类型过滤设备"""
    # 先创建设备
    await client.post("/api/readings/", json=sample_reading_data)

    # 按类型过滤
    response = await client.get("/api/devices/", params={"device_type": "smart_meter"})

    assert response.status_code == 200
    data = response.json()
    # 验证返回的设备类型都是smart_meter
    for device in data:
        assert device["device_type"] == "smart_meter"


@pytest.mark.asyncio
async def test_get_devices_with_status_filter(client, sample_reading_data):
    """测试按状态过滤设备"""
    # 先创建设备
    await client.post("/api/readings/", json=sample_reading_data)

    # 按状态过滤
    response = await client.get("/api/devices/", params={"status": "online"})

    assert response.status_code == 200
    data = response.json()
    # 验证返回的设备状态都是online
    for device in data:
        assert device["status"] == "online"
