#pragma once

#include <string>
#include <vector>
#include <chrono>
#include <optional>
#include <map>

namespace smart_energy {

/**
 * 时间戳类型
 */
using Timestamp = std::chrono::system_clock::time_point;

/**
 * 设备读数结构
 */
struct Reading {
    std::string id;
    std::string device_id;
    Timestamp timestamp;
    double power_watts;
    double energy_kwh;
    double voltage;
    double current_amps;
    double frequency_hz;
    double power_factor;
    std::map<std::string, double> metadata;

    /**
     * 转换为map（用于Python绑定）
     */
    std::map<std::string, std::string> to_map() const {
        return {
            {"device_id", device_id},
            {"power_watts", std::to_string(power_watts)},
            {"energy_kwh", std::to_string(energy_kwh)},
            {"voltage", std::to_string(voltage)},
            {"current_amps", std::to_string(current_amps)}
        };
    }
};

/**
 * 聚合统计结果
 */
struct AggregatedStats {
    Timestamp time_bucket;
    double avg_power;
    double max_power;
    double min_power;
    double std_power;
    double total_energy;
    int count;
};

/**
 * 预测结果
 */
struct PredictionResult {
    Timestamp timestamp;
    double predicted_power;
    double confidence_lower;
    double confidence_upper;
};

/**
 * 模型训练结果
 */
struct TrainingResult {
    bool success;
    double r2_score;
    double mse;
    int training_samples;
    int test_samples;
    std::map<std::string, double> feature_importance;
    std::string error_message;
};

/**
 * 负荷统计
 */
struct LoadProfile {
    int hour;
    double avg_power;
    double std_power;
    double peak_power;
    int sample_count;
};

/**
 * 异常检测结果
 */
struct AnomalyDetection {
    Timestamp timestamp;
    double value;
    double z_score;
    bool is_anomaly;
};

} // namespace smart_energy