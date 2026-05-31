#include "predictor.h"
#include "statistics.h"
#include <iostream>
#include <cmath>
#include <random>
#include <algorithm>

namespace smart_energy {

EnergyPredictor::EnergyPredictor()
    : trained_(false)
    , intercept_(0.0)
{
    coefficients_ = Eigen::VectorXd::Zero(4);
    metrics_ = {0.0, 0.0, 0.0, 0.0};
}

void EnergyPredictor::reset() {
    trained_ = false;
    intercept_ = 0.0;
    coefficients_ = Eigen::VectorXd::Zero(4);
    metrics_ = {0.0, 0.0, 0.0, 0.0};
}

EnergyPredictor::Features EnergyPredictor::extract_features(
    const Reading& reading,
    double prev_power
) {
    auto time = std::chrono::system_clock::to_time_t(reading.timestamp);
    auto* tm = std::gmtime(&time);

    return Features{
        tm->tm_hour,
        tm->tm_wday,
        (tm->tm_wday >= 5) ? 1 : 0,
        prev_power
    };
}

void EnergyPredictor::prepare_features(
    const std::vector<Reading>& readings,
    Eigen::MatrixXd& X,
    Eigen::VectorXd& y
) {
    if (readings.size() < 2) {
        throw std::runtime_error("Insufficient data for training");
    }

    size_t n = readings.size() - 1; // 第一个样本没有prev_power

    X.resize(n, 4);
    y.resize(n);

    for (size_t i = 1; i < readings.size(); ++i) {
        Features feat = extract_features(readings[i], readings[i-1].power_watts);

        X(i-1, 0) = feat.hour;
        X(i-1, 1) = feat.day_of_week;
        X(i-1, 2) = feat.is_weekend;
        X(i-1, 3) = feat.prev_power;

        y(i-1) = readings[i].power_watts;
    }
}

TrainingResult EnergyPredictor::train(const std::vector<Reading>& readings) {
    TrainingResult result;

    if (readings.size() < 20) {
        result.success = false;
        result.error_message = "Need at least 20 data points for training";
        return result;
    }

    try {
        // 准备特征矩阵
        Eigen::MatrixXd X;
        Eigen::VectorXd y;
        prepare_features(readings, X, y);

        // 标准化特征（提高数值稳定性）
        Eigen::VectorXd mean = X.colwise().mean();
        Eigen::VectorXd stddev = Eigen::VectorXd::Zero(4);

        for (int col = 0; col < 4; ++col) {
            double var = 0;
            for (int row = 0; row < X.rows(); ++row) {
                double diff = X(row, col) - mean(col);
                var += diff * diff;
            }
            stddev(col) = std::sqrt(var / (X.rows() - 1));
            if (stddev(col) == 0) stddev(col) = 1;
        }

        // 标准化
        Eigen::MatrixXd X_norm = X;
        for (int col = 0; col < 4; ++col) {
            X_norm.col(col) = (X.col(col).array() - mean(col)) / stddev(col);
        }

        // 添加截距项
        Eigen::MatrixXd X_design(X_norm.rows(), X_norm.cols() + 1);
        X_design << Eigen::VectorXd::Ones(X_norm.rows()), X_norm;

        // 使用正规方程求解: β = (X^T X)^(-1) X^T y
        Eigen::VectorXd beta = (X_design.transpose() * X_design)
            .ldlt()
            .solve(X_design.transpose() * y);

        // 提取系数
        intercept_ = beta(0);
        coefficients_ = beta.tail(4);

        // 计算预测值
        Eigen::VectorXd y_pred = X_design * beta;

        // 计算评估指标
        std::vector<double> y_actual(y.data(), y.data() + y.size());
        std::vector<double> predicted(y_pred.data(), y_pred.data() + y_pred.size());

        metrics_.r2_score = Statistics::r2_score(y_actual, predicted);
        metrics_.mse = Statistics::mse(y_actual, predicted);
        metrics_.rmse = std::sqrt(metrics_.mse);

        // 计算MAE
        double mae = 0;
        for (size_t i = 0; i < y_actual.size(); ++i) {
            mae += std::abs(y_actual[i] - predicted[i]);
        }
        metrics_.mae = mae / y_actual.size();

        // 训练/测试分割评估
        size_t test_size = y.size() / 5; // 20% 测试集
        size_t train_size = y.size() - test_size;

        result.success = true;
        result.r2_score = metrics_.r2_score;
        result.mse = metrics_.mse;
        result.training_samples = train_size;
        result.test_samples = test_size;

        // 特征重要性（系数绝对值）
        result.feature_importance["hour"] = std::abs(coefficients_(0));
        result.feature_importance["day_of_week"] = std::abs(coefficients_(1));
        result.feature_importance["is_weekend"] = std::abs(coefficients_(2));
        result.feature_importance["prev_power"] = std::abs(coefficients_(3));

        trained_ = true;

        std::cout << "[Predictor] Model trained successfully" << std::endl;
        std::cout << "  R² Score: " << metrics_.r2_score << std::endl;
        std::cout << "  MSE: " << metrics_.mse << std::endl;
        std::cout << "  RMSE: " << metrics_.rmse << std::endl;
        std::cout << "  MAE: " << metrics_.mae << std::endl;

    } catch (const std::exception& e) {
        result.success = false;
        result.error_message = e.what();
        std::cerr << "[Predictor] Training failed: " << e.what() << std::endl;
    }

    return result;
}

double EnergyPredictor::predict(
    int hour,
    int day_of_week,
    bool is_weekend,
    double prev_power
) {
    if (!trained_) {
        throw std::runtime_error("Model not trained");
    }

    // 构建特征向量
    Eigen::VectorXd features(4);
    features << hour, day_of_week, is_weekend ? 1 : 0, prev_power;

    // 预测
    double prediction = intercept_ + coefficients_.dot(features);

    // 确保非负
    return std::max(0.0, prediction);
}

std::vector<PredictionResult> EnergyPredictor::predict_next_hours(
    const std::vector<Reading>& readings,
    int hours
) {
    if (!trained_) {
        throw std::runtime_error("Model not trained");
    }

    if (readings.empty()) {
        return {};
    }

    std::vector<PredictionResult> results;

    // 获取最后一条记录
    const auto& last_reading = readings.back();
    auto last_time = std::chrono::system_clock::to_time_t(last_reading.timestamp);
    double last_power = last_reading.power_watts;

    for (int i = 1; i <= hours; ++i) {
        // 计算未来时间
        auto future_time = std::chrono::system_clock::from_time_t(last_time + i * 3600);
        auto* tm = std::gmtime(&last_time + i * 3600);

        int hour = tm->tm_hour;
        int day_of_week = tm->tm_wday;
        bool is_weekend = day_of_week >= 5;

        // 预测
        double predicted = predict(hour, day_of_week, is_weekend, last_power);

        // 简单的置信区间（±10%）
        double margin = predicted * 0.1;

        results.push_back(PredictionResult{
            future_time,
            predicted,
            predicted - margin,
            predicted + margin
        });

        // 使用预测值作为下一个预测的输入
        last_power = predicted;
    }

    return results;
}

std::map<std::string, double> EnergyPredictor::get_feature_importance() const {
    if (!trained_) {
        return {};
    }

    std::map<std::string, double> importance;
    for (size_t i = 0; i < feature_names_.size(); ++i) {
        importance[feature_names_[i]] = std::abs(coefficients_(i));
    }

    return importance;
}

} // namespace smart_energy