/**
 * Smart Energy Platform - Device Simulator (C++ Version)
 *
 * 智能能源设备模拟器
 * 使用Paho MQTT C++库发布模拟的能耗数据
 *
 * 特性：
 * - 5种设备类型模拟（智能电表、太阳能板、电池、充电桩、HVAC）
 * - 高性能C++实现
 * - MQTT消息发布
 * - 可配置的发布间隔
 */

#include <iostream>
#include <csignal>
#include <thread>
#include <chrono>
#include <atomic>

#include "config.h"
#include "mqtt_client.h"
#include "device_simulator.h"

using namespace smart_energy;

// 全局停止标志
std::atomic<bool> g_running{true};

// 信号处理
void signal_handler(int signal) {
    std::cout << "\n[Main] Received signal " << signal << ", shutting down..." << std::endl;
    g_running.store(false);
}

int main() {
    std::cout << "============================================================" << std::endl;
    std::cout << "Smart Energy Device Simulator (C++)" << std::endl;
    std::cout << "============================================================" << std::endl;

    // 注册信号处理
    std::signal(SIGINT, signal_handler);
    std::signal(SIGTERM, signal_handler);

    // 加载配置
    auto config = Config::from_env();

    std::cout << "Configuration:" << std::endl;
    std::cout << "  MQTT Broker: " << config.mqtt_broker << ":" << config.mqtt_port << std::endl;
    std::cout << "  Publish Interval: " << config.publish_interval_seconds << " seconds" << std::endl;
    std::cout << "  API URL: " << config.api_url << std::endl;
    std::cout << "============================================================" << std::endl;

    // 创建MQTT客户端
    std::string broker_address = "tcp://" + config.mqtt_broker + ":" + std::to_string(config.mqtt_port);
    MqttClient mqtt_client(broker_address, config.mqtt_client_id);

    // 连接到MQTT Broker
    std::cout << "\n[Main] Connecting to MQTT Broker..." << std::endl;

    int retry_count = 0;
    const int max_retries = 30;

    while (!mqtt_client.connect() && retry_count < max_retries) {
        std::cout << "[Main] Connection failed, retrying in 2 seconds... ("
                  << retry_count + 1 << "/" << max_retries << ")" << std::endl;
        std::this_thread::sleep_for(std::chrono::seconds(2));
        retry_count++;
    }

    if (!mqtt_client.is_connected()) {
        std::cerr << "[Main] Failed to connect to MQTT Broker after " << max_retries << " retries" << std::endl;
        return 1;
    }

    // 初始化设备模拟器
    DeviceSimulatorManager simulator;
    simulator.initialize_devices();

    // 设置发布回调
    simulator.set_publish_callback([&mqtt_client](const std::string& topic, const nlohmann::json& payload) {
        return mqtt_client.publish(topic, payload);
    });

    std::cout << "\n[Main] Device simulator started" << std::endl;
    std::cout << "[Main] Publishing data every " << config.publish_interval_seconds << " seconds" << std::endl;
    std::cout << "[Main] Press Ctrl+C to stop" << std::endl;
    std::cout << "============================================================" << std::endl;

    // 主循环
    int cycle_count = 0;
    int total_published = 0;

    while (g_running.load()) {
        cycle_count++;

        // 发布所有设备数据
        int published = simulator.publish_all_devices();
        total_published += published;

        std::cout << "[Cycle " << cycle_count << "] Published data for "
                  << published << " devices (Total: " << total_published << ")" << std::endl;

        // 等待下一个周期
        for (int i = 0; i < config.publish_interval_seconds * 10 && g_running.load(); ++i) {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
    }

    // 清理
    std::cout << "\n[Main] Shutting down..." << std::endl;
    mqtt_client.disconnect();

    std::cout << "============================================================" << std::endl;
    std::cout << "Device Simulator stopped" << std::endl;
    std::cout << "Total cycles: " << cycle_count << std::endl;
    std::cout << "Total messages published: " << total_published << std::endl;
    std::cout << "============================================================" << std::endl;

    return 0;
}