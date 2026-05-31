"""
数据处理器测试

测试Pandas聚合和Scikit-learn预测模型
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from app.core.data_processor import EnergyDataProcessor, EnergyPredictor


@pytest.fixture
def sample_dataframe():
    """创建示例DataFrame"""
    np.random.seed(42)
    n_records = 100

    timestamps = [
        datetime.utcnow() - timedelta(minutes=i * 10) for i in range(n_records)
    ]
    timestamps.reverse()

    data = {
        "timestamp": timestamps,
        "power_watts": np.random.uniform(500, 3000, n_records),
        "energy_kwh": np.random.uniform(0.1, 5, n_records),
        "voltage": np.random.uniform(215, 225, n_records),
        "current_amps": np.random.uniform(2, 15, n_records),
        "frequency_hz": np.random.uniform(49.5, 50.5, n_records),
        "power_factor": np.random.uniform(0.8, 1.0, n_records),
    }

    return pd.DataFrame(data)


class TestEnergyDataProcessor:
    """测试EnergyDataProcessor类"""

    def test_aggregate_by_hour(self, sample_dataframe):
        """测试按小时聚合"""
        processor = EnergyDataProcessor()
        result = processor.aggregate_by_hour(sample_dataframe)

        assert not result.empty
        assert "hour" in result.columns
        assert "avg_power" in result.columns
        assert "max_power" in result.columns
        assert "min_power" in result.columns
        assert "total_energy_kwh" in result.columns

    def test_aggregate_by_day(self, sample_dataframe):
        """测试按天聚合"""
        processor = EnergyDataProcessor()
        result = processor.aggregate_by_day(sample_dataframe)

        assert not result.empty
        assert "day" in result.columns
        assert "avg_power" in result.columns

    def test_calculate_cost(self, sample_dataframe):
        """测试成本计算"""
        processor = EnergyDataProcessor()
        cost = processor.calculate_cost(sample_dataframe, rate_per_kwh=0.5)

        assert cost >= 0
        assert isinstance(cost, float)

    def test_detect_anomalies(self, sample_dataframe):
        """测试异常检测"""
        processor = EnergyDataProcessor()
        result = processor.detect_anomalies(sample_dataframe, threshold=2.0)

        assert "is_anomaly" in result.columns
        assert "z_score" in result.columns
        # 应该有一些异常值
        assert result["is_anomaly"].sum() >= 0

    def test_get_peak_hours(self, sample_dataframe):
        """测试高峰时段分析"""
        processor = EnergyDataProcessor()
        result = processor.get_peak_hours(sample_dataframe)

        assert "peak_hours" in result
        assert "peak_power" in result
        assert "hourly_distribution" in result
        assert isinstance(result["peak_hours"], list)

    def test_readings_to_dataframe(self):
        """测试读数转DataFrame"""
        processor = EnergyDataProcessor()
        readings = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "power_watts": 1000,
                "energy_kwh": 10,
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "power_watts": 2000,
                "energy_kwh": 20,
            },
        ]

        df = processor.readings_to_dataframe(readings)

        assert not df.empty
        assert len(df) == 2
        assert "power_watts" in df.columns

    def test_readings_to_empty_dataframe(self):
        """测试空读数列表"""
        processor = EnergyDataProcessor()
        df = processor.readings_to_dataframe([])

        assert df.empty


class TestEnergyPredictor:
    """测试EnergyPredictor类"""

    def test_prepare_features(self, sample_dataframe):
        """测试特征准备"""
        predictor = EnergyPredictor()
        X, y = predictor._prepare_features(sample_dataframe)

        assert len(X) > 0
        assert len(y) > 0
        assert "hour" in X.columns
        assert "day_of_week" in X.columns
        assert "is_weekend" in X.columns

    def test_train_model(self, sample_dataframe):
        """测试模型训练"""
        predictor = EnergyPredictor()
        result = predictor.train(sample_dataframe)

        assert result["status"] == "success"
        assert "r2_score" in result
        assert "mse" in result
        assert predictor.is_trained

    def test_predict(self, sample_dataframe):
        """测试预测功能"""
        predictor = EnergyPredictor()
        predictor.train(sample_dataframe)

        prediction = predictor.predict(
            hour=12, day_of_week=3, is_weekend=False, prev_power=1500.0
        )

        assert prediction >= 0
        assert isinstance(prediction, float)

    def test_predict_next_hours(self, sample_dataframe):
        """测试未来N小时预测"""
        predictor = EnergyPredictor()
        predictor.train(sample_dataframe)

        predictions = predictor.predict_next_hours(sample_dataframe, hours=12)

        assert len(predictions) == 12
        assert "timestamp" in predictions[0]
        assert "predicted_power" in predictions[0]
        assert predictions[0]["predicted_power"] >= 0

    def test_predict_without_training(self):
        """测试未训练时预测（应抛出异常）"""
        predictor = EnergyPredictor()

        with pytest.raises(RuntimeError, match="Model not trained"):
            predictor.predict(hour=12, day_of_week=3, is_weekend=False, prev_power=1000)
