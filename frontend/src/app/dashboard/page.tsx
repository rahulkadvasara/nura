'use client'

import { useAuthStore } from '@/stores/auth'

export default function DashboardPage() {
  const { user } = useAuthStore()

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">
          Welcome back, {user?.full_name?.split(' ')[0] || 'User'}
        </h1>
        <p className="text-muted-foreground">
          Here is what&apos;s happening with your health profile today.
        </p>
      </div>

      <div className="flex h-[400px] shrink-0 items-center justify-center rounded-md border border-dashed border-slate-300">
        <div className="mx-auto flex max-w-[420px] flex-col items-center justify-center text-center">
          <h3 className="mt-4 text-lg font-semibold">Dashboard Coming Soon</h3>
          <p className="mb-4 mt-2 text-sm text-muted-foreground">
            The dashboard features for your {user?.role || 'patient'} account are currently under construction.
          </p>
        </div>
      </div>
    </div>
  )
}
