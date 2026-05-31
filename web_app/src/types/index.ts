export interface Device {
  id: string
  device_id: string
  name: string
  device_type: DeviceType
  location?: string
  latitude?: number
  longitude?: number
  status: DeviceStatus
  is_active: boolean
  manufacturer?: string
  model?: string
  firmware_version?: string
  installation_date?: string
  last_seen?: string
  created_at: string
  updated_at?: string
}

export type DeviceType =
  | 'smart_meter'
  | 'solar_panel'
  | 'battery'
  | 'ev_charger'
  | 'hvac'
  | 'lighting'
  | 'appliance'

export type DeviceStatus = 'online' | 'offline' | 'maintenance' | 'error'

export interface EnergyReading {
  id: string
  device_id: string
  timestamp: string
  power_watts: number
  energy_kwh?: number
  voltage?: number
  current_amps?: number
  frequency_hz?: number
  power_factor?: number
  metadata?: Record<string, any>
  created_at: string
}

export interface DeviceSummary {
  device_id: string
  total_readings: number
  avg_power: number
  max_power: number
  min_power: number
  total_energy_kwh: number
  first_reading: string
  last_reading: string
}

export interface HourlyStats {
  hour: string
  avg_power: number
  max_power: number
  min_power: number
  total_energy_kwh: number
  reading_count: number
}

export interface DailyStats {
  day: string
  avg_power: number
  max_power: number
  min_power: number
  total_energy_kwh: number
  reading_count: number
}

export interface ApiResponse<T> {
  data: T
  message?: string
  status: number
}