'use client'

import { useState, useEffect } from 'react'
import { Card, Title } from '@tremor/react'
import { 
  ExclamationTriangleIcon,
  ShieldExclamationIcon,
  FireIcon,
  CheckCircleIcon 
} from '@heroicons/react/24/outline'

interface Threat {
  id: string
  type: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  description: string
  timestamp: string
}

export default function ThreatFeed() {
  const [threats, setThreats] = useState<Threat[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchThreats = async () => {
      try {
        const response = await fetch('/api/threats')
        const data = await response.json()
        setThreats(data)
      } catch (error) {
        console.error('Failed to fetch threats:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchThreats()
  }, [])

  const getSeverityConfig = (severity: string) => {
    switch (severity) {
      case 'critical':
        return {
          color: 'from-red-500 to-red-600',
          bg: 'bg-red-50',
          border: 'border-red-500',
          text: 'text-red-700',
          icon: FireIcon
        }
      case 'high':
        return {
          color: 'from-orange-500 to-orange-600',
          bg: 'bg-orange-50',
          border: 'border-orange-500',
          text: 'text-orange-700',
          icon: ExclamationTriangleIcon
        }
      case 'medium':
        return {
          color: 'from-yellow-500 to-yellow-600',
          bg: 'bg-yellow-50',
          border: 'border-yellow-500',
          text: 'text-yellow-700',
          icon: ShieldExclamationIcon
        }
      default:
        return {
          color: 'from-green-500 to-green-600',
          bg: 'bg-green-50',
          border: 'border-green-500',
          text: 'text-green-700',
          icon: CheckCircleIcon
        }
    }
  }

  return (
    <Card className="bg-white shadow-xl rounded-2xl border-0 overflow-hidden">
      <div className="bg-gradient-to-r from-slate-800 to-slate-900 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-white/10 rounded-lg backdrop-blur-sm">
              <ShieldExclamationIcon className="h-6 w-6 text-white" />
            </div>
            <Title className="text-white text-2xl font-bold">Threat Feed</Title>
          </div>
          <div className="flex items-center space-x-2">
            <div className="h-2 w-2 bg-red-500 rounded-full animate-pulse"></div>
            <div className="text-white/80 text-sm">Live Monitoring</div>
          </div>
        </div>
      </div>
      
      <div className="p-6">
        <div className="space-y-4 max-h-[600px] overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : threats.length === 0 ? (
            <div className="text-center py-12">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
                <CheckCircleIcon className="h-8 w-8 text-green-600" />
              </div>
              <div className="text-green-600 font-semibold text-lg">All Clear!</div>
              <div className="text-gray-500 mt-2">No active threats detected</div>
            </div>
          ) : (
            threats.map((threat) => {
              const config = getSeverityConfig(threat.severity)
              const ThreatIcon = config.icon
              
              return (
                <div 
                  key={threat.id} 
                  className={`group relative bg-white border-l-4 ${config.border} rounded-lg shadow-md hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 overflow-hidden`}
                >
                  <div className={`absolute inset-0 bg-gradient-to-r ${config.color} opacity-0 group-hover:opacity-5 transition-opacity`}></div>
                  <div className="relative p-4">
                    <div className="flex items-start space-x-4">
                      <div className={`p-3 bg-gradient-to-br ${config.color} rounded-xl shadow-lg flex-shrink-0`}>
                        <ThreatIcon className="h-5 w-5 text-white" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between mb-2">
                          <div className="font-bold text-gray-900 text-lg">{threat.type}</div>
                          <span className={`px-3 py-1 text-xs font-bold text-white rounded-full bg-gradient-to-r ${config.color} shadow-md uppercase tracking-wide`}>
                            {threat.severity}
                          </span>
                        </div>
                        <div className="text-gray-600 mb-3">{threat.description}</div>
                        <div className="flex items-center space-x-4 text-xs text-gray-500">
                          <span className="flex items-center">
                            <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            {threat.timestamp}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })
          )}
        </div>
      </div>
    </Card>
  )
}
