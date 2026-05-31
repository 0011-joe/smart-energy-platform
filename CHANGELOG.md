# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-01-15

### Added

#### 数据服务 (FastAPI)
- 设备能耗数据采集API (POST /api/readings)
- 批量数据创建接口
- 设备管理API (CRUD)
- 设备读数查询（支持时间范围）
- 小时/天粒度统计分析
- 动态设备类型配置
- MQTT消息订阅和处理
- PostgreSQL + InfluxDB双数据库支持
- API缓存 (fastapi-cache2)
- 完整的Pydantic数据验证
- 自动生成的OpenAPI文档

#### 前端应用 (React)
- 仪表盘页面（能耗曲线、设备状态）
- 设备列表页面（搜索、筛选）
- 设备详情页面（实时功率、历史曲线）
- 设备控制UI（开关控制）
- ECharts图表集成
- Ant Design组件库
- 响应式布局设计

#### 数据分析工具 (Streamlit)
- 设备能耗可视化
- 24小时负荷曲线分析
- 功率分布直方图
- Z-score异常检测
- 线性回归预测模型
- 温度相关性分析
- 交互式Plotly图表

#### 设备模拟器
- 5种设备类型模拟（电表、太阳能板、电池、充电桩、HVAC）
- MQTT数据发布
- Matter协议桥接模拟
- 设备状态随机波动

#### 基础设施
- Docker Compose服务编排
- Nginx反向代理配置
- GitHub Actions CI/CD流水线
- 集成测试脚本
- 环境变量配置管理

### Documentation
- 详细的README.md
- API文档（Swagger/ReDoc）
- Matter协议说明
- 项目架构图
- 快速开始指南
- 贡献指南
- MIT许可证

## [0.1.0] - 2024-01-01

### Added
- 项目初始化
- 基础目录结构
- Docker配置文件