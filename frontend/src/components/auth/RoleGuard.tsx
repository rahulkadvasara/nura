'use client'

import { useAuthStore } from '@/stores/auth'

interface RoleGuardProps {
  children: React.ReactNode
  allowedRoles: string[]
  fallback?: React.ReactNode
}

export function RoleGuard({ children, allowedRoles, fallback = null }: RoleGuardProps) {
  const { user, isAuthenticated, isLoading } = useAuthStore()

  if (isLoading) {
    return null
  }

  if (!isAuthenticated || !user) {
    return <>{fallback}</>
  }

  if (!allowedRoles.includes(user.role)) {
    return <>{fallback}</>
  }

  return <>{children}</>
}
