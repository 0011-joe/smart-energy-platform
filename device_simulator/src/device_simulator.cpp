#include "device_simulator.h"
#include <iostream>
#include <iomanip>
#include <sstream>
#include <ctime>

namespace smart_energy {

// ============================================================================
// SimulatedDevice 基类实现
// ============================================================================

SimulatedDevice::SimulatedDevice(const std::string& device_id, DeviceType type, const std::string& name)
    : device_id_(device_id)
    , type_(type)
    , name_(name)
    , is_on_(true)
    , base_power_(0.0)
    , voltage_(220.0)
    , energy_accumulated_(0.0)
    , rng_(std::random_device{}())
{
}

std::string SimulatedDevice::get_current_timestamp() {
    auto now = std::chrono::system_clock::now();
    auto time = std::chrono::system_clock::to_time_t(now);
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        now.time_since_epoch()
    ) % 1000;

    std::ostringstream oss;
    oss << std::put_time(std::gmtime(&time), "%Y-%m-%dT%H:%M:%S");
    oss << "." << std::setfill('0') << std::setw(3) << ms.count() << "Z";

    return oss.str();
}

double SimulatedDevice::random_double(double min, double max) {
    std::uniform_real_distribution<double> dist(min, max);
    return dist(rng_);
}

double SimulatedDevice::add_noise(double value, double noise_percent) {
    double noise = value * (noise_percent / 100.0);
    return value + random_double(-noise, noise);
}

// ============================================================================
// SmartMeter 智能电表
// ============================================================================

class SmartMeter : public SimulatedDevice {
public:
    SmartMeter(const std::string& device_id)
        : SimulatedDevice(device_id, DeviceType::SMART_METER, "Smart Meter " + device_id)
    {
        base_power_ = 2500.0;  // 家庭基础用电
    }

    DeviceReading generate_reading() override {
        // 模拟家庭用电波动
        double hour = get_current_hour();
        double power_factor = 1.0;

        // 白天用电较高，夜间较低
        if (hour >= 8 && hour <= 20) {
            power_factor = 1.0 + 0.3 * std::sin((hour - 8) * M_PI / 12);
        } else {
            power_factor = 0.5 + 0.2 * random_double(0, 1);
        }

        double power = add_noise(base_power_ * power_factor, 15);
        double current = power / voltage_;
        double energy_increment = power / 3600.0 * 10.0 / 1000.0; // 10秒间隔

        energy_accumulated_ += energy_increment;

        return DeviceReading{
            device_id_,
            type_,
            get_current_timestamp(),
            power,
            energy_accumulated_,
            add_noise(voltage_, 2),
            current,
            add_noise(50.0, 1),
            0.9 + random_double(0, 0.1),
            {{"temperature", add_noise(25, 10)}, {"humidity", add_noise(50, 20)}}
        };
    }

private:
    double get_current_hour() {
        auto now = std::chrono::system_clock::now();
        auto time = std::chrono::system_clock::to_time_t(now);
        auto* tm = std::localtime(&time);
        return tm->tm_hour + tm->tm_min / 60.0;
    }
};

// ============================================================================
// SolarPanel 太阳能电池板
// ============================================================================

class SolarPanel : public SimulatedDevice {
public:
    SolarPanel(const std::string& device_id)
        : SimulatedDevice(device_id, DeviceType::SOLAR_PANEL, "Solar Panel " + device_id)
    {
        base_power_ = 5000.0;
    }

    DeviceReading generate_reading() override {
        double hour = get_current_hour();
        double power = 0.0;

        // 模拟日照变化（白天发电，晚上不发电）
        if (hour >= 6 && hour <= 18) {
            double peak_hour = 12.0;
            double distance = std::abs(hour - peak_hour);
            power = base_power_ * std::max(0.0, 1.0 - distance / 6.0);
            power = add_noise(power, 20);
            is_on_ = true;
        } else {
            is_on_ = false;
            power = 0.0;
        }

        double current = power > 0 ? power / voltage_ : 0;
        double energy_increment = power / 3600.0 * 10.0 / 1000.0;

        energy_accumulated_ += energy_increment;

        return DeviceReading{
            device_id_,
            type_,
            get_current_timestamp(),
            power,
            energy_accumulated_,
            add_noise(voltage_, 2),
            current,
            add_noise(50.0, 1),
            power > 0 ? 0.95 : 0.0,
            {{"irradiance", power > 0 ? add_noise(800, 20) : 0}, {"panel_temp", add_noise(35, 15)}}
        };
    }

private:
    double get_current_hour() {
        auto now = std::chrono::system_clock::now();
        auto time = std::chrono::system_clock::to_time_t(now);
        auto* tm = std::localtime(&time);
        return tm->tm_hour + tm->tm_min / 60.0;
    }
};

// ============================================================================
// Battery 储能电池
// ============================================================================

class Battery : public SimulatedDevice {
public:
    Battery(const std::string& device_id)
        : SimulatedDevice(device_id, DeviceType::BATTERY, "Battery " + device_id)
        , charge_level_(50.0)
    {
        base_power_ = 1000.0;
    }

