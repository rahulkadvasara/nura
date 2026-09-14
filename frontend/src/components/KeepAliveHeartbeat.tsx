'use client'

import { useEffect, useRef } from 'react'
import { healthService } from '@/services/health'

// 9 minutes interval in milliseconds (Render free tier sleeps after 15 mins of inactivity)
const HEARTBEAT_INTERVAL_MS = 9 * 60 * 1000

export function KeepAliveHeartbeat() {
  const lastPingTimeRef = useRef<number>(Date.now())
  const isPingingRef = useRef<boolean>(false)

  useEffect(() => {
    let isMounted = true

    const pingBackendWithRetry = async (maxRetries = 6, delayMs = 5000) => {
      if (isPingingRef.current) return
      isPingingRef.current = true

      for (let attempt = 1; attempt <= maxRetries; attempt++) {
        if (!isMounted) break
        try {
          // Use 60 second timeout per health ping attempt
          await healthService.checkHealth(60000)
          lastPingTimeRef.current = Date.now()
          console.debug('[KeepAlive] Backend is healthy and active')
          break // Success - backend is awake
        } catch (err) {
          console.debug(`[KeepAlive] Ping attempt ${attempt}/${maxRetries} failed (backend may be spinning up):`, err)
          if (attempt < maxRetries && isMounted) {
            await new Promise((resolve) => setTimeout(resolve, delayMs))
          }
        }
      }

      isPingingRef.current = false
    }

    // Ping immediately with retries when the application mounts in browser
    pingBackendWithRetry(6, 5000)

    // Periodically ping every 9 minutes to prevent Render free-tier sleep
    const intervalId = setInterval(() => {
      if (isMounted) {
        pingBackendWithRetry(3, 5000)
      }
    }, HEARTBEAT_INTERVAL_MS)

    // Also ping if user returns to tab after being inactive for > 5 minutes
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        const elapsed = Date.now() - lastPingTimeRef.current
        if (elapsed > 5 * 60 * 1000) {
          pingBackendWithRetry(3, 5000)
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

