"""
Smart Energy Platform - FastAPI数据服务

提供设备能耗数据采集、存储和查询的RESTful API
"""

import logging
from contextlib import asynccontextmanager

from app.api.device_types import router as device_types_router
from app.api.devices import router as devices_router
from app.api.readings import router as readings_router
from app.core.config import settings
from app.core.database import init_db
from app.services.mqtt_client import MQTTClient
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    logger.info("Initializing database...")
    await init_db()

    # 初始化缓存
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
    logger.info("Cache initialized")

    # 启动MQTT客户端
    mqtt_client = MQTTClient()
    try:
        await mqtt_client.connect()
        app.state.mqtt_client = mqtt_client
        logger.info("MQTT client connected successfully")
    except Exception as e:
        logger.warning(f"MQTT client failed to connect: {e}")
        app.state.mqtt_client = None

    yield

    # 关闭时清理资源
    if app.state.mqtt_client:
        await app.state.mqtt_client.disconnect()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="Smart Energy Platform API",
    description="""
    智能能源管理平台数据服务API

    ## 功能特性

    * **设备管理** - 注册、查询和管理智能设备
    * **能耗数据** - 采集、存储和查询设备能耗数据
    * **数据分析** - 提供小时/天粒度的统计分析
    * **设备类型** - 动态设备类型配置

    ## 技术栈

    * **FastAPI** - 高性能异步Web框架
    * **SQLAlchemy** - 异步ORM
    * **PostgreSQL** - 关系型数据库
    * **InfluxDB** - 时序数据库
    * **MQTT** - IoT消息协议
    * **Redis** - 缓存
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "能耗数据", "description": "能耗数据的采集和查询"},
        {"name": "设备管理", "description": "设备的注册和管理"},
        {"name": "设备类型", "description": "设备类型配置管理"},
    ],
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(readings_router, prefix="/api/readings", tags=["能耗数据"])
app.include_router(devices_router, prefix="/api/devices", tags=["设备管理"])
app.include_router(device_types_router, prefix="/api/device-types", tags=["设备类型"])


@app.get("/")
async def root():
    """服务根路径"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "readings": "/api/readings",
            "devices": "/api/devices",
            "device_types": "/api/device-types",
        },
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "data_service",
        "version": settings.APP_VERSION,
    }


@app.get("/api/status")
async def api_status():
    """API状态信息"""
    mqtt_connected = app.state.mqtt_client and app.state.mqtt_client.is_connected
    mqtt_status = "connected" if mqtt_connected else "disconnected"
    return {
        "api": "running",
        "mqtt": mqtt_status,
        "database": "postgresql",
        "timeseries_db": "influxdb",
        "cache": "in-memory",
    }