    DeviceReading generate_reading() override {
        // 模拟充放电逻辑
        if (charge_level_ < 20) {
            is_on_ = true;
            base_power_ = -1000.0; // 充电（负值）
        } else if (charge_level_ > 80) {
            is_on_ = true;
            base_power_ = 800.0;   // 放电
        } else {
            is_on_ = random_double(0, 1) > 0.5;
        }

        charge_level_ += random_double(-2, 2);
        charge_level_ = std::max(0.0, std::min(100.0, charge_level_));

        double power = add_noise(base_power_, 10);
        double current = std::abs(power) / voltage_;
        double energy_increment = std::abs(power) / 3600.0 * 10.0 / 1000.0;

        if (power > 0) {
            energy_accumulated_ += energy_increment;
        }

        return DeviceReading{
            device_id_,
            type_,
            get_current_timestamp(),
            power,
            energy_accumulated_,
            add_noise(voltage_, 2),
            current,
            add_noise(50.0, 1),
            0.92 + random_double(0, 0.08),
            {{"charge_level", charge_level_}, {"temperature", add_noise(30, 10)}}
        };
    }

private:
    double charge_level_;
};

// ============================================================================
// EVCharger 电动汽车充电桩
// ============================================================================

class EVCharger : public SimulatedDevice {
public:
    EVCharger(const std::string& device_id)
        : SimulatedDevice(device_id, DeviceType::EV_CHARGER, "EV Charger " + device_id)
    {
        base_power_ = 7200.0; // 7.2kW慢充
    }

    DeviceReading generate_reading() override {
        double hour = get_current_hour();

        // 晚上大概率充电，白天小概率
        if (hour >= 22 || hour <= 6) {
            is_on_ = random_double(0, 1) > 0.3;
        } else {
            is_on_ = random_double(0, 1) > 0.9;
        }

        double power = is_on_ ? add_noise(base_power_, 5) : 0.0;
        double current = power / voltage_;
        double energy_increment = power / 3600.0 * 10.0 / 1000.0;

        energy_accumulated_ += energy_increment;

        return DeviceReading{
            device_id_,
            type_,
            get_current_timestamp(),
            power,
            energy_accumulated_,
            add_noise(voltage_, 2),
            current,
            add_noise(50.0, 1),
            is_on_ ? 0.98 : 0.0,
            {{"charging_status", is_on_ ? "charging" : "idle"}, {"soc", add_noise(60, 30)}}
        };
    }

private:
    double get_current_hour() {
        auto now = std::chrono::system_clock::now();
        auto time = std::chrono::system_clock::to_time_t(now);
        auto* tm = std::localtime(&time);
        return tm->tm_hour + tm->tm_min / 60.0;
    }
};

// ============================================================================
// HVAC 暖通空调
// ============================================================================

class HVAC : public SimulatedDevice {
public:
    HVAC(const std::string& device_id)
        : SimulatedDevice(device_id, DeviceType::HVAC, "HVAC " + device_id)
    {
        base_power_ = 3500.0;
    }

    DeviceReading generate_reading() override {
        double hour = get_current_hour();

        // 根据时间段调整功率
        if (hour >= 10 && hour <= 16) {
            is_on_ = true;
            base_power_ = 3500.0 + random_double(-500, 1000);
        } else if (hour >= 20 || hour <= 6) {
            is_on_ = random_double(0, 1) > 0.5;
            base_power_ = 2000.0;
        } else {
            is_on_ = random_double(0, 1) > 0.7;
            base_power_ = 2500.0;
        }

        double power = is_on_ ? add_noise(base_power_, 10) : 0.0;
        double current = power / voltage_;
        double energy_increment = power / 3600.0 * 10.0 / 1000.0;

        energy_accumulated_ += energy_increment;

        return DeviceReading{
            device_id_,
            type_,
            get_current_timestamp(),
            power,
            energy_accumulated_,
            add_noise(voltage_, 2),
            current,
            add_noise(50.0, 1),
            is_on_ ? 0.85 + random_double(0, 0.15) : 0.0,
            {{"indoor_temp", add_noise(24, 3)}, {"target_temp", 24.0}, {"mode", "cooling"}}
        };
    }

private:
    double get_current_hour() {
        auto now = std::chrono::system_clock::now();
        auto time = std::chrono::system_clock::to_time_t(now);
        auto* tm = std::localtime(&time);
        return tm->tm_hour + tm->tm_min / 60.0;
    }
};

// ============================================================================
// DeviceSimulatorManager 实现
// ============================================================================

DeviceSimulatorManager::DeviceSimulatorManager() = default;
DeviceSimulatorManager::~DeviceSimulatorManager() = default;

void DeviceSimulatorManager::initialize_devices() {
    std::cout << "[Simulator] Initializing devices..." << std::endl;

    devices_.push_back(std::make_unique<SmartMeter>("smart_meter_001"));
    devices_.push_back(std::make_unique<SolarPanel>("solar_panel_001"));
    devices_.push_back(std::make_unique<Battery>("battery_001"));
    devices_.push_back(std::make_unique<EVCharger>("ev_charger_001"));
    devices_.push_back(std::make_unique<HVAC>("hvac_001"));

    std::cout << "[Simulator] Initialized " << devices_.size() << " devices:" << std::endl;
    for (const auto& device : devices_) {
        std::cout << "  - " << device->get_name() << " (" << device->get_device_id() << ")" << std::endl;
    }
}

int DeviceSimulatorManager::publish_all_devices() {
    int published = 0;

    for (auto& device : devices_) {
        try {
            auto reading = device->generate_reading();
            auto topic = device->get_topic();
            auto payload = reading.to_json();

            if (publish_callback_ && publish_callback_(topic, payload)) {
                published++;
            }
        } catch (const std::exception& e) {
            std::cerr << "[Simulator] Error publishing " << device->get_device_id()
                      << ": " << e.what() << std::endl;
        }
    }

    return published;
}

} // namespace smart_energy