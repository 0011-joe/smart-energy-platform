import { useEffect, useState } from 'react'
import { Row, Col, Card, Statistic, Table, Tag, Space, Spin, message } from 'antd'
import {
  ThunderboltOutlined,
  DashboardOutlined,
  RiseOutlined,
  FallOutlined,
  CloudServerOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { deviceApi, readingApi } from '@/services/api'
import { Device, HourlyStats } from '@/types'
import dayjs from 'dayjs'

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [devices, setDevices] = useState<Device[]>([])
  const [hourlyData, setHourlyData] = useState<HourlyStats[]>([])
  const [totalPower, setTotalPower] = useState(0)
  const [todayEnergy, setTodayEnergy] = useState(0)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const devicesData = (await deviceApi.getDevices()) as Device[]
      setDevices(devicesData)

      // 获取汇总数据
      let powerSum = 0
      let energySum = 0
      for (const device of devicesData) {
        try {
          const summary = (await readingApi.getDeviceSummary(device.device_id, 24)) as any
          powerSum += summary?.avg_power || 0
          energySum += summary?.total_energy_kwh || 0
        } catch {
          // 忽略单个设备的错误
        }
      }
      setTotalPower(powerSum)
      setTodayEnergy(energySum)

      // 获取第一个设备的小时数据用于图表
      if (devicesData.length > 0) {
        const hourlyStats = (await deviceApi.getDeviceHourlyStats(
          devicesData[0].device_id,
          24
        )) as HourlyStats[]
        setHourlyData(hourlyStats)
      }
    } catch (error) {
      message.error('Failed to fetch data')
    } finally {
      setLoading(false)
    }
  }

  // 能耗曲线图表配置
  const getEnergyChartOption = () => ({
    tooltip: {
      trigger: 'axis',
      formatter: '{b}<br />功率: {c} W',
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: hourlyData.map((item) => dayjs(item.hour).format('HH:mm')),
    },
    yAxis: {
      type: 'value',
      name: '功率 (W)',
      axisLabel: {
        formatter: '{value}',
      },
    },
    series: [
      {
        name: '平均功率',
        type: 'line',
        smooth: true,
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(14, 165, 233, 0.3)' },
              { offset: 1, color: 'rgba(14, 165, 233, 0.05)' },
            ],
          },
        },
        lineStyle: {
          color: '#0ea5e9',
          width: 2,
        },
        itemStyle: {
          color: '#0ea5e9',
        },
        data: hourlyData.map((item) => item.avg_power),
      },
    ],
  })

  // 设备类型分布图表
  const getDeviceTypeChartOption = () => {
    const typeCount: Record<string, number> = {}
    devices.forEach((device) => {
      typeCount[device.device_type] = (typeCount[device.device_type] || 0) + 1
    })

    return {
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)',
      },
      legend: {
        orient: 'vertical',
        left: 'left',
      },
      series: [
        {
          name: '设备类型',
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2,
          },
          label: {
            show: false,
            position: 'center',
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 16,
              fontWeight: 'bold',
            },
          },
          labelLine: {
            show: false,
          },
          data: Object.entries(typeCount).map(([name, value]) => ({
            name: name.replace('_', ' ').toUpperCase(),
            value,
          })),
        },
      ],
    }
  }

  // 设备状态表格列
  const deviceColumns = [
    {
      title: '设备名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <span className="font-medium">{text}</span>,
    },
    {
      title: '类型',
      dataIndex: 'device_type',
      key: 'device_type',
      render: (type: string) => (
        <Tag color="blue">{type.replace('_', ' ').toUpperCase()}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colorMap: Record<string, string> = {
          online: 'green',
          offline: 'default',
          error: 'red',
          maintenance: 'orange',
        }
        return <Tag color={colorMap[status] || 'default'}>{status.toUpperCase()}</Tag>
      },
    },
    {
      title: '最后在线',
      dataIndex: 'last_seen',
      key: 'last_seen',
      render: (text: string) => (text ? dayjs(text).format('YYYY-MM-DD HH:mm:ss') : '-'),
    },
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Spin size="large" tip="Loading dashboard..." />
      </div>
    )
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">仪表盘</h1>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="在线设备"
              value={devices.filter((d) => d.status === 'online').length}
              suffix={`/ ${devices.length}`}
              prefix={<CloudServerOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="当前总功率"
              value={totalPower}
              suffix="W"
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="今日用电"
              value={todayEnergy}
              suffix="kWh"
              prefix={<RiseOutlined />}
              precision={2}
              valueStyle={{ color: '#0ea5e9' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="平均功率"
              value={devices.length > 0 ? totalPower / devices.length : 0}
              suffix="W"
              prefix={<DashboardOutlined />}
              precision={1}
            />
          </Card>
        </Col>
      </Row>

      {/* 图表区域 */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} lg={16}>
          <Card title="24小时能耗曲线" extra={<span className="text-gray-400">功率 (W)</span>}>
            <ReactECharts option={getEnergyChartOption()} style={{ height: 350 }} />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="设备类型分布">
            <ReactECharts option={getDeviceTypeChartOption()} style={{ height: 350 }} />
          </Card>
        </Col>
      </Row>

      {/* 设备列表 */}
      <Card title="设备状态概览">
        <Table
          columns={deviceColumns}
          dataSource={devices}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  )
}