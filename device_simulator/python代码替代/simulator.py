#!/usr/bin/env python3
"""
智能能源设备模拟器
模拟多种智能家居设备，定时发布能耗数据到MQTT Broker
"""

import paho.mqtt.client as mqtt
import json
import time
import random
import logging
import os
import schedule
from datetime import datetime, timezone
from typing import Dict, List, Optional
import threading

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MQTT配置
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
API_URL = os.getenv("API_URL", "http://localhost:8000")

# 发布间隔（秒）
PUBLISH_INTERVAL = int(os.getenv("PUBLISH_INTERVAL", "10"))


class SimulatedDevice:
    """模拟设备基类"""

    def __init__(self, device_id: str, device_type: str, name: str):
        self.device_id = device_id
        self.device_type = device_type
        self.name = name
        self.is_on = True
        self.base_power = 0.0
        self.voltage = 220.0

    def generate_reading(self) -> Dict:
        """生成设备读数"""
        if not self.is_on:
            return {
                "device_id": self.device_id,
                "device_type": self.device_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "power_watts": 0.0,
                "energy_kwh": 0.0,
                "voltage": self.voltage,
                "current_amps": 0.0,
                "frequency_hz": 50.0,
                "power_factor": 0.0
            }

        # 添加随机波动
        power = self.base_power * (0.8 + random.random() * 0.4)
        current = power / self.voltage
        energy_increment = power / 3600 * PUBLISH_INTERVAL / 1000

        return {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "power_watts": round(power, 2),
            "energy_kwh": round(energy_increment, 6),
            "voltage": round(self.voltage + random.uniform(-5, 5), 1),
            "current_amps": round(current, 3),
            "frequency_hz": round(50.0 + random.uniform(-0.5, 0.5), 2),
            "power_factor": round(0.85 + random.random() * 0.15, 2),
            "metadata": {
                "simulated": True,
                "temperature": round(20 + random.uniform(-5, 15), 1),
                "humidity": round(40 + random.random() * 40, 1)
            }
        }


class SmartMeter(SimulatedDevice):
    """智能电表"""

    def __init__(self, device_id: str):
        super().__init__(device_id, "smart_meter", f"Smart Meter {device_id}")
        self.base_power = 2500.0  # 家庭基础用电


class SolarPanel(SimulatedDevice):
    """太阳能电池板"""

    def __init__(self, device_id: str):
        super().__init__(device_id, "solar_panel", f"Solar Panel {device_id}")
        self.base_power = 5000.0

    def generate_reading(self) -> Dict:
        # 模拟日照变化（白天发电，晚上不发电）
        hour = datetime.now().hour
        if 6 <= hour <= 18:
            # 白天，根据时间调整发电量
            peak_hour = 12
            distance = abs(hour - peak_hour)
            self.base_power = 5000.0 * max(0, 1 - distance / 6)
            self.is_on = True
        else:
            self.is_on = False
            self.base_power = 0.0

        return super().generate_reading()


class Battery(SimulatedDevice):
    """储能电池"""

    def __init__(self, device_id: str):
        super().__init__(device_id, "battery", f"Battery {device_id}")
        self.base_power = 1000.0
        self.charge_level = 50.0  # 充电水平百分比

    def generate_reading(self) -> Dict:
        # 模拟充放电
        if self.charge_level < 20:
            self.is_on = True  # 充电
            self.base_power = -1000.0  # 负值表示充电
        elif self.charge_level > 80:
            self.is_on = True  # 放电
            self.base_power = 800.0
        else:
            self.is_on = random.random() > 0.5

        self.charge_level += random.uniform(-2, 2)
        self.charge_level = max(0, min(100, self.charge_level))

        reading = super().generate_reading()
        reading["metadata"]["charge_level"] = round(self.charge_level, 1)
        return reading


class EVCharger(SimulatedDevice):
    """电动汽车充电桩"""

    def __init__(self, device_id: str):
        super().__init__(device_id, "ev_charger", f"EV Charger {device_id}")
        self.base_power = 7200.0  # 7.2kW慢充

    def generate_reading(self) -> Dict:
        # 模拟充电状态
        hour = datetime.now().hour
        if 22 <= hour or hour <= 6:
            self.is_on = random.random() > 0.3  # 晚上大概率充电
        else:
            self.is_on = random.random() > 0.9  # 白天小概率充电

        return super().generate_reading()


