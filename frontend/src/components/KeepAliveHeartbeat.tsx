'use client'

import { useEffect, useRef } from 'react'
import { healthService } from '@/services/health'

// 9.5 minutes interval in milliseconds (Render free tier sleeps after 15 mins of inactivity)
const HEARTBEAT_INTERVAL_MS = 9.5 * 60 * 1000

export function KeepAliveHeartbeat() {
  const lastPingTimeRef = useRef<number>(Date.now())

  useEffect(() => {
    let isMounted = true

    const pingBackend = async () => {
      try {
        await healthService.checkHealth()
        lastPingTimeRef.current = Date.now()
      } catch (err) {
        // Silently ignore errors (e.g. backend initial spinning up or temporary network hiccup)
        console.debug('[KeepAlive] Heartbeat ping (backend may be spinning up):', err)
      }
    }

    // Ping immediately when the application mounts in browser
    pingBackend()

    // Periodically ping every 9.5 minutes to prevent Render free-tier sleep
    const intervalId = setInterval(() => {
      if (isMounted) {
        pingBackend()
      }
    }, HEARTBEAT_INTERVAL_MS)

    // Also ping if user returns to tab after being inactive for > 5 minutes
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        const elapsed = Date.now() - lastPingTimeRef.current
        if (elapsed > 5 * 60 * 1000) {
          pingBackend()
        }
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      isMounted = false
      clearInterval(intervalId)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [])

  return null
}
