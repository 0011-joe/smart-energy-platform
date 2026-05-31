#pragma once

#include <string>
#include <functional>
#include <memory>
#include <mutex>
#include <atomic>
#include <mqtt/async_client.h>
#include <nlohmann/json.hpp>

namespace smart_energy {

/**
 * MQTT客户端封装类
 *
 * 提供与MQTT Broker的连接和消息发布功能
 * 使用Paho MQTT C++库实现
 */
class MqttClient : public virtual mqtt::callback {
public:
    using MessageHandler = std::function<void(const std::string& topic, const nlohmann::json& payload)>;

    MqttClient(const std::string& broker_address, const std::string& client_id);
    ~MqttClient();

    // 禁止拷贝
    MqttClient(const MqttClient&) = delete;
    MqttClient& operator=(const MqttClient&) = delete;

    /**
     * 连接到MQTT Broker
     * @return 是否连接成功
     */
    bool connect();

    /**
     * 断开连接
     */
    void disconnect();

    /**
     * 发布消息到指定主题
     * @param topic MQTT主题
     * @param payload JSON格式的消息内容
     * @param qos QoS级别 (0, 1, 2)
     * @return 是否发布成功
     */
    bool publish(const std::string& topic, const nlohmann::json& payload, int qos = 1);

    /**
     * 订阅主题
     * @param topic 主题模式（支持通配符）
     * @param qos QoS级别
     */
    void subscribe(const std::string& topic, int qos = 1);

    /**
     * 设置消息处理回调
     * @param handler 消息处理函数
     */
    void set_message_handler(MessageHandler handler);

    /**
     * 检查是否已连接
     */
    bool is_connected() const { return connected_.load(); }

    /**
     * 获取客户端ID
     */
    std::string get_client_id() const { return client_id_; }

protected:
    // MQTT回调函数
    void connected(const std::string& cause) override;
    void connection_lost(const std::string& cause) override;
    void message_arrived(mqtt::const_message_ptr msg) override;
    void delivery_complete(mqtt::delivery_token_ptr tok) override;

private:
    std::string broker_address_;
    std::string client_id_;
    std::unique_ptr<mqtt::async_client> client_;
    mqtt::connect_options conn_opts_;
    std::atomic<bool> connected_{false};
    std::mutex publish_mutex_;
    MessageHandler message_handler_;
};

} // namespace smart_energy