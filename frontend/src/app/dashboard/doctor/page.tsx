'use client'

import { useAuthStore } from '@/stores/auth'
import { useDoctorDashboard } from '@/hooks/use-dashboard'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { Button } from '@/components/ui/button'
import { RefreshCw } from 'lucide-react'
import {
  DoctorStatCards,
  EarningsCard,
  AppointmentOverviewCard,
  PatientOverviewCard,
  VerificationStatusCard,
  DoctorQuickActions,
} from '@/components/doctor-dashboard'

function getGreeting(): string {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 17) return 'Good afternoon'
  return 'Good evening'
}

function DoctorDashboardContent() {
  const { user } = useAuthStore()
  const { data, isLoading, isError, error, refetch } = useDoctorDashboard()
  
  // Format name to prefix with Dr.
  const rawName = user?.full_name || 'Doctor'
  const doctorName = rawName.toLowerCase().startsWith('dr.') ? rawName : `Dr. ${rawName}`

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        {/* Greeting skeleton */}
        <div className="space-y-2">
          <div className="h-8 w-64 bg-slate-200 rounded-md" />
          <div className="h-5 w-96 bg-slate-100 rounded-md" />
        </div>

        {/* Stat cards skeleton */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="h-[120px] bg-white border border-slate-200 rounded-lg"
            />
          ))}
        </div>

        {/* Quick actions skeleton */}
        <div className="h-[140px] bg-white border border-slate-200 rounded-lg" />

        {/* Two column layout skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-6 h-[320px]">
            <div className="bg-white border border-slate-200 rounded-lg" />
            <div className="bg-white border border-slate-200 rounded-lg" />
          </div>
          <div className="space-y-6">
            <div className="h-[220px] bg-white border border-slate-200 rounded-lg" />
            <div className="h-[160px] bg-white border border-slate-200 rounded-lg" />
          </div>
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            {getGreeting()}, {doctorName}
          </h1>
        </div>
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="p-4 rounded-full bg-red-50 mb-4">
            <RefreshCw className="h-6 w-6 text-red-400" />
          </div>
          <h3 className="text-lg font-semibold text-slate-800 mb-1">
            Unable to load practice metrics
          </h3>
          <p className="text-sm text-slate-500 mb-5 max-w-md">
            {(error as Error)?.message || 'Something went wrong while fetching your dashboard data. Please try again.'}
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
          {getGreeting()}, {doctorName}
        </h1>
        <p className="text-slate-500">
          Here is an overview of your medical practice today.
        </p>
      </div>

      {/* Stat Cards */}
      <DoctorStatCards data={data} />

      {/* Quick Actions */}
      <DoctorQuickActions />

      {/* Two Column Layout: Main Widgets */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Side: Appointment & Patient overview cards */}
        <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-6">
          <AppointmentOverviewCard 
            todaysCount={data.todays_appointments_count} 
            upcomingCount={data.upcoming_appointments_count} 
          />
          <PatientOverviewCard count={data.total_patients_count} />
        </div>

        {/* Right Side: Wallet details & Verification details */}
        <div className="space-y-6">
          <EarningsCard 
            walletBalance={data.wallet_balance} 
            totalEarnings={data.total_earnings}
            pendingBalance={data.pending_balance}
          />
          <VerificationStatusCard 
            profileStatus={data.profile_status} 
            documentStatus={data.document_status} 
          />
        </div>
      </div>
    </div>
  )
}

export default function DoctorDashboardPage() {
  return (
    <ProtectedRoute allowedRoles={['doctor']}>
      <DoctorDashboardContent />
    </ProtectedRoute>
  )
}
