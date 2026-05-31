"""
数据处理模块 - 封装Pandas聚合和Scikit-learn预测模型逻辑
该模块可被FastAPI端点、Streamlit和React应用共享调用，体现"逻辑复用"
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import joblib
import logging
import os

logger = logging.getLogger(__name__)

# 模型存储路径
MODEL_DIR = os.getenv("MODEL_DIR", "models")


class EnergyDataProcessor:
    """能耗数据处理器 - 使用Pandas进行数据聚合分析"""

    def __init__(self):
        pass

    @staticmethod
    def readings_to_dataframe(readings: List[Dict]) -> pd.DataFrame:
        """
        将读数列表转换为Pandas DataFrame

        Args:
            readings: 读数字典列表

        Returns:
            pd.DataFrame: 包含能耗数据的DataFrame
        """
        if not readings:
            return pd.DataFrame()

        df = pd.DataFrame(readings)

        # 确保timestamp列是datetime类型
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])

        return df

    @staticmethod
    def aggregate_by_hour(df: pd.DataFrame) -> pd.DataFrame:
        """
        按小时聚合能耗数据

        Args:
            df: 包含timestamp和power_watts列的DataFrame

        Returns:
            pd.DataFrame: 按小时聚合的数据
        """
        if df.empty:
            return pd.DataFrame()

        df = df.copy()
        df['hour'] = df['timestamp'].dt.floor('H')

        hourly_stats = df.groupby('hour').agg({
            'power_watts': ['mean', 'max', 'min', 'std', 'count'],
            'energy_kwh': 'sum',
            'voltage': 'mean',
            'current_amps': 'mean'
        }).reset_index()

        # 展平多级列名
        hourly_stats.columns = [
            'hour', 'avg_power', 'max_power', 'min_power', 'power_std',
            'reading_count', 'total_energy_kwh', 'avg_voltage', 'avg_current'
        ]

        # 填充NaN值
        hourly_stats = hourly_stats.fillna(0)

        return hourly_stats

    @staticmethod
    def aggregate_by_day(df: pd.DataFrame) -> pd.DataFrame:
        """
        按天聚合能耗数据

        Args:
            df: 包含timestamp和power_watts列的DataFrame

        Returns:
            pd.DataFrame: 按天聚合的数据
        """
        if df.empty:
            return pd.DataFrame()

        df = df.copy()
        df['day'] = df['timestamp'].dt.date

        daily_stats = df.groupby('day').agg({
            'power_watts': ['mean', 'max', 'min', 'std', 'count'],
            'energy_kwh': 'sum',
            'voltage': 'mean',
            'current_amps': 'mean'
        }).reset_index()

        daily_stats.columns = [
            'day', 'avg_power', 'max_power', 'min_power', 'power_std',
            'reading_count', 'total_energy_kwh', 'avg_voltage', 'avg_current'
        ]

        daily_stats = daily_stats.fillna(0)

        return daily_stats

    @staticmethod
    def aggregate_by_week(df: pd.DataFrame) -> pd.DataFrame:
        """
        按周聚合能耗数据

        Args:
            df: 包含timestamp和power_watts列的DataFrame

        Returns:
            pd.DataFrame: 按周聚合的数据
        """
        if df.empty:
            return pd.DataFrame()

        df = df.copy()
        df['week'] = df['timestamp'].dt.isocalendar().week
        df['year'] = df['timestamp'].dt.year
        df['year_week'] = df['year'].astype(str) + '-W' + df['week'].astype(str).str.zfill(2)

        weekly_stats = df.groupby('year_week').agg({
            'power_watts': ['mean', 'max', 'min', 'count'],
            'energy_kwh': 'sum'
        }).reset_index()

        weekly_stats.columns = ['year_week', 'avg_power', 'max_power', 'min_power', 'reading_count', 'total_energy_kwh']
        weekly_stats = weekly_stats.fillna(0)

        return weekly_stats

    @staticmethod
    def calculate_cost(df: pd.DataFrame, rate_per_kwh: float = 0.12) -> float:
        """
        计算能耗成本

        Args:
            df: 包含energy_kwh列的DataFrame
            rate_per_kwh: 每千瓦时电价（元）

        Returns:
            float: 总成本
        """
        if df.empty or 'energy_kwh' not in df.columns:
            return 0.0

        total_energy = df['energy_kwh'].sum()
        return round(total_energy * rate_per_kwh, 2)

    @staticmethod
    def detect_anomalies(df: pd.DataFrame, threshold: float = 3.0) -> pd.DataFrame:
        """
        检测能耗异常值（使用Z-score方法）

        Args:
            df: 包含power_watts列的DataFrame
            threshold: Z-score阈值，默认3.0

        Returns:
            pd.DataFrame: 包含异常标记的DataFrame
        """
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
        """
        分析用电高峰时段

        Args:
            df: 包含timestamp和power_watts列的DataFrame

        Returns:
            Dict: 高峰时段统计信息
        """
        if df.empty:
            return {"peak_hours": [], "peak_power": 0}

        df = df.copy()
        df['hour'] = df['timestamp'].dt.hour

        hourly_avg = df.groupby('hour')['power_watts'].mean()

        # 找出功率最高的3个小时
        peak_hours = hourly_avg.nlargest(3).index.tolist()
        peak_power = hourly_avg.max()

        return {
            "peak_hours": peak_hours,
            "peak_power": round(peak_power, 2),
            "hourly_distribution": {str(h): round(p, 2) for h, p in hourly_avg.items()}
        }


class EnergyPredictor:
    """能耗预测模型 - 使用Scikit-learn线性回归"""

    def __init__(self):
        self.model = None
        self.is_trained = False
        self.feature_columns = ['hour', 'day_of_week', 'is_weekend', 'prev_power']

    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        准备训练特征

        Args:
            df: 包含timestamp和power_watts列的DataFrame

        Returns:
            Tuple[pd.DataFrame, pd.Series]: 特征矩阵和目标变量
        """
        df = df.copy()

        # 提取时间特征
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)

        # 创建滞后特征（前一个时间点的功率）
        df['prev_power'] = df['power_watts'].shift(1)
        df = df.dropna()

        if len(df) < 10:
            raise ValueError("Insufficient data for training. Need at least 10 records.")

        X = df[self.feature_columns]
        y = df['power_watts']

        return X, y

    def train(self, df: pd.DataFrame) -> Dict:
        """
        训练预测模型

        Args:
            df: 包含timestamp和power_watts列的DataFrame

        Returns:
            Dict: 训练结果指标
        """
        try:
            X, y = self.prepare_features(df)

            # 划分训练集和测试集
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # 训练线性回归模型
            self.model = LinearRegression()
            self.model.fit(X_train, y_train)

            # 评估模型
            y_pred = self.model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)

            self.is_trained = True

            # 保存模型
            self.save_model()

            return {
                "status": "success",
                "mse": round(mse, 4),
                "r2_score": round(r2, 4),
                "training_samples": len(X_train),
                "test_samples": len(X_test),
                "feature_importance": dict(zip(self.feature_columns, self.model.coef_.tolist()))
            }

        except Exception as e:
            logger.error(f"Model training failed: {e}")
            return {"status": "error", "message": str(e)}

    def predict(self, features: Dict) -> float:
        """
        预测能耗

        Args:
            features: 特征字典，包含hour, day_of_week, is_weekend, prev_power

        Returns:
            float: 预测的功率值
        """
        if not self.is_trained or self.model is None:
            raise RuntimeError("Model not trained. Call train() first.")

        X = pd.DataFrame([features])[self.feature_columns]
        prediction = self.model.predict(X)[0]

        return round(max(0, prediction), 2)

    def predict_next_hours(self, df: pd.DataFrame, hours: int = 24) -> List[Dict]:
        """
        预测未来N小时的能耗

        Args:
            df: 历史数据DataFrame
            hours: 预测小时数

        Returns:
            List[Dict]: 预测结果列表
        """
        if not self.is_trained:
            raise RuntimeError("Model not trained. Call train() first.")

        predictions = []
        last_power = df['power_watts'].iloc[-1] if not df.empty else 0

        current_time = datetime.utcnow()

        for i in range(hours):
            future_time = current_time + timedelta(hours=i+1)

            features = {
                'hour': future_time.hour,
                'day_of_week': future_time.weekday(),
                'is_weekend': 1 if future_time.weekday() >= 5 else 0,
                'prev_power': last_power if i == 0 else predictions[-1]['predicted_power']
            }

            predicted_power = self.predict(features)

            predictions.append({
                "timestamp": future_time.isoformat(),
                "predicted_power": predicted_power,
                "hour": future_time.hour
            })

        return predictions

    def save_model(self, filename: str = "energy_predictor.joblib"):
        """保存训练好的模型"""
        if self.model is None:
            return

        os.makedirs(MODEL_DIR, exist_ok=True)
        filepath = os.path.join(MODEL_DIR, filename)
        joblib.dump(self.model, filepath)
        logger.info(f"Model saved to {filepath}")

    def load_model(self, filename: str = "energy_predictor.joblib") -> bool:
        """加载已保存的模型"""
        filepath = os.path.join(MODEL_DIR, filename)
        if os.path.exists(filepath):
            self.model = joblib.load(filepath)
            self.is_trained = True
            logger.info(f"Model loaded from {filepath}")
            return True
        return False


# 创建全局实例供共享使用
data_processor = EnergyDataProcessor()
energy_predictor = EnergyPredictor()


def get_data_processor() -> EnergyDataProcessor:
    """获取数据处理器实例"""
    return data_processor


def get_energy_predictor() -> EnergyPredictor:
    """获取能耗预测器实例"""
    return energy_predictor