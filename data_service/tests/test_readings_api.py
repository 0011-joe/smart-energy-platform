"""
能耗读数API测试

测试POST /api/readings和相关端点
"""

import pytest


@pytest.mark.asyncio
async def test_create_reading(client, sample_reading_data):
    """测试创建单条读数"""
    response = await client.post("/api/readings/", json=sample_reading_data)

    assert response.status_code == 201
    data = response.json()
    assert data["device_id"] == sample_reading_data["device_id"]
    assert data["power_watts"] == sample_reading_data["power_watts"]
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_reading_invalid_power(client):
    """测试创建读数时功率为负数（应失败）"""
    reading_data = {
        "device_id": "test_device",
        "power_watts": -100  # 负功率应被拒绝
    }
    response = await client.post("/api/readings/", json=reading_data)
    assert response.status_code == 422  # 验证错误


@pytest.mark.asyncio
async def test_create_reading_missing_device_id(client):
    """测试创建读数时缺少设备ID（应失败）"""
    reading_data = {
        "power_watts": 1000.0
    }
    response = await client.post("/api/readings/", json=reading_data)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_reading_auto_device(client, sample_reading_data):
    """测试创建读数时自动创建设备"""
    # 第一次创建读数
    response1 = await client.post("/api/readings/", json=sample_reading_data)
    assert response1.status_code == 201

    # 检查设备是否被自动创建
    response2 = await client.get(f"/api/devices/{sample_reading_data['device_id']}")
    assert response2.status_code == 200
    assert response2.json()["device_id"] == sample_reading_data["device_id"]


@pytest.mark.asyncio
async def test_create_readings_batch(client, sample_readings_batch):
    """测试批量创建读数"""
    response = await client.post("/api/readings/batch", json=sample_readings_batch)

    assert response.status_code == 201
    data = response.json()
    assert data["created"] == 10
    assert data["total"] == 10


@pytest.mark.asyncio
async def test_get_readings(client, sample_reading_data):
    """测试获取读数列表"""
    # 先创建一条读数
    await client.post("/api/readings/", json=sample_reading_data)

    # 获取读数列表
    response = await client.get("/api/readings/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_get_readings_with_filters(client, sample_reading_data):
    """测试带过滤条件获取读数"""
    # 先创建读数
    await client.post("/api/readings/", json=sample_reading_data)

    # 带设备ID过滤
    response = await client.get(
        "/api/readings/",
        params={"device_id": sample_reading_data["device_id"]}
    )

    assert response.status_code == 200
    data = response.json()
    assert all(r["device_id"] == sample_reading_data["device_id"] for r in data)


@pytest.mark.asyncio
async def test_get_device_summary(client, sample_reading_data):
    """测试获取设备汇总"""
    # 先创建读数
    await client.post("/api/readings/", json=sample_reading_data)

    # 获取汇总
    response = await client.get(
        f"/api/readings/device/{sample_reading_data['device_id']}/summary",
        params={"hours": 24}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["device_id"] == sample_reading_data["device_id"]
    assert "total_readings" in data
    assert "avg_power" in data


@pytest.mark.asyncio
async def test_delete_reading(client, sample_reading_data):
    """测试删除读数"""
    # 先创建读数
    create_response = await client.post("/api/readings/", json=sample_reading_data)
    reading_id = create_response.json()["id"]

    # 删除读数
    delete_response = await client.delete(f"/api/readings/{reading_id}")
    assert delete_response.status_code == 204


@pytest.mark.asyncio
async def test_delete_nonexistent_reading(client):
    """测试删除不存在的读数（应返回404）"""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.delete(f"/api/readings/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_readings_health_check(client):
    """测试读数服务健康检查"""
    response = await client.get("/api/readings/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"