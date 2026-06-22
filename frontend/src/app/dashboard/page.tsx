'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/stores/auth'
import { usePatientDashboard } from '@/hooks/use-dashboard'
import { Button } from '@/components/ui/button'
import { RefreshCw } from 'lucide-react'
import {
  StatCards,
  QuickActions,
  AppointmentsList,
  MedicationsList,
  RecentReports,
  HealthInsights,
} from '@/components/dashboard'

function getGreeting(): string {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 17) return 'Good afternoon'
  return 'Good evening'
}

function PatientDashboard() {
  const { user } = useAuthStore()
  const { data, isLoading, isError, error, refetch } = usePatientDashboard()
  const firstName = user?.full_name?.split(' ')[0] || 'there'

  if (isLoading) {
    return (
      <div className="space-y-6">
        {/* Greeting skeleton */}
        <div className="space-y-2">
          <div className="h-8 w-64 bg-slate-200 rounded-md animate-pulse" />
          <div className="h-5 w-96 bg-slate-100 rounded-md animate-pulse" />
        </div>

        {/* Stat cards skeleton */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="h-[120px] bg-white border border-slate-200 rounded-lg animate-pulse"
            />
          ))}
        </div>

        {/* Quick actions skeleton */}
        <div className="h-[140px] bg-white border border-slate-200 rounded-lg animate-pulse" />

        {/* Two column skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="h-[280px] bg-white border border-slate-200 rounded-lg animate-pulse" />
          <div className="h-[280px] bg-white border border-slate-200 rounded-lg animate-pulse" />
        </div>

        {/* Bottom row skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="h-[280px] bg-white border border-slate-200 rounded-lg animate-pulse" />
          <div className="h-[280px] bg-white border border-slate-200 rounded-lg animate-pulse" />
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            {getGreeting()}, {firstName}
          </h1>
        </div>
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="p-4 rounded-full bg-red-50 mb-4">
            <RefreshCw className="h-6 w-6 text-red-400" />
          </div>
          <h3 className="text-lg font-semibold text-slate-800 mb-1">
            Unable to load your dashboard
          </h3>
          <p className="text-sm text-slate-500 mb-5 max-w-md">
            {(error as Error)?.message || 'Something went wrong while fetching your health data. Please try again.'}
          </p>
          <Button
            onClick={() => refetch()}
            variant="outline"
            className="border-slate-300"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="space-y-6">
      {/* Greeting */}
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">
          {getGreeting()}, {firstName}
        </h1>
        <p className="text-slate-500">
          Here&apos;s an overview of your health. Nura is here to help.
        </p>
      </div>

      {/* Stat Cards */}
      <StatCards data={data} />

      {/* Quick Actions */}
      <QuickActions />

      {/* Appointments + Medications */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <AppointmentsList count={data.upcoming_appointments_count} />
        <MedicationsList />
      </div>

      {/* Reports + Health Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <RecentReports count={data.reports_count} />
        <HealthInsights insights={data.recent_health_insights} />
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const router = useRouter()
  const { user, isLoading: authLoading } = useAuthStore()
  const role = user?.role || 'patient'

  useEffect(() => {
    if (!authLoading && role === 'doctor') {
      router.replace('/dashboard/doctor')
    }
  }, [role, authLoading, router])

  if (authLoading || role === 'doctor') {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
      </div>
    )
  }

  // Only patients get the full dashboard; doctor/admin see a placeholder for now
  if (role === 'patient') {
    return <PatientDashboard />
  }

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
