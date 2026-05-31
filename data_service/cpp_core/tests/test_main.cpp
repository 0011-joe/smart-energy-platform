/**
 * C++ Core Unit Tests
 *
 * 测试数据处理器和预测模型的功能
 */

#include <iostream>
#include <cassert>
#include <cmath>
#include <vector>
#include <chrono>

#include "data_processor.h"
#include "predictor.h"
#include "statistics.h"

using namespace smart_energy;
using namespace std::chrono;

// 测试计数器
int tests_passed = 0;
int tests_failed = 0;

#define TEST(name) \
    void test_##name(); \
    struct TestRunner_##name { \
        TestRunner_##name() { \
            std::cout << "Running " << #name << "... "; \
            try { \
                test_##name(); \
                std::cout << "PASSED" << std::endl; \
                tests_passed++; \
            } catch (const std::exception& e) { \
                std::cout << "FAILED: " << e.what() << std::endl; \
                tests_failed++; \
            } \
        } \
    } runner_##name; \
    void test_##name()

// ============================================================================
// Statistics Tests
// ============================================================================

TEST(statistics_mean) {
    std::vector<double> values = {1, 2, 3, 4, 5};
    double result = Statistics::mean(values);
    assert(std::abs(result - 3.0) < 0.001);
}

TEST(statistics_standard_deviation) {
    std::vector<double> values = {2, 4, 4, 4, 5, 5, 7, 9};
    double result = Statistics::standard_deviation(values);
    assert(std::abs(result - 2.0) < 0.1);
}

TEST(statistics_median_odd) {
    std::vector<double> values = {1, 3, 5, 7, 9};
    double result = Statistics::median(values);
    assert(std::abs(result - 5.0) < 0.001);
}

TEST(statistics_median_even) {
    std::vector<double> values = {1, 2, 3, 4};
    double result = Statistics::median(values);
    assert(std::abs(result - 2.5) < 0.001);
}

TEST(statistics_z_score) {
    double result = Statistics::z_score(10, 5, 2);
    assert(std::abs(result - 2.5) < 0.001);
}

TEST(statistics_pearson_correlation) {
    std::vector<double> x = {1, 2, 3, 4, 5};
    std::vector<double> y = {2, 4, 6, 8, 10};
    double result = Statistics::pearson_correlation(x, y);
    assert(std::abs(result - 1.0) < 0.001); // 完美正相关
}

TEST(statistics_r2_score) {
    std::vector<double> actual = {1, 2, 3, 4, 5};
    std::vector<double> predicted = {1.1, 2.1, 2.9, 4.2, 4.8};
    double result = Statistics::r2_score(actual, predicted);
    assert(result > 0.95); // 应该接近1
}

// ============================================================================
// DataProcessor Tests
// ============================================================================

TEST(data_processor_aggregate_by_hour) {
    DataProcessor processor;
    std::vector<Reading> readings;

    // 创建测试数据
    auto now = system_clock::now();

    for (int i = 0; i < 100; ++i) {
        Reading r;
        r.device_id = "test_device";
        r.timestamp = now + minutes(i * 10);
        r.power_watts = 1000.0 + (i % 10) * 100;
        r.energy_kwh = 0.1;
        readings.push_back(r);
    }

    auto results = processor.aggregate_by_hour(readings);
    assert(!results.empty());
}

TEST(data_processor_calculate_cost) {
    DataProcessor processor;
    std::vector<Reading> readings;

    Reading r;
    r.energy_kwh = 10.0;
    readings.push_back(r);

    r.energy_kwh = 20.0;
    readings.push_back(r);

    double cost = processor.calculate_cost(readings, 0.5);
    assert(std::abs(cost - 15.0) < 0.001); // (10+20) * 0.5
}

TEST(data_processor_detect_anomalies) {
    DataProcessor processor;
    std::vector<Reading> readings;

    auto now = system_clock::now();

    // 创建正常数据
    for (int i = 0; i < 50; ++i) {
        Reading r;
        r.device_id = "test";
        r.timestamp = now + minutes(i);
        r.power_watts = 1000.0 + (rand() % 100);
        readings.push_back(r);
    }

    // 添加异常值
    Reading anomaly;
    anomaly.device_id = "test";
    anomaly.timestamp = now + minutes(50);
    anomaly.power_watts = 50000.0; // 明显异常
    readings.push_back(anomaly);

    auto results = processor.detect_anomalies(readings, 3.0);
    assert(results.size() == readings.size());

    // 最后一个应该是异常
    assert(results.back().is_anomaly);
}

TEST(data_processor_calculate_load_profile) {
    DataProcessor processor;
    std::vector<Reading> readings;

    auto now = system_clock::now();

    for (int i = 0; i < 200; ++i) {
        Reading r;
        r.device_id = "test";
        r.timestamp = now + minutes(i * 10);
        r.power_watts = 1000.0 + sin(i * 0.1) * 500;
        readings.push_back(r);
    }

    auto profile = processor.calculate_load_profile(readings);
    assert(profile.size() == 24); // 应该有24个小时
}

// ============================================================================
// EnergyPredictor Tests
// ============================================================================

TEST(predictor_train_and_predict) {
    EnergyPredictor predictor;
    std::vector<Reading> readings;

    auto now = system_clock::now();

    // 创建训练数据
    for (int i = 0; i < 100; ++i) {
        Reading r;
        r.device_id = "test";
        r.timestamp = now + hours(i);
        r.power_watts = 1000.0 + sin(i * 0.5) * 500 + (rand() % 100);
        readings.push_back(r);
    }

    // 训练模型
    auto result = predictor.train(readings);
    assert(result.success);
    assert(result.r2_score > 0.5);

    // 预测
    double prediction = predictor.predict(12, 3, false, 1200.0);
    assert(prediction > 0);
}

TEST(predictor_predict_next_hours) {
    EnergyPredictor predictor;
    std::vector<Reading> readings;

    auto now = system_clock::now();

    for (int i = 0; i < 100; ++i) {
        Reading r;
        r.device_id = "test";
        r.timestamp = now + hours(i);
        r.power_watts = 1000.0 + i * 10;
        readings.push_back(r);
    }

    predictor.train(readings);
    auto predictions = predictor.predict_next_hours(readings, 24);

    assert(predictions.size() == 24);
    for (const auto& pred : predictions) {
        assert(pred.predicted_power >= 0);
        assert(pred.confidence_lower <= pred.predicted_power);
        assert(pred.confidence_upper >= pred.predicted_power);
    }
}

TEST(predictor_without_training) {
    EnergyPredictor predictor;

    bool exception_thrown = false;
    try {
        predictor.predict(12, 3, false, 1000.0);
    } catch (const std::runtime_error& e) {
        exception_thrown = true;
    }

    assert(exception_thrown);
}

// ============================================================================
// Main
// ============================================================================

int main() {
    std::cout << "============================================================" << std::endl;
    std::cout << "Smart Energy Core - Unit Tests" << std::endl;
    std::cout << "============================================================" << std::endl;
    std::cout << std::endl;

    // Tests are auto-registered via TestRunner

    std::cout << std::endl;
    std::cout << "============================================================" << std::endl;
    std::cout << "Results: " << tests_passed << " passed, "
              << tests_failed << " failed" << std::endl;
    std::cout << "============================================================" << std::endl;

    return tests_failed > 0 ? 1 : 0;
}