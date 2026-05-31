#include "mqtt_client.h"
#include <iostream>
#include <stdexcept>

namespace smart_energy {

MqttClient::MqttClient(const std::string& broker_address, const std::string& client_id)
    : broker_address_(broker_address)
    , client_id_(client_id)
{
    // 创建MQTT客户端
    client_ = std::make_unique<mqtt::async_client>(broker_address, client_id);

    // 设置回调
    client_->set_callback(*this);

    // 配置连接选项
    conn_opts_.set_keep_alive_interval(60);
    conn_opts_.set_clean_session(true);
    conn_opts_.set_automatic_reconnect(true);
    conn_opts_.set_max_inflight(100);

    std::cout << "[MQTT] Client initialized: " << client_id << " -> " << broker_address << std::endl;
}

MqttClient::~MqttClient() {
    disconnect();
}

bool MqttClient::connect() {
    try {
        std::cout << "[MQTT] Connecting to broker: " << broker_address_ << "..." << std::endl;

        auto token = client_->connect(conn_opts_);
        token->wait();

        if (client_->is_connected()) {
            connected_.store(true);
            std::cout << "[MQTT] Connected successfully!" << std::endl;
            return true;
        }

        std::cerr << "[MQTT] Connection failed!" << std::endl;
        return false;
    } catch (const mqtt::exception& e) {
        std::cerr << "[MQTT] Connection error: " << e.what() << std::endl;
        return false;
    }
}

void MqttClient::disconnect() {
    if (client_ && client_->is_connected()) {
        try {
            auto token = client_->disconnect();
            token->wait();
            connected_.store(false);
            std::cout << "[MQTT] Disconnected" << std::endl;
        } catch (const mqtt::exception& e) {
            std::cerr << "[MQTT] Disconnect error: " << e.what() << std::endl;
        }
    }
}

bool MqttClient::publish(const std::string& topic, const nlohmann::json& payload, int qos) {
    if (!connected_.load()) {
        std::cerr << "[MQTT] Not connected, cannot publish" << std::endl;
        return false;
    }

    try {
        std::lock_guard<std::mutex> lock(publish_mutex_);

        std::string payload_str = payload.dump();
        auto msg = mqtt::make_message(topic, payload_str);
        msg->set_qos(qos);

        auto token = client_->publish(msg);
        token->wait_for(std::chrono::seconds(5));

        return true;
    } catch (const mqtt::exception& e) {
        std::cerr << "[MQTT] Publish error: " << e.what() << std::endl;
        return false;
    }
}

void MqttClient::subscribe(const std::string& topic, int qos) {
    if (!connected_.load()) {
        std::cerr << "[MQTT] Not connected, cannot subscribe" << std::endl;
        return;
    }

    try {
        auto token = client_->subscribe(topic, qos);
        token->wait();
        std::cout << "[MQTT] Subscribed to: " << topic << std::endl;
    } catch (const mqtt::exception& e) {
        std::cerr << "[MQTT] Subscribe error: " << e.what() << std::endl;
    }
}

void MqttClient::set_message_handler(MessageHandler handler) {
    message_handler_ = std::move(handler);
}

void MqttClient::connected(const std::string& cause) {
    std::cout << "[MQTT] Connection established. Cause: " << cause << std::endl;
    connected_.store(true);
}

void MqttClient::connection_lost(const std::string& cause) {
    std::cerr << "[MQTT] Connection lost. Cause: " << cause << std::endl;
    connected_.store(false);
}

void MqttClient::message_arrived(mqtt::const_message_ptr msg) {
    try {
        std::string topic = msg->get_topic();
        std::string payload_str = msg->to_string();

        if (message_handler_) {
            auto payload = nlohmann::json::parse(payload_str);
            message_handler_(topic, payload);
        }
    } catch (const std::exception& e) {
        std::cerr << "[MQTT] Message processing error: " << e.what() << std::endl;
    }
}

void MqttClient::delivery_complete(mqtt::delivery_token_ptr tok) {
    // 可选：记录投递完成
}

} // namespace smart_energy