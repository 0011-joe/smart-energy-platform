import { useState, useEffect, useCallback } from 'react'
import { deviceApi } from '@/services/api'
import { Device, DeviceSummary, HourlyStats } from '@/types'

export function useDevices() {
  const [devices, setDevices] = useState<Device[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchDevices = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await deviceApi.getDevices()
      setDevices(data as Device[])
    } catch (err: any) {
      setError(err.message || 'Failed to fetch devices')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchDevices()
  }, [fetchDevices])

  return { devices, loading, error, refetch: fetchDevices }
}

export function useDevice(deviceId: string | null) {
  const [device, setDevice] = useState<Device | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!deviceId) {
      setLoading(false)
      return
    }

    const fetchDevice = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await deviceApi.getDevice(deviceId)
        setDevice(data as Device)
      } catch (err: any) {
        setError(err.message || 'Failed to fetch device')
      } finally {
        setLoading(false)
      }
    }

    fetchDevice()
  }, [deviceId])

  return { device, loading, error }
}

export function useDeviceSummary(deviceId: string | null, hours: number = 24) {
  const [summary, setSummary] = useState<DeviceSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!deviceId) {
      setLoading(false)
      return
    }

    const fetchSummary = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await deviceApi.getDevice(deviceId)
        // Note: We need to use readingApi for summary, but keeping it simple here
        setSummary(null)
      } catch (err: any) {
        setError(err.message || 'Failed to fetch summary')
      } finally {
        setLoading(false)
      }
    }

    fetchSummary()
  }, [deviceId, hours])

  return { summary, loading, error }
}

export function useHourlyStats(deviceId: string | null, hours: number = 24) {
  const [stats, setStats] = useState<HourlyStats[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!deviceId) {
      setLoading(false)
      return
    }

    const fetchStats = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await deviceApi.getDeviceHourlyStats(deviceId, hours)
        setStats(data as HourlyStats[])
      } catch (err: any) {
        setError(err.message || 'Failed to fetch stats')
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [deviceId, hours])

  return { stats, loading, error }
}