class HVAC(SimulatedDevice):
    """暖通空调系统"""

    def __init__(self, device_id: str):
        super().__init__(device_id, "hvac", f"HVAC {device_id}")
        self.base_power = 3500.0

    def generate_reading(self) -> Dict:
        # 根据温度调整功率
        hour = datetime.now().hour
        if 10 <= hour <= 16:
            self.is_on = True
            self.base_power = 3500.0 + random.uniform(-500, 1000)
        elif 20 <= hour or hour <= 6:
            self.is_on = random.random() > 0.5
            self.base_power = 2000.0
        else:
            self.is_on = random.random() > 0.7
            self.base_power = 2500.0

        return super().generate_reading()


class DeviceSimulator:
    """设备模拟器管理器"""

    def __init__(self):
        self.client = mqtt.Client(client_id="device-simulator", protocol=mqtt.MQTTv311)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.devices: List[SimulatedDevice] = []
        self._running = False
        self._lock = threading.Lock()

        # 初始化模拟设备
        self._init_devices()

    def _init_devices(self):
        """初始化模拟设备列表"""
        self.devices = [
            SmartMeter("smart_meter_001"),
            SolarPanel("solar_panel_001"),
            Battery("battery_001"),
            EVCharger("ev_charger_001"),
            HVAC("hvac_001"),
        ]
        logger.info(f"Initialized {len(self.devices)} simulated devices")

    def _on_connect(self, client, userdata, flags, rc):
        """MQTT连接回调"""
        if rc == 0:
            logger.info(f"Connected to MQTT Broker at {MQTT_BROKER}:{MQTT_PORT}")
        else:
            logger.error(f"Failed to connect to MQTT Broker, return code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """MQTT断开回调"""
        if rc != 0:
            logger.warning(f"Unexpected disconnection from MQTT Broker, return code: {rc}")

    def connect(self):
        """连接到MQTT Broker"""
        try:
            logger.info(f"Connecting to MQTT Broker at {MQTT_BROKER}:{MQTT_PORT}")
            self.client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            self.client.loop_start()
            logger.info("MQTT client started")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT Broker: {e}")
            raise

    def disconnect(self):
        """断开MQTT连接"""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT client disconnected")

    def publish_device_data(self, device: SimulatedDevice):
        """发布单个设备的能耗数据"""
        try:
            reading = device.generate_reading()
            topic = f"energy/devices/{device.device_id}/readings"
            payload = json.dumps(reading)

            result = self.client.publish(topic, payload, qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published data for {device.device_id}: {reading['power_watts']}W")
            else:
                logger.error(f"Failed to publish data for {device.device_id}")

        except Exception as e:
            logger.error(f"Error publishing data for {device.device_id}: {e}")

    def publish_all_devices(self):
        """发布所有设备的能耗数据"""
        with self._lock:
            for device in self.devices:
                self.publish_device_data(device)
                time.sleep(0.1)  # 避免消息过于密集
        logger.info(f"Published data for {len(self.devices)} devices")

    def start(self):
        """启动模拟器"""
        self._running = True
        self.connect()

        # 定时发布数据
        schedule.every(PUBLISH_INTERVAL).seconds.do(self.publish_all_devices)

        logger.info(f"Device simulator started, publishing every {PUBLISH_INTERVAL} seconds")
        logger.info(f"Simulated devices: {[d.device_id for d in self.devices]}")

        try:
            while self._running:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping device simulator...")
        finally:
            self.stop()

    def stop(self):
        """停止模拟器"""
        self._running = False
        schedule.clear()
        self.disconnect()
        logger.info("Device simulator stopped")


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("Smart Energy Device Simulator")
    logger.info("=" * 60)
    logger.info(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    logger.info(f"API URL: {API_URL}")
    logger.info(f"Publish Interval: {PUBLISH_INTERVAL} seconds")
    logger.info("=" * 60)

    simulator = DeviceSimulator()
    simulator.start()


if __name__ == "__main__":
    main()