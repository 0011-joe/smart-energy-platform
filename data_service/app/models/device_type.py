"""
设备类型配置模型

支持动态设备类型，无需修改代码即可添加新设备类型
"""

from sqlalchemy import Column, String, Boolean, DateTime, JSON, Integer
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class DeviceTypeConfig(Base):
    """
    设备类型配置表

    存储设备类型的元数据和配置信息
    前端可根据这些配置自动渲染不同的图标和控制组件
    """
    __tablename__ = "device_type_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type_key = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(String(500))
    category = Column(String(50), default="general")  # energy, comfort, security, etc.

    # 前端显示配置
    icon = Column(String(100), default="device")  # 图标名称
    color = Column(String(20), default="#0ea5e9")  # 主题颜色
    image_url = Column(String(500))  # 设备图片URL

    # 功能配置
    capabilities = Column(JSON, default=list)  # 支持的功能列表
    # 示例: ["power_monitoring", "on_off_control", "dimming"]

    # 控制组件配置
    control_components = Column(JSON, default=list)
    # 示例: [{"type": "switch", "label": "电源开关"}, {"type": "slider", "label": "亮度", "min": 0, "max": 100}]

    # 数据字段配置
    data_fields = Column(JSON, default=list)
    # 示例: [
    #   {"key": "power_watts", "label": "功率", "unit": "W", "type": "number"},
    #   {"key": "energy_kwh", "label": "电量", "unit": "kWh", "type": "number"}
    # ]

    # Matter协议映射
    matter_device_type = Column(Integer)  # Matter设备类型代码
    matter_clusters = Column(JSON, default=list)  # Matter集群列表

    # 状态
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "type_key": self.type_key,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category,
            "icon": self.icon,
            "color": self.color,
            "image_url": self.image_url,
            "capabilities": self.capabilities,
            "control_components": self.control_components,
            "data_fields": self.data_fields,
            "matter_device_type": self.matter_device_type,
            "matter_clusters": self.matter_clusters,
            "is_active": self.is_active
        }


