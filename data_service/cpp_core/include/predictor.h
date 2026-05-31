#pragma once

#include "types.h"
#include <Eigen/Dense>
#include <vector>
#include <string>
#include <map>

namespace smart_energy {

/**
 * 能耗预测模型
 *
 * 使用线性回归进行能耗预测
 * 基于Eigen库实现高性能矩阵运算
 */
class EnergyPredictor {
public:
    EnergyPredictor();
    ~EnergyPredictor() = default;

    /**
     * 训练模型
     * @param readings 历史读数数据
     * @return 训练结果
     */
    TrainingResult train(const std::vector<Reading>& readings);

    /**
     * 预测单点
     * @param hour 小时 (0-23)
     * @param day_of_week 星期几 (0-6, 0=周日)
     * @param is_weekend 是否周末
     * @param prev_power 前一个时间点的功率
     * @return 预测的功率值
     */
    double predict(int hour, int day_of_week, bool is_weekend, double prev_power);

    /**
     * 预测未来N小时
     * @param readings 历史数据（用于获取最后的功率值）
     * @param hours 预测小时数
     * @return 预测结果列表
     */
    std::vector<PredictionResult> predict_next_hours(
        const std::vector<Reading>& readings,
        int hours = 24
    );

    /**
     * 检查模型是否已训练
     */
    bool is_trained() const { return trained_; }

    /**
     * 获取特征重要性
     */
    std::map<std::string, double> get_feature_importance() const;

    /**
     * 获取模型评估指标
     */
    struct ModelMetrics {
        double r2_score;
        double mse;
        double rmse;
        double mae;
    };

    ModelMetrics get_metrics() const { return metrics_; }

    /**
     * 重置模型
     */
    void reset();

private:
    /**
     * 准备特征矩阵
     */
    void prepare_features(
        const std::vector<Reading>& readings,
        Eigen::MatrixXd& X,
        Eigen::VectorXd& y
    );

    /**
     * 特征提取
     */
    struct Features {
        int hour;
        int day_of_week;
        int is_weekend;
        double prev_power;
    };

    Features extract_features(const Reading& reading, double prev_power);

    // 模型参数
    Eigen::VectorXd coefficients_;
    double intercept_;

    // 训练状态
    bool trained_;
    ModelMetrics metrics_;

    // 特征名称
    const std::vector<std::string> feature_names_ = {
        "hour", "day_of_week", "is_weekend", "prev_power"
    };
};

} // namespace smart_energy