"""
Smart Energy Platform - 数据分析工具

基于Streamlit构建的高级数据分析界面
功能包括：
- 设备能耗数据可视化
- 时间序列分析
- 用电负荷分布分析
- 温度相关性分析
- 预测模型训练与评估
"""

import json
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from plotly.subplots import make_subplots

# ============================================================================
# 配置
# ============================================================================

API_BASE_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000/api")

# 页面配置
st.set_page_config(
    page_title="Smart Energy Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #0ea5e9;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.8;
    }
    .stPlotlyChart {
        border-radius: 1rem;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# API调用函数
# ============================================================================

@st.cache_data(ttl=300)
def fetch_devices():
    """获取设备列表"""
    try:
        response = requests.get(f"{API_BASE_URL}/devices", timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Failed to fetch devices: {e}")
        return []


@st.cache_data(ttl=60)
def fetch_device_readings(device_id: str, start_time: str, end_time: str, limit: int = 1000):
    """获取设备读数"""
    try:
        params = {
            "start_time": start_time,
            "end_time": end_time,
            "limit": limit
        }
        response = requests.get(
            f"{API_BASE_URL}/devices/{device_id}/readings",
            params=params,
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Failed to fetch readings: {e}")
        return []


@st.cache_data(ttl=300)
def fetch_hourly_stats(device_id: str, hours: int = 24):
    """获取小时统计"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/devices/{device_id}/readings/hourly",
            params={"hours": hours},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Failed to fetch hourly stats: {e}")
        return []


@st.cache_data(ttl=300)
def fetch_daily_stats(device_id: str, days: int = 7):
    """获取日统计"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/devices/{device_id}/readings/daily",
            params={"days": days},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Failed to fetch daily stats: {e}")
        return []


# ============================================================================
# 数据处理函数
# ============================================================================

def readings_to_dataframe(readings: list) -> pd.DataFrame:
    """将读数列表转换为DataFrame"""
    if not readings:
        return pd.DataFrame()

    df = pd.DataFrame(readings)
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
    return df


def aggregate_by_hour(df: pd.DataFrame) -> pd.DataFrame:
    """按小时聚合数据"""
    if df.empty:
        return df

    df = df.copy()
    df['hour'] = df['timestamp'].dt.floor('H')

    hourly = df.groupby('hour').agg({
        'power_watts': ['mean', 'max', 'min', 'std', 'count'],
        'energy_kwh': 'sum',
        'voltage': 'mean',
        'current_amps': 'mean'
    }).reset_index()

    hourly.columns = [
        'hour', 'avg_power', 'max_power', 'min_power', 'power_std',
        'reading_count', 'total_energy', 'avg_voltage', 'avg_current'
    ]

    return hourly.fillna(0)


def aggregate_by_day(df: pd.DataFrame) -> pd.DataFrame:
    """按天聚合数据"""
    if df.empty:
        return df

    df = df.copy()
    df['day'] = df['timestamp'].dt.date

    daily = df.groupby('day').agg({
        'power_watts': ['mean', 'max', 'min', 'sum', 'count'],
        'energy_kwh': 'sum'
    }).reset_index()

    daily.columns = ['day', 'avg_power', 'max_power', 'min_power', 'total_power', 'reading_count', 'total_energy']
    daily['day'] = pd.to_datetime(daily['day'])

    return daily.fillna(0)


def detect_anomalies(df: pd.DataFrame, threshold: float = 2.5) -> pd.DataFrame:
    """检测异常值（Z-score方法）"""
    if df.empty:
        return df

    df = df.copy()
    mean_power = df['power_watts'].mean()
    std_power = df['power_watts'].std()

    if std_power > 0:
        df['z_score'] = (df['power_watts'] - mean_power) / std_power
        df['is_anomaly'] = abs(df['z_score']) > threshold
    else:
        df['z_score'] = 0
        df['is_anomaly'] = False

    return df


def calculate_load_profile(df: pd.DataFrame) -> pd.DataFrame:
    """计算负荷分布曲线"""
    if df.empty:
        return df

    df = df.copy()
    df['hour'] = df['timestamp'].dt.hour

    load_profile = df.groupby('hour').agg({
        'power_watts': ['mean', 'std', 'count']
    }).reset_index()

    load_profile.columns = ['hour', 'avg_power', 'std_power', 'count']
    load_profile['std_power'] = load_profile['std_power'].fillna(0)

    return load_profile


# ============================================================================
# 页面函数
# ============================================================================

def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/electrical.png", width=64)
        st.title("⚡ Smart Energy")
        st.markdown("---")

        # 获取设备列表
        devices = fetch_devices()

        if not devices:
            st.warning("No devices found. Please ensure the API is running.")
            return None, None, None

        # 设备选择
        device_options = {d['name']: d['device_id'] for d in devices}
        selected_device_name = st.selectbox(
            "🔌 选择设备",
            options=list(device_options.keys()),
            index=0
        )
        selected_device_id = device_options[selected_device_name]

        st.markdown("---")

        # 时间范围选择
        st.subheader("📅 时间范围")
        time_range = st.selectbox(
            "预设时间范围",
            ["最近1小时", "最近6小时", "最近24小时", "最近7天", "最近30天", "自定义"],
            index=2
        )

        now = datetime.utcnow()

        if time_range == "最近1小时":
            start_time = now - timedelta(hours=1)
            end_time = now
        elif time_range == "最近6小时":
            start_time = now - timedelta(hours=6)
            end_time = now
        elif time_range == "最近24小时":
            start_time = now - timedelta(hours=24)
            end_time = now
        elif time_range == "最近7天":
            start_time = now - timedelta(days=7)
            end_time = now
        elif time_range == "最近30天":
            start_time = now - timedelta(days=30)
            end_time = now
        else:
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("开始日期", value=now - timedelta(days=1))
            with col2:
                end_date = st.date_input("结束日期", value=now)
            start_time = datetime.combine(start_date, datetime.min.time())
            end_time = datetime.combine(end_date, datetime.max.time())

        st.markdown("---")

        # 分析选项
        st.subheader("📊 分析选项")
        show_anomalies = st.checkbox("显示异常检测", value=True)
        show_prediction = st.checkbox("显示预测分析", value=False)

        return selected_device_id, (start_time, end_time), {
            "show_anomalies": show_anomalies,
            "show_prediction": show_prediction
        }


def render_overview_tab(df: pd.DataFrame, hourly_stats: list):
    """渲染概览标签页"""
    # 统计卡片
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_power = df['power_watts'].mean() if not df.empty else 0
        st.metric("平均功率", f"{avg_power:.1f} W", delta=None)

    with col2:
        max_power = df['power_watts'].max() if not df.empty else 0
        st.metric("最大功率", f"{max_power:.1f} W", delta=None)

    with col3:
        total_energy = df['energy_kwh'].sum() if not df.empty else 0
        st.metric("总用电量", f"{total_energy:.2f} kWh", delta=None)

    with col4:
        reading_count = len(df)
        st.metric("数据点数", f"{reading_count:,}", delta=None)

    st.markdown("---")

    # 功率曲线图
    if not df.empty:
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['power_watts'],
            mode='lines',
            name='功率',
            line=dict(color='#0ea5e9', width=2),
            fill='tozeroy',
            fillcolor='rgba(14, 165, 233, 0.1)'
        ))

        fig.update_layout(
            title="功率变化曲线",
            xaxis_title="时间",
            yaxis_title="功率 (W)",
            hovermode='x unified',
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

    # 小时统计柱状图
    if hourly_stats:
        hourly_df = pd.DataFrame(hourly_stats)
        hourly_df['hour'] = pd.to_datetime(hourly_df['hour'])

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Bar(
                x=hourly_df['hour'],
                y=hourly_df['avg_power'],
                name='平均功率',
                marker_color='#0ea5e9',
                opacity=0.7
            ),
            secondary_y=False
        )

        fig.add_trace(
            go.Scatter(
                x=hourly_df['hour'],
                y=hourly_df['total_energy_kwh'],
                name='用电量',
                line=dict(color='#f59e0b', width=3),
                mode='lines+markers'
            ),
            secondary_y=True
        )

        fig.update_layout(
            title="小时统计",
            hovermode='x unified',
            height=350
        )

        fig.update_xaxes(title_text="时间")
        fig.update_yaxes(title_text="功率 (W)", secondary_y=False)
        fig.update_yaxes(title_text="用电量 (kWh)", secondary_y=True)

        st.plotly_chart(fig, use_container_width=True)


def render_load_analysis_tab(df: pd.DataFrame):
    """渲染负荷分析标签页"""
    if df.empty:
        st.warning("No data available for load analysis")
        return

    st.subheader("📊 用电负荷分布分析")

    col1, col2 = st.columns(2)

    with col1:
        # 负荷曲线
        load_profile = calculate_load_profile(df)

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=load_profile['hour'],
            y=load_profile['avg_power'],
            mode='lines+markers',
            name='平均功率',
            line=dict(color='#0ea5e9', width=3),
            marker=dict(size=8)
        ))

        # 添加置信区间
        fig.add_trace(go.Scatter(
            x=pd.concat([load_profile['hour'], load_profile['hour'][::-1]]),
            y=pd.concat([
                load_profile['avg_power'] + load_profile['std_power'],
                (load_profile['avg_power'] - load_profile['std_power'])[::-1]
            ]),
            fill='toself',
            fillcolor='rgba(14, 165, 233, 0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='标准差范围'
        ))

        fig.update_layout(
            title="24小时负荷曲线",
            xaxis_title="小时",
            yaxis_title="平均功率 (W)",
            xaxis=dict(tickmode='linear', dtick=1),
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # 功率分布直方图
        fig = px.histogram(
            df,
            x='power_watts',
            nbins=50,
            title="功率分布直方图",
            labels={'power_watts': '功率 (W)'},
            color_discrete_sequence=['#0ea5e9']
        )

        fig.update_layout(
            xaxis_title="功率 (W)",
            yaxis_title="频次",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

    # 负荷统计
    st.subheader("负荷统计指标")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        peak_power = df['power_watts'].max()
        st.metric("峰值功率", f"{peak_power:.1f} W")

    with col2:
        avg_power = df['power_watts'].mean()
        st.metric("平均功率", f"{avg_power:.1f} W")

    with col3:
        load_factor = (avg_power / peak_power * 100) if peak_power > 0 else 0
        st.metric("负荷率", f"{load_factor:.1f}%")

    with col4:
        peak_hour = df.groupby(df['timestamp'].dt.hour)['power_watts'].mean().idxmax()
        st.metric("高峰时段", f"{peak_hour}:00")


def render_anomaly_tab(df: pd.DataFrame):
    """渲染异常检测标签页"""
    if df.empty:
        st.warning("No data available for anomaly detection")
        return

    st.subheader("🔍 异常检测分析")

    # 参数设置
    col1, col2 = st.columns([1, 3])

    with col1:
        threshold = st.slider("Z-score阈值", 1.0, 5.0, 2.5, 0.1)

    # 检测异常
    df_with_anomalies = detect_anomalies(df, threshold)
    anomalies = df_with_anomalies[df_with_anomalies['is_anomaly']]

    # 统计信息
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("总数据点", len(df))
    with col2:
        st.metric("异常点数", len(anomalies))
    with col3:
        anomaly_rate = (len(anomalies) / len(df) * 100) if len(df) > 0 else 0
        st.metric("异常率", f"{anomaly_rate:.2f}%")

    # 异常分布图
    fig = go.Figure()

    # 正常数据
    normal_data = df_with_anomalies[~df_with_anomalies['is_anomaly']]
    fig.add_trace(go.Scatter(
        x=normal_data['timestamp'],
        y=normal_data['power_watts'],
        mode='markers',
        name='正常',
        marker=dict(color='#0ea5e9', size=6)
    ))

    # 异常数据
    if not anomalies.empty:
        fig.add_trace(go.Scatter(
            x=anomalies['timestamp'],
            y=anomalies['power_watts'],
            mode='markers',
            name='异常',
            marker=dict(color='#ef4444', size=10, symbol='x')
        ))

    fig.update_layout(
        title=f"异常检测结果 (Z-score > {threshold})",
        xaxis_title="时间",
        yaxis_title="功率 (W)",
        hovermode='closest',
        height=450
    )

    st.plotly_chart(fig, use_container_width=True)

    # 异常详情表格
    if not anomalies.empty:
        st.subheader("异常数据详情")
        st.dataframe(
            anomalies[['timestamp', 'power_watts', 'voltage', 'current_amps', 'z_score']].head(100),
            use_container_width=True
        )


def render_prediction_tab(df: pd.DataFrame):
    """渲染预测分析标签页"""
    if df.empty or len(df) < 50:
        st.warning("需要至少50个数据点进行预测分析")
        return

    st.subheader("🔮 预测分析")

    # 导入预测模块
    try:
        import sys
        sys.path.append('../data_service')
        from app.core.data_processor import EnergyPredictor

        predictor = EnergyPredictor()

        col1, col2 = st.columns([1, 3])

        with col1:
            st.markdown("### 模型参数")
            test_size = st.slider("测试集比例", 0.1, 0.4, 0.2, 0.05)
            predict_hours = st.slider("预测时长(小时)", 6, 72, 24)

            if st.button("训练模型", type="primary"):
                with st.spinner("正在训练模型..."):
                    result = predictor.train(df)

                    if result['status'] == 'success':
                        st.success("模型训练成功！")
                        st.metric("R² Score", f"{result['r2_score']:.4f}")
                        st.metric("MSE", f"{result['mse']:.4f}")
                        st.metric("训练样本", result['training_samples'])

                        # 保存训练状态到session
                        st.session_state['model_trained'] = True
                        st.session_state['predictor'] = predictor
                    else:
                        st.error(f"训练失败: {result.get('message')}")

        with col2:
            if st.session_state.get('model_trained'):
                predictor = st.session_state['predictor']

                # 生成预测
                predictions = predictor.predict_next_hours(df, predict_hours)
                pred_df = pd.DataFrame(predictions)
                pred_df['timestamp'] = pd.to_datetime(pred_df['timestamp'])

                # 绘制预测图
                fig = go.Figure()

                # 历史数据
                fig.add_trace(go.Scatter(
                    x=df['timestamp'].tail(100),
                    y=df['power_watts'].tail(100),
                    mode='lines',
                    name='历史数据',
                    line=dict(color='#0ea5e9', width=2)
                ))

                # 预测数据
                fig.add_trace(go.Scatter(
                    x=pred_df['timestamp'],
                    y=pred_df['predicted_power'],
                    mode='lines+markers',
                    name='预测值',
                    line=dict(color='#f59e0b', width=2, dash='dash'),
                    marker=dict(size=6)
                ))

                fig.update_layout(
                    title="功率预测",
                    xaxis_title="时间",
                    yaxis_title="功率 (W)",
                    hovermode='x unified',
                    height=400
                )

                st.plotly_chart(fig, use_container_width=True)

                # 预测统计
                st.subheader("预测统计")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("预测平均功率", f"{pred_df['predicted_power'].mean():.1f} W")
                with col2:
                    st.metric("预测最大功率", f"{pred_df['predicted_power'].max():.1f} W")
                with col3:
                    st.metric("预测最小功率", f"{pred_df['predicted_power'].min():.1f} W")

                # 预测数据表
                st.subheader("预测数据详情")
                st.dataframe(pred_df, use_container_width=True)
            else:
                st.info("请先训练模型")

    except ImportError as e:
        st.error(f"Failed to import predictor: {e}")


def render_correlation_tab(df: pd.DataFrame):
    """渲染相关性分析标签页"""
    if df.empty:
        st.warning("No data available for correlation analysis")
        return

    st.subheader("📈 相关性分析")

    # 检查是否有温度数据
    has_temperature = 'metadata' in df.columns and df['metadata'].apply(
        lambda x: isinstance(x, dict) and 'temperature' in x if x else False
    ).any()

    if has_temperature:
        # 提取温度数据
        df_with_temp = df.copy()
        df_with_temp['temperature'] = df_with_temp['metadata'].apply(
            lambda x: x.get('temperature', None) if isinstance(x, dict) else None
        )
        df_with_temp = df_with_temp.dropna(subset=['temperature'])

        col1, col2 = st.columns(2)

        with col1:
            # 功率与温度散点图
            fig = px.scatter(
                df_with_temp,
                x='temperature',
                y='power_watts',
                title="功率 vs 温度",
                labels={'temperature': '温度 (°C)', 'power_watts': '功率 (W)'},
                trendline='ols',
                color_discrete_sequence=['#0ea5e9']
            )

            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

            # 计算相关系数
            correlation = df_with_temp['temperature'].corr(df_with_temp['power_watts'])
            st.metric("相关系数", f"{correlation:.4f}")

        with col2:
            # 温度分布
            fig = px.histogram(
                df_with_temp,
                x='temperature',
                nbins=30,
                title="温度分布",
                labels={'temperature': '温度 (°C)'},
                color_discrete_sequence='#f59e0b'
            )

            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("当前数据不包含温度信息")

    # 功率与电压相关性
    if 'voltage' in df.columns:
        st.subheader("功率与电压关系")

        fig = px.scatter(
            df,
            x='voltage',
            y='power_watts',
            title="功率 vs 电压",
            labels={'voltage': '电压 (V)', 'power_watts': '功率 (W)'},
            color_discrete_sequence=['#8b5cf6']
        )

        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# 主函数
# ============================================================================

def main():
    """主函数"""

    # 渲染侧边栏
    result = render_sidebar()

    if result[0] is None:
        st.stop()

    device_id, time_range, options = result
    start_time, end_time = time_range

    # 页面标题
    st.markdown('<h1 class="main-header">⚡ Smart Energy Analytics</h1>', unsafe_allow_html=True)

    # 获取数据
    with st.spinner("Loading data..."):
        readings = fetch_device_readings(
            device_id,
            start_time.isoformat(),
            end_time.isoformat(),
            limit=5000
        )
        hourly_stats = fetch_hourly_stats(device_id, hours=24)

    df = readings_to_dataframe(readings)

    # 标签页
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 概览",
        "📈 负荷分析",
        "🔍 异常检测",
        "🔮 预测分析",
        "📉 相关性分析"
    ])

    with tab1:
        render_overview_tab(df, hourly_stats)

    with tab2:
        render_load_analysis_tab(df)

    with tab3:
        render_anomaly_tab(df)

    with tab4:
        render_prediction_tab(df)

    with tab5:
        render_correlation_tab(df)

    # 页脚
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <p>Smart Energy Platform - Analytics Tool | Built with Streamlit</p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()