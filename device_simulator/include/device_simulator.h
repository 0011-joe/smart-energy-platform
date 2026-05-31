#pragma once

#include <string>
#include <random>
#include <chrono>
#include <nlohmann/json.hpp>

namespace smart_energy {

/**
 * 设备类型枚举
 */
enum class DeviceType {
    SMART_METER,
    SOLAR_PANEL,
    BATTERY,
    EV_CHARGER,
    HVAC
};

/**
 * 设备读数结构体
 */
struct DeviceReading {
    std::string device_id;
    DeviceType device_type;
    std::string timestamp;
    double power_watts;
    double energy_kwh;
    double voltage;
    double current_amps;
    double frequency_hz;
    double power_factor;
    nlohmann::json metadata;

    /**
     * 转换为JSON格式
     */
    nlohmann::json to_json() const {
        return {
            {"device_id", device_id},
            {"device_type", device_type_to_string(device_type)},
            {"timestamp", timestamp},
            {"power_watts", power_watts},
            {"energy_kwh", energy_kwh},
            {"voltage", voltage},
            {"current_amps", current_amps},
            {"frequency_hz", frequency_hz},
            {"power_factor", power_factor},
            {"metadata", metadata}
        };
    }

    static std::string device_type_to_string(DeviceType type) {
        switch (type) {
            case DeviceType::SMART_METER: return "smart_meter";
            case DeviceType::SOLAR_PANEL: return "solar_panel";
            case DeviceType::BATTERY: return "battery";
            case DeviceType::EV_CHARGER: return "ev_charger";
            case DeviceType::HVAC: return "hvac";
            default: return "unknown";
        }
    }
};

/**
 * 模拟设备基类
 *
 * 提供设备模拟的基础功能，所有具体设备类型都继承此类
 */
class SimulatedDevice {
public:
    SimulatedDevice(const std::string& device_id, DeviceType type, const std::string& name);
    virtual ~SimulatedDevice() = default;

    /**
     * 生成设备读数（纯虚函数，由子类实现）
     * @return 设备读数
     */
    virtual DeviceReading generate_reading() = 0;

    /**
     * 获取设备ID
     */
    std::string get_device_id() const { return device_id_; }

    /**
     * 获取设备名称
     */
    std::string get_name() const { return name_; }

    /**
     * 获取设备类型
     */
    DeviceType get_type() const { return type_; }

    /**
     * 获取MQTT主题
     */
    std::string get_topic() const {
        return "energy/devices/" + device_id_ + "/readings";
    }

protected:
    /**
     * 获取当前时间戳（ISO 8601格式）
     */
    static std::string get_current_timestamp();

    /**
     * 生成随机数
     */
    double random_double(double min, double max);

    /**
     * 添加随机波动
     */
    double add_noise(double value, double noise_percent = 10.0);

    std::string device_id_;
    DeviceType type_;
    std::string name_;
    bool is_on_;
    double base_power_;
    double voltage_;
    double energy_accumulated_;

private:
    std::mt19937 rng_;
};

/**
 * 设备模拟器管理类
 *
 * 管理所有模拟设备，定时发布数据
 */
class DeviceSimulatorManager {
public:
    DeviceSimulatorManager();
    ~DeviceSimulatorManager();

    /**
     * 初始化模拟设备
     */
    void initialize_devices();

    /**
     * 发布所有设备数据
     * @return 发布的设备数量
     */
    int publish_all_devices();

    /**
     * 获取设备列表
     */
    const std::vector<std::unique_ptr<SimulatedDevice>>& get_devices() const {
        return devices_;
    }

    /**
     * 设置MQTT客户端（用于发布数据）
     */
    void set_publish_callback(std::function<bool(const std::string&, const nlohmann::json&)> callback) {
        publish_callback_ = std::move(callback);
    }

private:
    std::vector<std::unique_ptr<SimulatedDevice>> devices_;
    std::function<bool(const std::string&, const nlohmann::json&)> publish_callback_;
};

} // namespace smart_energy