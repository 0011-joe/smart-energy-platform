#!/usr/bin/env python3
"""
Smart Energy Device Simulator

C++版本的Python包装器
如果C++二进制可用则调用，否则使用Python实现
"""

import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# C++二进制路径
CPP_BINARY = os.path.join(os.path.dirname(__file__), "build", "smart_energy_device_simulator")


def run_cpp_simulator():
    """运行C++版本的设备模拟器"""
    if os.path.exists(CPP_BINARY):
        logger.info("Starting C++ device simulator...")
        try:
            subprocess.run([CPP_BINARY], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"C++ simulator failed: {e}")
            return False
        except KeyboardInterrupt:
            logger.info("Simulator stopped by user")
            return True
    return False


def run_python_simulator():
    """运行Python版本的设备模拟器（回退方案）"""
    logger.info("Starting Python device simulator...")

    import paho.mqtt.client as mqtt
    import json
    import time
    import random
    from datetime import datetime, timezone

    MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
    MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
    PUBLISH_INTERVAL = int(os.getenv("PUBLISH_INTERVAL", "10"))

    client = mqtt.Client(client_id="device-simulator-py", protocol=mqtt.MQTTv311)

    def on_connect(c, userdata, flags, rc):
        if rc == 0:
            logger.info(f"Connected to MQTT Broker at {MQTT_BROKER}:{MQTT_PORT}")
        else:
            logger.error(f"Connection failed: {rc}")

    client.on_connect = on_connect

    # 设备配置
    devices = [
        {"id": "smart_meter_001", "type": "smart_meter", "base_power": 2500},
        {"id": "solar_panel_001", "type": "solar_panel", "base_power": 5000},
        {"id": "battery_001", "type": "battery", "base_power": 1000},
        {"id": "ev_charger_001", "type": "ev_charger", "base_power": 7200},
        {"id": "hvac_001", "type": "hvac", "base_power": 3500},
    ]

    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()

    logger.info(f"Publishing data every {PUBLISH_INTERVAL} seconds")

    try:
        while True:
            for device in devices:
                # 生成模拟数据
                hour = datetime.now().hour
                power_factor = 1.0

                if device["type"] == "solar_panel":
                    power_factor = max(0, 1 - abs(hour - 12) / 6) if 6 <= hour <= 18 else 0
                elif device["type"] == "ev_charger":
                    power_factor = 0.8 if hour >= 22 or hour <= 6 else 0.1

                power = device["base_power"] * power_factor * (0.8 + random.random() * 0.4)

                payload = {
                    "device_id": device["id"],
                    "device_type": device["type"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "power_watts": round(power, 2),
                    "energy_kwh": round(power / 3600 * PUBLISH_INTERVAL / 1000, 6),
                    "voltage": round(220 + random.uniform(-5, 5), 1),
                    "current_amps": round(power / 220, 3),
                    "frequency_hz": round(50 + random.uniform(-0.5, 0.5), 2),
                    "power_factor": round(0.85 + random.random() * 0.15, 2)
                }

                topic = f"energy/devices/{device['id']}/readings"
                client.publish(topic, json.dumps(payload))

            logger.info(f"Published data for {len(devices)} devices")
            time.sleep(PUBLISH_INTERVAL)

    except KeyboardInterrupt:
        logger.info("Stopping simulator...")
    finally:
        client.loop_stop()
        client.disconnect()


def main():
    """主函数"""
    # 优先尝试C++版本
    if not run_cpp_simulator():
        # 回退到Python版本
        run_python_simulator()


if __name__ == "__main__":
    main()