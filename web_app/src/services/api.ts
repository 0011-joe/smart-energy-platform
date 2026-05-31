import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证token等
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// 设备相关API
export const deviceApi = {
  // 获取设备列表
  getDevices: (params?: {
    device_type?: string
    status?: string
    is_active?: boolean
    limit?: number
    offset?: number
  }) => api.get('/devices', { params }),

  // 获取设备详情
  getDevice: (deviceId: string) => api.get(`/devices/${deviceId}`),

  // 获取设备读数
  getDeviceReadings: (
    deviceId: string,
    params?: {
      start_time?: string
      end_time?: string
      limit?: number
      offset?: number
    }
  ) => api.get(`/devices/${deviceId}/readings`, { params }),

  // 获取设备小时统计
  getDeviceHourlyStats: (deviceId: string, hours?: number) =>
    api.get(`/devices/${deviceId}/readings/hourly`, { params: { hours } }),

  // 获取设备日统计
  getDeviceDailyStats: (deviceId: string, days?: number) =>
    api.get(`/devices/${deviceId}/readings/daily`, { params: { days } }),
}

// 能耗读数API
export const readingApi = {
  // 创建读数
  createReading: (data: {
    device_id: string
    power_watts: number
    energy_kwh?: number
    voltage?: number
    current_amps?: number
    timestamp?: string
  }) => api.post('/readings', data),

  // 批量创建读数
  createReadingsBatch: (readings: any[]) =>
    api.post('/readings/batch', { readings }),

  // 查询读数
  getReadings: (params?: {
    device_id?: string
    start_time?: string
    end_time?: string
    limit?: number
    offset?: number
  }) => api.get('/readings', { params }),

  // 获取设备汇总
  getDeviceSummary: (deviceId: string, hours?: number) =>
    api.get(`/readings/device/${deviceId}/summary`, { params: { hours } }),
}

// 健康检查API
export const healthApi = {
  check: () => api.get('/health'),
  status: () => api.get('/api/status'),
}

export default api