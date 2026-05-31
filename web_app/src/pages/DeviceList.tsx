import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Cpu, Search, Filter, RefreshCw } from 'lucide-react'
import { useDevices } from '@/hooks/useDevices'
import { DeviceType } from '@/types'

const deviceTypeLabels: Record<DeviceType, string> = {
  smart_meter: 'Smart Meter',
  solar_panel: 'Solar Panel',
  battery: 'Battery',
  ev_charger: 'EV Charger',
  hvac: 'HVAC',
  lighting: 'Lighting',
  appliance: 'Appliance',
}

const deviceTypeColors: Record<DeviceType, string> = {
  smart_meter: 'bg-blue-100 text-blue-700',
  solar_panel: 'bg-yellow-100 text-yellow-700',
  battery: 'bg-green-100 text-green-700',
  ev_charger: 'bg-purple-100 text-purple-700',
  hvac: 'bg-cyan-100 text-cyan-700',
  lighting: 'bg-orange-100 text-orange-700',
  appliance: 'bg-gray-100 text-gray-700',
}

export default function DeviceList() {
  const { devices, loading, error, refetch } = useDevices()
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState<DeviceType | ''>('')

  const filteredDevices = devices.filter((device) => {
    const matchesSearch =
      device.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      device.device_id.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesType = filterType === '' || device.device_type === filterType
    return matchesSearch && matchesType
  })

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Devices</h1>
          <p className="text-gray-500 mt-1">Manage your smart energy devices</p>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search devices..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value as DeviceType | '')}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        >
          <option value="">All Types</option>
          {Object.entries(deviceTypeLabels).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>

      {/* Device Grid */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 text-primary-600 animate-spin" />
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      ) : filteredDevices.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <Cpu className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">No devices found</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredDevices.map((device) => (
            <Link
              key={device.id}
              to={`/devices/${device.device_id}`}
              className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="p-2 bg-primary-50 rounded-lg">
                  <Cpu className="w-6 h-6 text-primary-600" />
                </div>
                <span
                  className={`px-2 py-1 text-xs font-medium rounded-full ${
                    device.status === 'online'
                      ? 'bg-green-100 text-green-700'
                      : device.status === 'offline'
                      ? 'bg-gray-100 text-gray-700'
                      : device.status === 'error'
                      ? 'bg-red-100 text-red-700'
                      : 'bg-yellow-100 text-yellow-700'
                  }`}
                >
                  {device.status}
                </span>
              </div>

              <h3 className="font-semibold text-gray-900 mb-1">{device.name}</h3>
              <p className="text-sm text-gray-500 mb-3">{device.device_id}</p>

              <div className="flex items-center gap-2">
                <span
                  className={`px-2 py-1 text-xs font-medium rounded-full ${
                    deviceTypeColors[device.device_type]
                  }`}
                >
                  {deviceTypeLabels[device.device_type]}
                </span>
                {device.location && (
                  <span className="text-xs text-gray-400">{device.location}</span>
                )}
              </div>

              {device.last_seen && (
                <p className="text-xs text-gray-400 mt-3">
                  Last seen: {new Date(device.last_seen).toLocaleString()}
                </p>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}