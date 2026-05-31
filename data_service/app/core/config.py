from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "Smart Energy Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 数据库配置 - PostgreSQL
    DATABASE_URL: str = (
        "postgresql://energy_admin:secure_password_123@localhost:5432/smart_energy"
    )

    # InfluxDB配置
    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_TOKEN: str = "my-super-secret-token"
    INFLUXDB_ORG: str = "smart-energy"
    INFLUXDB_BUCKET: str = "energy_data"

    # MQTT配置
    MQTT_BROKER: str = "localhost"
    MQTT_PORT: int = 1883
    MQTT_TOPIC: str = "energy/devices/+/readings"

    # CORS配置
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
