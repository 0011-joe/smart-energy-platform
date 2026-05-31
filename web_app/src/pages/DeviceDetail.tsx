import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Card,
  Row,
  Col,
  Statistic,
  Tag,
  Button,
  Switch,
  Space,
  Spin,
  Descriptions,
  message,
  Tabs,
  DatePicker,
} from 'antd'
import {
  ArrowLeftOutlined,
  ThunderboltOutlined,
  ReloadOutlined,
  PoweroffOutlined,
  LineChartOutlined,
  BarChartOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { deviceApi, readingApi } from '@/services/api'
import { Device, EnergyReading, HourlyStats } from '@/types'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker

export default function DeviceDetail() {
  const { deviceId } = useParams<{ deviceId: string }>()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [device, setDevice] = useState<Device | null>(null)
  const [readings, setReadings] = useState<EnergyReading[]>([])
  const [hourlyStats, setHourlyStats] = useState<HourlyStats[]>([])
  const [switchOn, setSwitchOn] = useState(false)
  const [controlling, setControlling] = useState(false)
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().subtract(24, 'hour'),
    dayjs(),
  ])

  useEffect(() => {
    if (deviceId) {
      fetchDeviceData()
    }
  }, [deviceId])

  const fetchDeviceData = async () => {
    if (!deviceId) return

    try {
      setLoading(true)

      // 获取设备信息
      const deviceData = (await deviceApi.getDevice(deviceId)) as Device
      setDevice(deviceData)
      setSwitchOn(deviceData.status === 'online')

      // 获取设备读数
      const readingsData = (await deviceApi.getDeviceReadings(deviceId, {
        start_time: dateRange[0].toISOString(),
        end_time: dateRange[1].toISOString(),
        limit: 200,
      })) as EnergyReading[]
      setReadings(readingsData)

      // 获取小时统计
      const hourlyData = (await deviceApi.getDeviceHourlyStats(deviceId, 24)) as HourlyStats[]
      setHourlyStats(hourlyData)
    } catch (error) {
      message.error('Failed to fetch device data')
    } finally {
      setLoading(false)
    }
  }

  // 处理设备开关控制
  const handleSwitchChange = async (checked: boolean) => {
    if (!deviceId) return

    setControlling(true)
    try {
      // 这里应该调用设备控制API
      // await deviceApi.controlDevice(deviceId, { power: checked })
      setSwitchOn(checked)
      message.success(`Device ${checked ? 'turned on' : 'turned off'}`)

      // 模拟通过MQTT发送控制命令
      await new Promise((resolve) => setTimeout(resolve, 500))
    } catch (error) {
      message.error('Failed to control device')
    } finally {
      setControlling(false)
    }
  }

  // 功率曲线图表配置
  const getPowerChartOption = () => ({
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const param = params[0]
        return `${dayjs(param.name).format('YYYY-MM-DD HH:mm:ss')}<br/>功率: ${param.value} W`
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true,
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100,
      },
      {
        start: 0,
        end: 100,
      },
    ],
    xAxis: {
      type: 'category',
      data: readings.map((r) => r.timestamp),
      axisLabel: {
        formatter: (value: string) => dayjs(value).format('HH:mm'),
        rotate: 45,
      },
    },
    yAxis: {
      type: 'value',
      name: '功率 (W)',
    },
    series: [
      {
        name: '功率',
        type: 'line',
        smooth: true,
        symbol: 'none',
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(14, 165, 233, 0.4)' },
              { offset: 1, color: 'rgba(14, 165, 233, 0.05)' },
            ],
          },
        },
        lineStyle: {
          color: '#0ea5e9',
          width: 2,
        },
        data: readings.map((r) => r.power_watts),
      },
    ],
  })

  // 小时统计柱状图
  const getHourlyBarOption = () => ({
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: hourlyStats.map((item) => dayjs(item.hour).format('HH:mm')),
    },
    yAxis: {
      type: 'value',
      name: '功率 (W)',
    },
    series: [
      {
        name: '平均功率',
        type: 'bar',
        barWidth: '60%',
        itemStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: '#0ea5e9' },
              { offset: 1, color: '#7dd3fc' },
            ],
          },
          borderRadius: [4, 4, 0, 0],
        },
        data: hourlyStats.map((item) => item.avg_power),
      },
      {
        name: '最大功率',
        type: 'bar',
        barWidth: '60%',
        itemStyle: {
          color: 'rgba(239, 68, 68, 0.3)',
          borderRadius: [4, 4, 0, 0],
        },
        data: hourlyStats.map((item) => item.max_power),
      },
    ],
  })

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Spin size="large" tip="Loading device..." />
      </div>
    )
  }

  if (!device) {
    return (
      <div className="p-6">
        <div className="text-center">
          <h2 className="text-xl font-semibold mb-4">Device not found</h2>
          <Button onClick={() => navigate('/devices')}>Back to Devices</Button>
        </div>
      </div>
    )
  }

  const statusColorMap: Record<string, string> = {
    online: 'green',
    offline: 'default',
    error: 'red',
    maintenance: 'orange',
  }

  return (
    <div className="p-6">
      {/* 头部 */}
      <div className="flex items-center justify-between mb-6">
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/devices')}>
            返回
          </Button>
          <h1 className="text-2xl font-bold">{device.name}</h1>
          <Tag color={statusColorMap[device.status]}>{device.status.toUpperCase()}</Tag>
        </Space>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={fetchDeviceData}>
            刷新
          </Button>
        </Space>
      </div>

      {/* 设备信息 */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} lg={16}>
          <Card title="设备信息">
            <Descriptions column={{ xs: 1, sm: 2, lg: 3 }}>
              <Descriptions.Item label="设备ID">{device.device_id}</Descriptions.Item>
              <Descriptions.Item label="设备类型">
                <Tag color="blue">{device.device_type.replace('_', ' ').toUpperCase()}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="位置">{device.location || '-'}</Descriptions.Item>
              <Descriptions.Item label="制造商">{device.manufacturer || '-'}</Descriptions.Item>
              <Descriptions.Item label="型号">{device.model || '-'}</Descriptions.Item>
              <Descriptions.Item label="固件版本">{device.firmware_version || '-'}</Descriptions.Item>
              <Descriptions.Item label="最后在线">
                {device.last_seen ? dayjs(device.last_seen).format('YYYY-MM-DD HH:mm:ss') : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {dayjs(device.created_at).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>

        {/* 设备控制 */}
        <Col xs={24} lg={8}>
          <Card title="设备控制">
            <div className="text-center">
              <div className="mb-6">
                <PoweroffOutlined
                  style={{ fontSize: 64, color: switchOn ? '#52c41a' : '#d9d9d9' }}
                />
              </div>
              <div className="mb-4">
                <span className="text-lg font-medium mr-4">电源开关</span>
                <Switch
                  checked={switchOn}
                  onChange={handleSwitchChange}
                  loading={controlling}
                  checkedChildren="开"
                  unCheckedChildren="关"
                  size="default"
                />
              </div>
              <Tag color={switchOn ? 'green' : 'default'} className="text-base px-4 py-1">
                {switchOn ? '设备运行中' : '设备已关闭'}
              </Tag>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="当前功率"
              value={
                readings.length > 0 ? readings[readings.length - 1].power_watts : 0
              }
              suffix="W"
              prefix={<ThunderboltOutlined />}
              precision={1}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="平均功率"
              value={
                hourlyStats.length > 0
                  ? hourlyStats.reduce((sum, s) => sum + s.avg_power, 0) / hourlyStats.length
                  : 0
              }
              suffix="W"
              precision={1}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="最大功率"
              value={
                hourlyStats.length > 0
                  ? Math.max(...hourlyStats.map((s) => s.max_power))
                  : 0
              }
              suffix="W"
              precision={1}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="今日用电"
              value={
                hourlyStats.length > 0
                  ? hourlyStats.reduce((sum, s) => sum + s.total_energy_kwh, 0)
                  : 0
              }
              suffix="kWh"
              precision={2}
            />
          </Card>
        </Col>
      </Row>

      {/* 图表区域 */}
      <Tabs
        defaultActiveKey="realtime"
        items={[
          {
            key: 'realtime',
            label: (
              <span>
                <LineChartOutlined />
                实时功率曲线
              </span>
            ),
            children: (
              <Card>
                <ReactECharts option={getPowerChartOption()} style={{ height: 400 }} />
              </Card>
            ),
          },
          {
            key: 'hourly',
            label: (
              <span>
                <BarChartOutlined />
                小时统计
              </span>
            ),
            children: (
              <Card>
                <ReactECharts option={getHourlyBarOption()} style={{ height: 400 }} />
              </Card>
            ),
          },
        ]}
      />
    </div>
  )
}