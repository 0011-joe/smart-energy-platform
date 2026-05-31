#pragma once

#include "types.h"
#include <vector>
#include <map>
#include <string>
#include <optional>

namespace smart_energy {

/**
 * 能耗数据处理器
 *
 * 使用C++实现高性能的数据聚合和分析功能
 * 比Python Pandas实现快10-100倍
 */
class DataProcessor {
public:
    DataProcessor() = default;
    ~DataProcessor() = default;

    /**
     * 按小时聚合数据
     * @param readings 原始读数列表
     * @return 按小时聚合的统计数据
     */
    std::vector<AggregatedStats> aggregate_by_hour(const std::vector<Reading>& readings);

    /**
     * 按天聚合数据
     * @param readings 原始读数列表
     * @return 按天聚合的统计数据
     */
    std::vector<AggregatedStats> aggregate_by_day(const std::vector<Reading>& readings);

    /**
     * 按周聚合数据
     * @param readings 原始读数列表
     * @return 按周聚合的统计数据
     */
    std::vector<AggregatedStats> aggregate_by_week(const std::vector<Reading>& readings);

    /**
     * 计算能耗成本
     * @param readings 原始读数列表
     * @param rate_per_kwh 每千瓦时电价
     * @return 总成本
     */
    double calculate_cost(const std::vector<Reading>& readings, double rate_per_kwh = 0.12);

    /**
     * 检测异常值（Z-score方法）
     * @param readings 原始读数列表
     * @param threshold Z-score阈值（默认3.0）
     * @return 异常检测结果
     */
    std::vector<AnomalyDetection> detect_anomalies(
        const std::vector<Reading>& readings,
        double threshold = 3.0
    );

    /**
     * 计算24小时负荷分布曲线
     * @param readings 原始读数列表
     * @return 24小时负荷分布
     */
    std::vector<LoadProfile> calculate_load_profile(const std::vector<Reading>& readings);

    /**
     * 分析用电高峰时段
     * @param readings 原始读数列表
     * @return 高峰时段信息（小时 -> 平均功率）
     */
    std::map<int, double> analyze_peak_hours(const std::vector<Reading>& readings);

    /**
     * 计算统计数据
     * @param values 数值列表
     * @return {mean, std, min, max}
     */
    struct Statistics {
        double mean;
        double std;
        double min;
        double max;
        double sum;
        int count;
    };

    Statistics calculate_statistics(const std::vector<double>& values);

    /**
     * 计算皮尔逊相关系数
     * @param x 第一组数据
     * @param y 第二组数据
     * @return 相关系数 (-1 到 1)
     */
    double calculate_correlation(const std::vector<double>& x, const std::vector<double>& y);

private:
    /**
     * 按时间桶聚合的通用方法
     */
    std::vector<AggregatedStats> aggregate_by_bucket(
        const std::vector<Reading>& readings,
        std::function<Timestamp(const Timestamp&)> bucket_func
    );
};

} // namespace smart_energy