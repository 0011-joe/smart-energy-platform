"""
数据处理模块

优先使用C++高性能实现，回退到Python实现
C++版本比Python快10-100倍
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# 尝试导入C++模块
try:
    import energy_core
    HAS_CPP_CORE = True
    logger.info("Using C++ core module for high-performance processing")
except ImportError:
    HAS_CPP_CORE = False
    logger.info("C++ core not available, using Python fallback")


class EnergyDataProcessor:
    """
    能耗数据处理器

    使用Pandas进行数据聚合分析
    如果C++模块可用，优先使用高性能实现
    """

    def __init__(self):
        if HAS_CPP_CORE:
            self._cpp_processor = energy_core.DataProcessor()
        self._use_cpp = HAS_CPP_CORE

    @staticmethod
    def readings_to_dataframe(readings: List[Dict]) -> pd.DataFrame:
        """将读数列表转换为DataFrame"""
        if not readings:
            return pd.DataFrame()

        df = pd.DataFrame(readings)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])

        return df

    def aggregate_by_hour(self, df: pd.DataFrame) -> pd.DataFrame:
        """按小时聚合数据"""
        if df.empty:
            return df

        df = df.copy()
        df['hour'] = df['timestamp'].dt.floor('H')

        hourly_stats = df.groupby('hour').agg({
            'power_watts': ['mean', 'max', 'min', 'std', 'count'],
            'energy_kwh': 'sum',
            'voltage': 'mean',
            'current_amps': 'mean'
        }).reset_index()

        hourly_stats.columns = [
            'hour', 'avg_power', 'max_power', 'min_power', 'power_std',
            'reading_count', 'total_energy_kwh', 'avg_voltage', 'avg_current'
        ]

        return hourly_stats.fillna(0)

    def aggregate_by_day(self, df: pd.DataFrame) -> pd.DataFrame:
        """按天聚合数据"""
        if df.empty:
            return df

        df = df.copy()
        df['day'] = df['timestamp'].dt.date

        daily_stats = df.groupby('day').agg({
            'power_watts': ['mean', 'max', 'min', 'std', 'count'],
            'energy_kwh': 'sum'
        }).reset_index()

        daily_stats.columns = [
            'day', 'avg_power', 'max_power', 'min_power', 'power_std',
            'reading_count', 'total_energy_kwh'
        ]

        return daily_stats.fillna(0)

    @staticmethod
    def calculate_cost(df: pd.DataFrame, rate_per_kwh: float = 0.12) -> float:
        """计算能耗成本"""
        if df.empty or 'energy_kwh' not in df.columns:
            return 0.0
        return round(df['energy_kwh'].sum() * rate_per_kwh, 2)

    @staticmethod
    def detect_anomalies(df: pd.DataFrame, threshold: float = 3.0) -> pd.DataFrame:
        """检测异常值（Z-score方法）"""
        if df.empty:
            return df

        df = df.copy()
        mean_power = df['power_watts'].mean()
        std_power = df['power_watts'].std()

        if std_power == 0:
            df['is_anomaly'] = False
            df['z_score'] = 0
        else:
            df['z_score'] = (df['power_watts'] - mean_power) / std_power
            df['is_anomaly'] = abs(df['z_score']) > threshold

        return df

    @staticmethod
    def get_peak_hours(df: pd.DataFrame) -> Dict:
        """分析用电高峰时段"""
        if df.empty:
            return {"peak_hours": [], "peak_power": 0}

        df = df.copy()
        df['hour'] = df['timestamp'].dt.hour
        hourly_avg = df.groupby('hour')['power_watts'].mean()

        peak_hours = hourly_avg.nlargest(3).index.tolist()
        peak_power = hourly_avg.max()

        return {
            "peak_hours": peak_hours,
            "peak_power": round(peak_power, 2),
            "hourly_distribution": {str(h): round(p, 2) for h, p in hourly_avg.items()}
        }


class EnergyPredictor:
    """
    能耗预测模型

    优先使用C++实现，回退到scikit-learn
    """

    def __init__(self):
        if HAS_CPP_CORE:
            self._cpp_predictor = energy_core.EnergyPredictor()
            self._use_cpp = True
        else:
            from sklearn.linear_model import LinearRegression
            from sklearn.model_selection import train_test_split
            self.model = LinearRegression()
            self._use_cpp = False

        self.is_trained = False
        self.feature_columns = ['hour', 'day_of_week', 'is_weekend', 'prev_power']

    def train(self, df: pd.DataFrame) -> Dict:
        """训练预测模型"""
        try:
            if self._use_cpp:
                # 使用C++实现
                readings = self._df_to_readings(df)
                result = self._cpp_predictor.train(readings)
                self.is_trained = result.success
                return {
                    "status": "success" if result.success else "error",
                    "r2_score": result.r2_score,
                    "mse": result.mse,
                    "training_samples": result.training_samples,
                    "test_samples": result.test_samples,
                    "feature_importance": result.feature_importance,
                    "engine": "c++"
                }
            else:
                # 使用Python实现
                X, y = self._prepare_features(df)
                from sklearn.model_selection import train_test_split
                from sklearn.metrics import mean_squared_error, r2_score

                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                self.model.fit(X_train, y_train)

                y_pred = self.model.predict(X_test)
                mse = mean_squared_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)

                self.is_trained = True
                return {
                    "status": "success",
                    "mse": round(mse, 4),
                    "r2_score": round(r2, 4),
                    "training_samples": len(X_train),
                    "test_samples": len(X_test),
                    "feature_importance": dict(zip(self.feature_columns, self.model.coef_.tolist())),
                    "engine": "python"
                }

        except Exception as e:
            logger.error(f"Model training failed: {e}")
            return {"status": "error", "message": str(e)}

    def predict(self, hour: int, day_of_week: int, is_weekend: bool, prev_power: float) -> float:
        """预测单点功率"""
        if not self.is_trained:
            raise RuntimeError("Model not trained. Call train() first.")

        if self._use_cpp:
            return self._cpp_predictor.predict(hour, day_of_week, is_weekend, prev_power)
        else:
            X = pd.DataFrame([{
                'hour': hour,
                'day_of_week': day_of_week,
                'is_weekend': int(is_weekend),
                'prev_power': prev_power
            }])[self.feature_columns]
            return max(0, self.model.predict(X)[0])

    def predict_next_hours(self, df: pd.DataFrame, hours: int = 24) -> List[Dict]:
        """预测未来N小时"""
        if not self.is_trained:
            raise RuntimeError("Model not trained. Call train() first.")

        if self._use_cpp:
            readings = self._df_to_readings(df)
            predictions = self._cpp_predictor.predict_next_hours(readings, hours)
            return [
                {
                    "timestamp": pred.timestamp,
                    "predicted_power": round(pred.predicted_power, 2),
                    "confidence_lower": round(pred.confidence_lower, 2),
                    "confidence_upper": round(pred.confidence_upper, 2)
                }
                for pred in predictions
            ]
        else:
            # Python实现
            predictions = []
            last_power = df['power_watts'].iloc[-1] if not df.empty else 0

            current_time = datetime.utcnow()
            for i in range(hours):
                future_time = current_time + timedelta(hours=i+1)
                pred_power = self.predict(
                    future_time.hour,
                    future_time.weekday(),
                    future_time.weekday() >= 5,
                    last_power if i == 0 else predictions[-1]['predicted_power']
                )
                predictions.append({
                    "timestamp": future_time.isoformat(),
                    "predicted_power": round(pred_power, 2),
                    "confidence_lower": round(pred_power * 0.9, 2),
                    "confidence_upper": round(pred_power * 1.1, 2)
                })

            return predictions

    def _prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """准备训练特征"""
        df = df.copy()
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        df['prev_power'] = df['power_watts'].shift(1)
        df = df.dropna()

        X = df[self.feature_columns]
        y = df['power_watts']
        return X, y

    def _df_to_readings(self, df: pd.DataFrame) -> List:
        """将DataFrame转换为C++ Reading对象列表"""
        readings = []
        for _, row in df.iterrows():
            r = energy_core.Reading()
            r.device_id = str(row.get('device_id', 'unknown'))
            r.power_watts = float(row['power_watts'])
            r.energy_kwh = float(row.get('energy_kwh', 0))
            r.voltage = float(row.get('voltage', 220))
            r.current_amps = float(row.get('current_amps', 0))
            r.frequency_hz = float(row.get('frequency_hz', 50))
            r.power_factor = float(row.get('power_factor', 1))
            readings.append(r)
        return readings


# 创建全局实例
data_processor = EnergyDataProcessor()
energy_predictor = EnergyPredictor()


def get_data_processor() -> EnergyDataProcessor:
    return data_processor


def get_energy_predictor() -> EnergyPredictor:
    return energy_predictor