'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Card, Metric, Badge, Button } from '@tremor/react'
import {
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  SignalIcon,
  FireIcon,
  CameraIcon
} from '@heroicons/react/24/outline'
import ThreatFeed from './threat-feed'
import AuthenticityMetrics from './metrics'
import KillSwitch from './kill-switch'
import FinOpsDashboard from './finops'

interface Stats {
  totalScans: number
  blockedTransactions: number
  avgResponseTime: number
  activeThreats: number
}

export default function SecurityCommandCenter() {
  const [isConnected, setIsConnected] = useState(false)
  const [stats, setStats] = useState<Stats>({
    totalScans: 0,
    blockedTransactions: 0,
    avgResponseTime: 0,
    activeThreats: 0
  })

  useEffect(() => {
    // Connect to WebSocket for real-time updates
    const ws = new WebSocket('ws://localhost:8000/ws/dashboard')
    let reconnectTimeout: NodeJS.Timeout

    ws.onopen = () => {
      console.log('WebSocket connected')
      setIsConnected(true)
    }
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setStats((prev: Stats) => ({ ...prev, ...data }))
      } catch (error) {
        console.error('Failed to parse WebSocket data:', error)
      }
    }
    ws.onerror = (event) => {
      console.error('WebSocket error:', event)
      setIsConnected(false)
    }
    ws.onclose = () => {
      console.log('WebSocket closed, attempting to reconnect in 3 seconds...')
      setIsConnected(false)
      // Attempt to reconnect after 3 seconds
      reconnectTimeout = setTimeout(() => {
        console.log('Reconnecting to WebSocket...')
        window.location.reload()
      }, 3000)
    }

    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout)
      if (ws.readyState === WebSocket.OPEN) ws.close()
    }
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header with Animated Background */}
        <div className="mb-8 relative">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl opacity-5 blur-3xl"></div>
          <div className="relative bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl shadow-lg">
                  <ShieldCheckIcon className="h-10 w-10 text-white" />
                </div>
                <div>
                  <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                    VeriShield AI
                  </h1>
                  <div className="text-gray-600 mt-1 flex items-center">
                    <SignalIcon className="h-4 w-4 mr-1" />
                    Real-time Deepfake Detection & Threat Response
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <Link href="/capture">
                  <Button className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-semibold px-4 py-2 rounded-lg transition-all duration-200 transform hover:scale-105 flex items-center space-x-2">
                    <CameraIcon className="h-4 w-4" />
                    <span>Test Capture</span>
                  </Button>
                </Link>
                <div className="flex items-center space-x-2">
                  <div className={`h-3 w-3 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'} shadow-lg`}></div>
                  <Badge color={isConnected ? 'green' : 'red'} size="lg" className="shadow-md">
                    {isConnected ? 'Live' : 'Disconnected'}
                  </Badge>
                </div>
                <KillSwitch />
              </div>
            </div>
          </div>
        </div>

        {/* Stats Grid with Enhanced Design */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-6 mb-8">
          {/* Total Scans */}
          <div className="group relative">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-400 to-blue-600 rounded-2xl opacity-75 group-hover:opacity-100 transition-opacity blur-xl"></div>
            <Card className="relative bg-white hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 border-0 rounded-2xl overflow-hidden">
              <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-blue-500/10 to-transparent rounded-bl-full"></div>
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-lg">
                    <ShieldCheckIcon className="h-6 w-6 text-white" />
                  </div>
                  <span className="text-xs font-semibold text-blue-600 bg-blue-50 px-3 py-1 rounded-full">+12.5%</span>
                </div>
                <div className="text-sm text-gray-600 font-medium">Total Scans</div>
                <Metric className="text-3xl font-bold text-gray-900 mt-2">
                  {stats.totalScans.toLocaleString()}
                </Metric>
              </div>
            </Card>
          </div>

          {/* Blocked Transactions */}
          <div className="group relative">
            <div className="absolute inset-0 bg-gradient-to-br from-red-400 to-red-600 rounded-2xl opacity-75 group-hover:opacity-100 transition-opacity blur-xl"></div>
            <Card className="relative bg-white hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 border-0 rounded-2xl overflow-hidden">
              <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-red-500/10 to-transparent rounded-bl-full"></div>
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 bg-gradient-to-br from-red-500 to-red-600 rounded-xl shadow-lg">
                    <ExclamationTriangleIcon className="h-6 w-6 text-white" />
                  </div>
                  <span className="text-xs font-semibold text-red-600 bg-red-50 px-3 py-1 rounded-full">Critical</span>
                </div>
                <div className="text-sm text-gray-600 font-medium">Blocked Threats</div>
                <Metric className="text-3xl font-bold text-gray-900 mt-2">
                  {stats.blockedTransactions}
                </Metric>
              </div>
            </Card>
          </div>

          {/* Avg Response Time */}
          <div className="group relative">
            <div className="absolute inset-0 bg-gradient-to-br from-green-400 to-emerald-600 rounded-2xl opacity-75 group-hover:opacity-100 transition-opacity blur-xl"></div>
            <Card className="relative bg-white hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 border-0 rounded-2xl overflow-hidden">
              <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-green-500/10 to-transparent rounded-bl-full"></div>
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl shadow-lg">
                    <ClockIcon className="h-6 w-6 text-white" />
                  </div>
                  <span className="text-xs font-semibold text-green-600 bg-green-50 px-3 py-1 rounded-full">Optimal</span>
                </div>
                <div className="text-sm text-gray-600 font-medium">Response Time</div>
                <Metric className="text-3xl font-bold text-gray-900 mt-2">
                  {stats.avgResponseTime}<span className="text-lg text-gray-500">ms</span>
                </Metric>
              </div>
            </Card>
          </div>

          {/* Active Threats */}
          <div className="group relative">
            <div className="absolute inset-0 bg-gradient-to-br from-amber-400 to-orange-600 rounded-2xl opacity-75 group-hover:opacity-100 transition-opacity blur-xl"></div>
            <Card className="relative bg-white hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 border-0 rounded-2xl overflow-hidden">
              <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-amber-500/10 to-transparent rounded-bl-full"></div>
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl shadow-lg animate-pulse">
                    <FireIcon className="h-6 w-6 text-white" />
                  </div>
                  <span className="text-xs font-semibold text-amber-600 bg-amber-50 px-3 py-1 rounded-full">Active</span>
                </div>
                <div className="text-sm text-gray-600 font-medium">Active Threats</div>
                <Metric className="text-3xl font-bold text-gray-900 mt-2">
                  {stats.activeThreats}
                </Metric>
              </div>
            </Card>
          </div>

          {/* PII Redactions */}
          <div className="group relative">
            <div className="absolute inset-0 bg-gradient-to-br from-purple-400 to-pink-600 rounded-2xl opacity-75 group-hover:opacity-100 transition-opacity blur-xl"></div>
            <Card className="relative bg-white hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 border-0 rounded-2xl overflow-hidden">
              <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-purple-500/10 to-transparent rounded-bl-full"></div>
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl shadow-lg">
                    <ShieldCheckIcon className="h-6 w-6 text-white" />
                  </div>
                  <span className="text-xs font-semibold text-purple-600 bg-purple-50 px-3 py-1 rounded-full">Privacy</span>
                </div>
                <div className="text-sm text-gray-600 font-medium">PII Redactions</div>
                <Metric className="text-3xl font-bold text-gray-900 mt-2">
                  1,247
                </Metric>
              </div>
            </Card>
          </div>

          {/* Content Safety */}
          <div className="group relative">
            <div className="absolute inset-0 bg-gradient-to-br from-teal-400 to-cyan-600 rounded-2xl opacity-75 group-hover:opacity-100 transition-opacity blur-xl"></div>
            <Card className="relative bg-white hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 border-0 rounded-2xl overflow-hidden">
              <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-teal-500/10 to-transparent rounded-bl-full"></div>
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 bg-gradient-to-br from-teal-500 to-cyan-600 rounded-xl shadow-lg">
                    <ShieldCheckIcon className="h-6 w-6 text-white" />
                  </div>
                  <span className="text-xs font-semibold text-teal-600 bg-teal-50 px-3 py-1 rounded-full">Safe</span>
                </div>
                <div className="text-sm text-gray-600 font-medium">Content Filtered</div>
                <Metric className="text-3xl font-bold text-gray-900 mt-2">
                  89
                </Metric>
              </div>
            </Card>
          </div>
        </div>

        {/* Main Content with Enhanced Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Threat Feed */}
          <div className="lg:col-span-2">
            <ThreatFeed />
          </div>

          {/* Authenticity Metrics */}
          <div>
            <AuthenticityMetrics />
          </div>
        </div>

        {/* FinOps Dashboard */}
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 p-6">
          <FinOpsDashboard />
        </div>
      </div>
    </div>
  )
}