# 预置设备类型数据
DEFAULT_DEVICE_TYPES = [
    {
        "type_key": "smart_meter",
        "display_name": "智能电表",
        "description": "用于测量家庭或设备的电能消耗",
        "category": "energy",
        "icon": "gauge",
        "color": "#3b82f6",
        "capabilities": ["power_monitoring", "energy_tracking"],
        "control_components": [],
        "data_fields": [
            {"key": "power_watts", "label": "瞬时功率", "unit": "W", "type": "number"},
            {"key": "energy_kwh", "label": "累计电量", "unit": "kWh", "type": "number"},
            {"key": "voltage", "label": "电压", "unit": "V", "type": "number"},
            {"key": "current_amps", "label": "电流", "unit": "A", "type": "number"}
        ],
        "matter_device_type": 0x000D,
        "matter_clusters": [0x0B04, 0x0702]
    },
    {
        "type_key": "solar_panel",
        "display_name": "太阳能电池板",
        "description": "光伏发电设备，将太阳能转换为电能",
        "category": "energy",
        "icon": "sun",
        "color": "#f59e0b",
        "capabilities": ["power_monitoring", "energy_generation"],
        "control_components": [],
        "data_fields": [
            {"key": "power_watts", "label": "发电功率", "unit": "W", "type": "number"},
            {"key": "energy_kwh", "label": "发电量", "unit": "kWh", "type": "number"},
            {"key": "efficiency", "label": "转换效率", "unit": "%", "type": "number"}
        ],
        "matter_device_type": 0x0510,
        "matter_clusters": [0x0B04, 0x0702]
    },
    {
        "type_key": "battery",
        "display_name": "储能电池",
        "description": "用于存储电能的电池系统",
        "category": "energy",
        "icon": "battery-charging",
        "color": "#22c55e",
        "capabilities": ["power_monitoring", "charge_control"],
        "control_components": [
            {"type": "slider", "label": "充电上限", "min": 0, "max": 100, "unit": "%"}
        ],
        "data_fields": [
            {"key": "power_watts", "label": "充放电功率", "unit": "W", "type": "number"},
            {"key": "charge_level", "label": "电量", "unit": "%", "type": "number"},
            {"key": "capacity", "label": "容量", "unit": "kWh", "type": "number"}
        ],
        "matter_device_type": 0x0510,
        "matter_clusters": [0x0B04, 0x0702]
    },
    {
        "type_key": "ev_charger",
        "display_name": "电动汽车充电桩",
        "description": "为电动汽车提供充电服务的设备",
        "category": "energy",
        "icon": "zap",
        "color": "#8b5cf6",
        "capabilities": ["power_monitoring", "on_off_control", "charge_scheduling"],
        "control_components": [
            {"type": "switch", "label": "充电开关"},
            {"type": "select", "label": "充电模式", "options": ["慢充", "快充", "定时"]}
        ],
        "data_fields": [
            {"key": "power_watts", "label": "充电功率", "unit": "W", "type": "number"},
            {"key": "energy_kwh", "label": "充电量", "unit": "kWh", "type": "number"},
            {"key": "charging_status", "label": "充电状态", "type": "string"}
        ],
        "matter_device_type": 0x010A,
        "matter_clusters": [0x0006, 0x0B04, 0x0702]
    },
    {
        "type_key": "hvac",
        "display_name": "暖通空调",
        "description": "供暖、通风和空调系统",
        "category": "comfort",
        "icon": "thermometer",
        "color": "#06b6d4",
        "capabilities": ["power_monitoring", "temperature_control", "mode_switch"],
        "control_components": [
            {"type": "switch", "label": "开关"},
            {"type": "slider", "label": "温度设置", "min": 16, "max": 30, "unit": "°C"},
            {"type": "select", "label": "模式", "options": ["制冷", "制热", "自动", "除湿"]}
        ],
        "data_fields": [
            {"key": "power_watts", "label": "功率", "unit": "W", "type": "number"},
            {"key": "temperature", "label": "室内温度", "unit": "°C", "type": "number"},
            {"key": "humidity", "label": "湿度", "unit": "%", "type": "number"},
            {"key": "target_temp", "label": "目标温度", "unit": "°C", "type": "number"}
        ],
        "matter_device_type": 0x0301,
        "matter_clusters": [0x0402, 0x0B04]
    },
    {
        "type_key": "lighting",
        "display_name": "智能照明",
        "description": "可控制的智能灯具",
        "category": "comfort",
        "icon": "lightbulb",
        "color": "#eab308",
        "capabilities": ["on_off_control", "dimming", "color_control"],
        "control_components": [
            {"type": "switch", "label": "开关"},
            {"type": "slider", "label": "亮度", "min": 0, "max": 100, "unit": "%"},
            {"type": "color", "label": "颜色"}
        ],
        "data_fields": [
            {"key": "power_watts", "label": "功率", "unit": "W", "type": "number"},
            {"key": "brightness", "label": "亮度", "unit": "%", "type": "number"}
        ],
        "matter_device_type": 0x0100,
        "matter_clusters": [0x0006, 0x0008, 0x0300]
    },
    {
        "type_key": "appliance",
        "display_name": "智能插座",
        "description": "可远程控制的智能插座",
        "category": "general",
        "icon": "plug",
        "color": "#64748b",
        "capabilities": ["power_monitoring", "on_off_control"],
        "control_components": [
            {"type": "switch", "label": "电源开关"}
        ],
        "data_fields": [
            {"key": "power_watts", "label": "功率", "unit": "W", "type": "number"},
            {"key": "energy_kwh", "label": "用电量", "unit": "kWh", "type": "number"}
        ],
        "matter_device_type": 0x010A,
        "matter_clusters": [0x0006, 0x0B04, 0x0702]
    }
]