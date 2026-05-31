/**
 * Python Bindings for Smart Energy Core (C++)
 *
 * 使用pybind11创建Python模块，提供以下功能：
 * - EnergyPredictor: 高性能能耗预测模型
 * - DataProcessor: 高性能数据处理
 * - Statistics: 统计计算工具
 */

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/chrono.h>

#include "types.h"
#include "data_processor.h"
#include "predictor.h"
#include "statistics.h"

namespace py = pybind11;
using namespace smart_energy;

PYBIND11_MODULE(energy_core, m) {
    m.doc() = "Smart Energy Core - High-performance C++ data processing and prediction";

    // ============================================================================
    // Types
    // ============================================================================

    py::class_<Reading>(m, "Reading")
        .def(py::init<>())
        .def_readwrite("id", &Reading::id)
        .def_readwrite("device_id", &Reading::device_id)
        .def_readwrite("timestamp", &Reading::timestamp)
        .def_readwrite("power_watts", &Reading::power_watts)
        .def_readwrite("energy_kwh", &Reading::energy_kwh)
        .def_readwrite("voltage", &Reading::voltage)
        .def_readwrite("current_amps", &Reading::current_amps)
        .def_readwrite("frequency_hz", &Reading::frequency_hz)
        .def_readwrite("power_factor", &Reading::power_factor)
        .def_readwrite("metadata", &Reading::metadata)
        .def("to_map", &Reading::to_map);

    py::class_<AggregatedStats>(m, "AggregatedStats")
        .def(py::init<>())
        .def_readwrite("time_bucket", &AggregatedStats::time_bucket)
        .def_readwrite("avg_power", &AggregatedStats::avg_power)
        .def_readwrite("max_power", &AggregatedStats::max_power)
        .def_readwrite("min_power", &AggregatedStats::min_power)
        .def_readwrite("std_power", &AggregatedStats::std_power)
        .def_readwrite("total_energy", &AggregatedStats::total_energy)
        .def_readwrite("count", &AggregatedStats::count);

    py::class_<PredictionResult>(m, "PredictionResult")
        .def(py::init<>())
        .def_readwrite("timestamp", &PredictionResult::timestamp)
        .def_readwrite("predicted_power", &PredictionResult::predicted_power)
        .def_readwrite("confidence_lower", &PredictionResult::confidence_lower)
        .def_readwrite("confidence_upper", &PredictionResult::confidence_upper);

    py::class_<TrainingResult>(m, "TrainingResult")
        .def(py::init<>())
        .def_readwrite("success", &TrainingResult::success)
        .def_readwrite("r2_score", &TrainingResult::r2_score)
        .def_readwrite("mse", &TrainingResult::mse)
        .def_readwrite("training_samples", &TrainingResult::training_samples)
        .def_readwrite("test_samples", &TrainingResult::test_samples)
        .def_readwrite("feature_importance", &TrainingResult::feature_importance)
        .def_readwrite("error_message", &TrainingResult::error_message);

    py::class_<LoadProfile>(m, "LoadProfile")
        .def(py::init<>())
        .def_readwrite("hour", &LoadProfile::hour)
        .def_readwrite("avg_power", &LoadProfile::avg_power)
        .def_readwrite("std_power", &LoadProfile::std_power)
        .def_readwrite("peak_power", &LoadProfile::peak_power)
        .def_readwrite("sample_count", &LoadProfile::sample_count);

    py::class_<AnomalyDetection>(m, "AnomalyDetection")
        .def(py::init<>())
        .def_readwrite("timestamp", &AnomalyDetection::timestamp)
        .def_readwrite("value", &AnomalyDetection::value)
        .def_readwrite("z_score", &AnomalyDetection::z_score)
        .def_readwrite("is_anomaly", &AnomalyDetection::is_anomaly);

    // ============================================================================
    // DataProcessor
    // ============================================================================

    py::class_<DataProcessor>(m, "DataProcessor")
        .def(py::init<>())
        .def("aggregate_by_hour", &DataProcessor::aggregate_by_hour,
             "Aggregate readings by hour",
             py::arg("readings"))
        .def("aggregate_by_day", &DataProcessor::aggregate_by_day,
             "Aggregate readings by day",
             py::arg("readings"))
        .def("aggregate_by_week", &DataProcessor::aggregate_by_week,
             "Aggregate readings by week",
             py::arg("readings"))
        .def("calculate_cost", &DataProcessor::calculate_cost,
             "Calculate energy cost",
             py::arg("readings"),
             py::arg("rate_per_kwh") = 0.12)
        .def("detect_anomalies", &DataProcessor::detect_anomalies,
             "Detect anomalies using Z-score",
             py::arg("readings"),
             py::arg("threshold") = 3.0)
        .def("calculate_load_profile", &DataProcessor::calculate_load_profile,
             "Calculate 24-hour load profile",
             py::arg("readings"))
        .def("analyze_peak_hours", &DataProcessor::analyze_peak_hours,
             "Analyze peak hours",
             py::arg("readings"))
        .def("calculate_correlation", &DataProcessor::calculate_correlation,
             "Calculate Pearson correlation coefficient",
             py::arg("x"),
             py::arg("y"));

    // ============================================================================
    // EnergyPredictor
    // ============================================================================

    py::class_<EnergyPredictor>(m, "EnergyPredictor")
        .def(py::init<>())
        .def("train", &EnergyPredictor::train,
             "Train the prediction model",
             py::arg("readings"))
        .def("predict", &EnergyPredictor::predict,
             "Predict power consumption",
             py::arg("hour"),
             py::arg("day_of_week"),
             py::arg("is_weekend"),
             py::arg("prev_power"))
        .def("predict_next_hours", &EnergyPredictor::predict_next_hours,
             "Predict power for next N hours",
             py::arg("readings"),
             py::arg("hours") = 24)
        .def("is_trained", &EnergyPredictor::is_trained,
             "Check if model is trained")
        .def("get_feature_importance", &EnergyPredictor::get_feature_importance,
             "Get feature importance scores")
        .def("get_metrics", &EnergyPredictor::get_metrics,
             "Get model metrics")
        .def("reset", &EnergyPredictor::reset,
             "Reset the model");

    py::class_<EnergyPredictor::ModelMetrics>(m, "ModelMetrics")
        .def_readwrite("r2_score", &EnergyPredictor::ModelMetrics::r2_score)
        .def_readwrite("mse", &EnergyPredictor::ModelMetrics::mse)
        .def_readwrite("rmse", &EnergyPredictor::ModelMetrics::rmse)
        .def_readwrite("mae", &EnergyPredictor::ModelMetrics::mae);

    // ============================================================================
    // Statistics (Static methods)
    // ============================================================================

    py::class_<Statistics>(m, "Statistics")
        .def_static("mean", &Statistics::mean,
                    "Calculate mean",
                    py::arg("values"))
        .def_static("standard_deviation", &Statistics::standard_deviation,
                    "Calculate standard deviation",
                    py::arg("values"))
        .def_static("variance", &Statistics::variance,
                    "Calculate variance",
                    py::arg("values"))
        .def_static("median", &Statistics::median,
                    "Calculate median",
                    py::arg("values"))
        .def_static("percentile", &Statistics::percentile,
                    "Calculate percentile",
                    py::arg("values"),
                    py::arg("p"))
        .def_static("z_score", &Statistics::z_score,
                    "Calculate Z-score",
                    py::arg("value"),
                    py::arg("mean"),
                    py::arg("std_dev"))
        .def_static("pearson_correlation", &Statistics::pearson_correlation,
                    "Calculate Pearson correlation",
                    py::arg("x"),
                    py::arg("y"))
        .def_static("mse", &Statistics::mse,
                    "Calculate mean squared error",
                    py::arg("actual"),
                    py::arg("predicted"))
        .def_static("r2_score", &Statistics::r2_score,
                    "Calculate R² score",
                    py::arg("actual"),
                    py::arg("predicted"));
}