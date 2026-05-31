#include "data_processor.h"
#include "statistics.h"
#include <algorithm>
#include <cmath>
#include <map>

namespace smart_energy {

std::vector<AggregatedStats> DataProcessor::aggregate_by_hour(const std::vector<Reading>& readings) {
    auto bucket_func = [](const Timestamp& ts) -> Timestamp {
        auto time = std::chrono::system_clock::to_time_t(ts);
        auto* tm = std::gmtime(&time);
        tm->tm_min = 0;
        tm->tm_sec = 0;
        return std::chrono::system_clock::from_time_t(std::mktime(tm));
    };

    return aggregate_by_bucket(readings, bucket_func);
}

std::vector<AggregatedStats> DataProcessor::aggregate_by_day(const std::vector<Reading>& readings) {
    auto bucket_func = [](const Timestamp& ts) -> Timestamp {
        auto time = std::chrono::system_clock::to_time_t(ts);
        auto* tm = std::gmtime(&time);
        tm->tm_hour = 0;
        tm->tm_min = 0;
        tm->tm_sec = 0;
        return std::chrono::system_clock::from_time_t(std::mktime(tm));
    };

    return aggregate_by_bucket(readings, bucket_func);
}

std::vector<AggregatedStats> DataProcessor::aggregate_by_week(const std::vector<Reading>& readings) {
    auto bucket_func = [](const Timestamp& ts) -> Timestamp {
        auto time = std::chrono::system_clock::to_time_t(ts);
        auto* tm = std::gmtime(&time);
        // 回到本周一
        int wday = tm->tm_wday;
        if (wday == 0) wday = 7; // 周日 = 7
        tm->tm_mday -= (wday - 1);
        tm->tm_hour = 0;
        tm->tm_min = 0;
        tm->tm_sec = 0;
        return std::chrono::system_clock::from_time_t(std::mktime(tm));
    };

    return aggregate_by_bucket(readings, bucket_func);
}

std::vector<AggregatedStats> DataProcessor::aggregate_by_bucket(
    const std::vector<Reading>& readings,
    std::function<Timestamp(const Timestamp&)> bucket_func
) {
    if (readings.empty()) return {};

    // 按时间桶分组
    std::map<time_t, std::vector<const Reading*>> buckets;

    for (const auto& reading : readings) {
        Timestamp bucket = bucket_func(reading.timestamp);
        auto time = std::chrono::system_clock::to_time_t(bucket);
        buckets[time].push_back(&reading);
    }

    // 计算每个桶的统计
    std::vector<AggregatedStats> results;

    for (const auto& [time, bucket_readings] : buckets) {
        std::vector<double> powers;
        double total_energy = 0.0;

        for (const auto* reading : bucket_readings) {
            powers.push_back(reading->power_watts);
            total_energy += reading->energy_kwh;
        }

        auto stats = Statistics::mean(powers);
        auto std_dev = Statistics::standard_deviation(powers);
        auto min_it = std::min_element(powers.begin(), powers.end());
        auto max_it = std::max_element(powers.begin(), powers.end());

        results.push_back(AggregatedStats{
            std::chrono::system_clock::from_time_t(time),
            stats,
            *max_it,
            *min_it,
            std_dev,
            total_energy,
            static_cast<int>(bucket_readings.size())
        });
    }

    return results;
}

double DataProcessor::calculate_cost(const std::vector<Reading>& readings, double rate_per_kwh) {
    double total_energy = 0.0;
    for (const auto& reading : readings) {
        total_energy += reading.energy_kwh;
    }
    return total_energy * rate_per_kwh;
}

std::vector<AnomalyDetection> DataProcessor::detect_anomalies(
    const std::vector<Reading>& readings,
    double threshold
) {
    if (readings.empty()) return {};

    // 提取功率值
    std::vector<double> powers;
    for (const auto& reading : readings) {
        powers.push_back(reading.power_watts);
    }

    // 计算均值和标准差
    double mean = Statistics::mean(powers);
    double std_dev = Statistics::standard_deviation(powers);

    // 检测异常
    std::vector<AnomalyDetection> results;

    for (size_t i = 0; i < readings.size(); ++i) {
        double z = Statistics::z_score(powers[i], mean, std_dev);

        results.push_back(AnomalyDetection{
            readings[i].timestamp,
            powers[i],
            z,
            std::abs(z) > threshold
        });
    }

    return results;
}

std::vector<LoadProfile> DataProcessor::calculate_load_profile(const std::vector<Reading>& readings) {
    if (readings.empty()) return {};

    // 按小时分组
    std::map<int, std::vector<double>> hourly_powers;

    for (const auto& reading : readings) {
        auto time = std::chrono::system_clock::to_time_t(reading.timestamp);
        auto* tm = std::gmtime(&time);
        int hour = tm->tm_hour;
        hourly_powers[hour].push_back(reading.power_watts);
    }

    // 计算每小时的统计
    std::vector<LoadProfile> results;

    for (int hour = 0; hour < 24; ++hour) {
        auto it = hourly_powers.find(hour);
        if (it != hourly_powers.end()) {
            const auto& powers = it->second;
            auto stats = Statistics::mean(powers);
            auto std_dev = Statistics::standard_deviation(powers);
            auto max_it = std::max_element(powers.begin(), powers.end());

            results.push_back(LoadProfile{
                hour,
                stats,
                std_dev,
                *max_it,
                static_cast<int>(powers.size())
            });
        } else {
            results.push_back(LoadProfile{hour, 0.0, 0.0, 0.0, 0});
        }
    }

    return results;
}

std::map<int, double> DataProcessor::analyze_peak_hours(const std::vector<Reading>& readings) {
    auto profile = calculate_load_profile(readings);

    std::map<int, double> peak_hours;
    for (const auto& load : profile) {
        peak_hours[load.hour] = load.avg_power;
    }

    return peak_hours;
}

DataProcessor::Statistics DataProcessor::calculate_statistics(const std::vector<double>& values) {
    if (values.empty()) {
        return {0.0, 0.0, 0.0, 0.0, 0.0, 0};
    }

    double mean_val = Statistics::mean(values);
    double std_val = Statistics::standard_deviation(values);
    double min_val = *std::min_element(values.begin(), values.end());
    double max_val = *std::max_element(values.begin(), values.end());
    double sum_val = std::accumulate(values.begin(), values.end(), 0.0);

    return {mean_val, std_val, min_val, max_val, sum_val, static_cast<int>(values.size())};
}

double DataProcessor::calculate_correlation(
    const std::vector<double>& x,
    const std::vector<double>& y
) {
    return Statistics::pearson_correlation(x, y);
}

} // namespace smart_energy