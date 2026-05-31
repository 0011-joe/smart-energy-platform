import asyncio
import json
import logging
from datetime import datetime
from typing import Callable, Optional

import paho.mqtt.client as mqtt
from app.core.config import settings
from app.core.database import async_session
from app.models.device import Device
from app.models.energy_reading import EnergyReading

logger = logging.getLogger(__name__)


class MQTTClient:
    """MQTT客户端 - 订阅设备能耗数据"""

    def __init__(self):
        self.client = mqtt.Client(client_id="smart-energy-api", protocol=mqtt.MQTTv311)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        self._connected = False
        self._message_handler: Optional[Callable] = None

    def _on_connect(self, client, userdata, flags, rc):
        """连接回调"""
        if rc == 0:
            logger.info("Connected to MQTT Broker successfully")
            self._connected = True
            # 订阅所有设备的能耗数据主题
            client.subscribe(settings.MQTT_TOPIC)
            logger.info(f"Subscribed to topic: {settings.MQTT_TOPIC}")
        else:
            logger.error(f"Failed to connect to MQTT Broker, return code: {rc}")

    def _on_message(self, client, userdata, msg):
        """消息回调"""
        try:
            payload = json.loads(msg.payload.decode())
            logger.info(f"Received message from {msg.topic}: {payload}")

            # 提取device_id从主题 (energy/devices/{device_id}/readings)
            topic_parts = msg.topic.split("/")
            if len(topic_parts) >= 3:
                device_id = topic_parts[2]
                payload["device_id"] = device_id

            # 使用异步处理
            asyncio.create_task(self._process_message(payload))

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON message: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def _process_message(self, payload: dict):
        """异步处理MQTT消息"""
        try:
            async with async_session() as session:
                # 检查设备是否存在
                device_id = payload.get("device_id")
                if not device_id:
                    logger.warning("Message missing device_id")
                    return

                device_query = await session.execute(
                    Device.__table__.select().where(Device.device_id == device_id)
                )
                device = device_query.scalar_one_or_none()

                # 自动创建设备记录
                if not device:
                    device = Device(
                        device_id=device_id,
                        name=f"Device {device_id}",
                        device_type=payload.get("device_type", "appliance"),
                    )
                    session.add(device)
                    await session.flush()

                # 创建能耗读数记录
                reading = EnergyReading(
                    device_id=device_id,
                    timestamp=datetime.fromisoformat(
                        payload.get("timestamp", datetime.utcnow().isoformat())
                    ),
                    power_watts=payload.get("power_watts", 0),
                    energy_kwh=payload.get("energy_kwh"),
                    voltage=payload.get("voltage"),
                    current_amps=payload.get("current_amps"),
                    frequency_hz=payload.get("frequency_hz"),
                    power_factor=payload.get("power_factor"),
                    metadata=payload.get("metadata"),
                )
                session.add(reading)

                # 更新设备最后在线时间
                device.last_seen = datetime.utcnow()

                await session.commit()
                logger.info(
                    f"Saved reading for device {device_id}: {payload.get('power_watts')}W"
                )

        except Exception as e:
            logger.error(f"Error saving reading to database: {e}")
            await session.rollback()

    def _on_disconnect(self, client, userdata, rc):
        """断开连接回调"""
        self._connected = False
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection, return code: {rc}")

    async def connect(self):
        """连接到MQTT Broker"""
        try:
            logger.info(
                f"Connecting to MQTT Broker at {settings.MQTT_BROKER}:{settings.MQTT_PORT}"
            )
            self.client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, keepalive=60)
            self.client.loop_start()
            logger.info("MQTT client started")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT Broker: {e}")
            raise

    async def disconnect(self):
        """断开MQTT连接"""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT client disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting MQTT client: {e}")

    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected

    def publish(self, topic: str, payload: dict):
        """发布消息到MQTT主题"""
        try:
            message = json.dumps(payload)
            result = self.client.publish(topic, message)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published message to {topic}")
            else:
                logger.error(f"Failed to publish message to {topic}")
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
