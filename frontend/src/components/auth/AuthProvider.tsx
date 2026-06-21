'use client'

import { useEffect, useState } from 'react'
import { useAuthStore } from '@/stores/auth'
import { authService } from '@/services/auth.service'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { accessToken, setUser, logout } = useAuthStore()
  const [isInitializing, setIsInitializing] = useState(true)

  useEffect(() => {
    const initSession = async () => {
      // Use the raw token from localStorage as the source of truth for initialization
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null

      if (!token) {
        setIsInitializing(false)
        return
      }

      try {
        const response = await authService.getCurrentUser()
        if (response.success && response.data) {
          setUser(response.data)
        } else {
          // Token is invalid or expired
          logout()
        }
      } catch (error) {
        // Network error or 401/403 (which is caught by interceptor)
        logout()
      } finally {
        setIsInitializing(false)
      }
    }

    initSession()
  }, []) // Empty dependency array ensures this runs once on mount

  if (isInitializing) {
    return (
      <div className="fixed inset-0 bg-slate-50 flex items-center justify-center z-50">
        <div className="flex flex-col items-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          <p className="text-sm text-muted-foreground font-medium animate-pulse">Initializing securely...</p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
