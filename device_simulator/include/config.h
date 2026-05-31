#pragma once

#include <string>
#include <chrono>

namespace smart_energy {

struct Config {
    // MQTT配置
    std::string mqtt_broker = "localhost";
    int mqtt_port = 1883;
    std::string mqtt_client_id = "device-simulator-cpp";

    // 模拟配置
    int publish_interval_seconds = 10;
    bool enable_matter_bridge = true;

    // API配置
    std::string api_url = "http://localhost:8000";

    // 从环境变量加载配置
    static Config from_env() {
        Config config;

        if (const char* broker = std::getenv("MQTT_BROKER")) {
            config.mqtt_broker = broker;
        }
        if (const char* port = std::getenv("MQTT_PORT")) {
            config.mqtt_port = std::stoi(port);
        }
        if (const char* interval = std::getenv("PUBLISH_INTERVAL")) {
            config.publish_interval_seconds = std::stoi(interval);
        }
        if (const char* api = std::getenv("API_URL")) {
            config.api_url = api;
        }

        return config;
    }
};

} // namespace smart_energy