#pragma once

#include <vector>
#include <cmath>
#include <algorithm>
#include <numeric>
#include <map>

namespace smart_energy {

/**
 * 统计计算工具类
 *
 * 提供各种统计计算功能
 */
class Statistics {
public:
    /**
     * 计算均值
     */
    static double mean(const std::vector<double>& values) {
        if (values.empty()) return 0.0;
        return std::accumulate(values.begin(), values.end(), 0.0) / values.size();
    }

    /**
     * 计算标准差
     */
    static double standard_deviation(const std::vector<double>& values) {
        if (values.size() < 2) return 0.0;

        double avg = mean(values);
        double sum_sq_diff = 0.0;

        for (double val : values) {
            double diff = val - avg;
            sum_sq_diff += diff * diff;
        }

        return std::sqrt(sum_sq_diff / (values.size() - 1));
    }

    /**
     * 计算方差
     */
    static double variance(const std::vector<double>& values) {
        double std = standard_deviation(values);
        return std * std;
    }

    /**
     * 计算中位数
     */
    static double median(std::vector<double> values) {
        if (values.empty()) return 0.0;

        std::sort(values.begin(), values.end());
        size_t n = values.size();

        if (n % 2 == 0) {
            return (values[n/2 - 1] + values[n/2]) / 2.0;
        } else {
            return values[n/2];
        }
    }

    /**
     * 计算百分位数
     */
    static double percentile(std::vector<double> values, double p) {
        if (values.empty()) return 0.0;

        std::sort(values.begin(), values.end());
        double index = (p / 100.0) * (values.size() - 1);
        int lower = static_cast<int>(std::floor(index));
        int upper = static_cast<int>(std::ceil(index));
        double fraction = index - lower;

        if (lower == upper) {
            return values[lower];
        }

        return values[lower] * (1.0 - fraction) + values[upper] * fraction;
    }

    /**
     * 计算Z-score
     */
    static double z_score(double value, double mean, double std_dev) {
        if (std_dev == 0) return 0.0;
        return (value - mean) / std_dev;
    }

    /**
     * 计算皮尔逊相关系数
     */
    static double pearson_correlation(
        const std::vector<double>& x,
        const std::vector<double>& y
    ) {
        if (x.size() != y.size() || x.size() < 2) return 0.0;

        size_t n = x.size();
        double sum_x = 0, sum_y = 0, sum_xy = 0;
        double sum_x2 = 0, sum_y2 = 0;

        for (size_t i = 0; i < n; ++i) {
            sum_x += x[i];
            sum_y += y[i];
            sum_xy += x[i] * y[i];
            sum_x2 += x[i] * x[i];
            sum_y2 += y[i] * y[i];
        }

        double numerator = n * sum_xy - sum_x * sum_y;
        double denominator = std::sqrt(
            (n * sum_x2 - sum_x * sum_x) *
            (n * sum_y2 - sum_y * sum_y)
        );

        if (denominator == 0) return 0.0;
        return numerator / denominator;
    }

    /**
     * 计算均方误差
     */
    static double mse(const std::vector<double>& actual, const std::vector<double>& predicted) {
        if (actual.size() != predicted.size() || actual.empty()) return 0.0;

        double sum_sq_error = 0.0;
        for (size_t i = 0; i < actual.size(); ++i) {
            double error = actual[i] - predicted[i];
            sum_sq_error += error * error;
        }

        return sum_sq_error / actual.size();
    }

    /**
     * 计算R²分数
     */
    static double r2_score(const std::vector<double>& actual, const std::vector<double>& predicted) {
        if (actual.size() != predicted.size() || actual.empty()) return 0.0;

        double ss_res = 0.0;
        double ss_tot = 0.0;
        double mean_actual = mean(actual);

        for (size_t i = 0; i < actual.size(); ++i) {
            ss_res += (actual[i] - predicted[i]) * (actual[i] - predicted[i]);
            ss_tot += (actual[i] - mean_actual) * (actual[i] - mean_actual);
        }

        if (ss_tot == 0) return 0.0;
        return 1.0 - (ss_res / ss_tot);
    }

    /**
     * 线性回归（最小二乘法）
     */
    struct LinearRegressionResult {
        double slope;
        double intercept;
        double r_squared;
    };

    static LinearRegressionResult linear_regression(
        const std::vector<double>& x,
        const std::vector<double>& y
    ) {
        if (x.size() != y.size() || x.size() < 2) {
            return {0.0, 0.0, 0.0};
        }

        double n = static_cast<double>(x.size());
        double sum_x = std::accumulate(x.begin(), x.end(), 0.0);
        double sum_y = std::accumulate(y.begin(), y.end(), 0.0);

        double sum_xy = 0.0, sum_x2 = 0.0;
        for (size_t i = 0; i < x.size(); ++i) {
            sum_xy += x[i] * y[i];
            sum_x2 += x[i] * x[i];
        }

        double slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x);
        double intercept = (sum_y - slope * sum_x) / n;

        // 计算R²
        std::vector<double> predicted;
        for (double xi : x) {
            predicted.push_back(slope * xi + intercept);
        }
        double r2 = r2_score(y, predicted);

        return {slope, intercept, r2};
    }

    /**
     * 多元线性回归
     */
    static std::vector<double> multiple_linear_regression(
        const std::vector<std::vector<double>>& X,
        const std::vector<double>& y
    ) {
        // 使用正规方程: β = (X^T X)^(-1) X^T y
        // 这里简化实现，实际应使用Eigen库

        size_t n = X.size();
        if (n == 0 || X[0].empty()) return {};

        size_t p = X[0].size();

        // 构建设计矩阵 (添加截距项)
        std::vector<std::vector<double>> X_design(n, std::vector<double>(p + 1, 1.0));
        for (size_t i = 0; i < n; ++i) {
            for (size_t j = 0; j < p; ++j) {
                X_design[i][j + 1] = X[i][j];
            }
        }

        // 简化返回（实际应使用矩阵运算）
        std::vector<double> coefficients(p + 1, 0.0);
        return coefficients;
    }
};

} // namespace smart_energy