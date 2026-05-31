from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# PostgreSQL异步引擎
_db_url = settings.DATABASE_URL
if _db_url.startswith("postgresql://"):
    _db_url = _db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    _db_url, echo=settings.DEBUG, pool_size=20, max_overflow=10
)

# 异步会话工厂
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# SQLAlchemy基类
class Base(DeclarativeBase):
    pass


# InfluxDB客户端（延迟初始化，避免导入时连接失败）
_influx_client = None
_write_api = None
_query_api = None


def _get_influx_client():
    """获取InfluxDB客户端（延迟初始化）"""
    global _influx_client, _write_api, _query_api
    if _influx_client is None:
        from influxdb_client import InfluxDBClient
        from influxdb_client.client.write_api import SYNCHRONOUS

        _influx_client = InfluxDBClient(
            url=settings.INFLUXDB_URL,
            token=settings.INFLUXDB_TOKEN,
            org=settings.INFLUXDB_ORG,
        )
        _write_api = _influx_client.write_api(write_options=SYNCHRONOUS)
        _query_api = _influx_client.query_api()
    return _influx_client


async def init_db():
    """初始化数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """获取数据库会话"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_influx_write_api():
    """获取InfluxDB写入API"""
    _get_influx_client()
    return _write_api


def get_influx_query_api():
    """获取InfluxDB查询API"""
    _get_influx_client()
    return _query_api
