'use client'

import { useState } from 'react'
import { Button } from '@tremor/react'
import { ExclamationTriangleIcon, ShieldCheckIcon } from '@heroicons/react/24/outline'

export default function KillSwitch() {
  const [isActive, setIsActive] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleToggle = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/kill-switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ active: !isActive })
      })

      if (response.ok) {
        setIsActive(!isActive)
      }
    } catch (error) {
      console.error('Failed to toggle kill switch:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative group">
      {isActive && (
        <div className="absolute -inset-1 bg-gradient-to-r from-red-500 to-red-600 rounded-xl blur opacity-75 group-hover:opacity-100 transition duration-200 animate-pulse"></div>
      )}
      <Button
        onClick={handleToggle}
        disabled={loading}
        className={`relative flex items-center gap-2 px-6 py-3 rounded-xl font-bold transition-all duration-300 transform hover:scale-105 shadow-lg ${
          isActive 
            ? 'bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white border-0' 
            : 'bg-gradient-to-r from-gray-700 to-gray-800 hover:from-gray-800 hover:to-gray-900 text-white border-0'
        }`}
      >
        {isActive ? (
          <>
            <ExclamationTriangleIcon className="h-5 w-5 animate-pulse" />
            <span>Emergency Kill Switch</span>
            <div className="absolute top-0 right-0 -mt-1 -mr-1">
              <span className="flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
              </span>
            </div>
          </>
        ) : (
          <>
            <ShieldCheckIcon className="h-5 w-5" />
            <span>Activate Protection</span>
          </>
        )}
      </Button>
    </div>
  )
}
