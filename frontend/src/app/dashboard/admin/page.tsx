'use client'

import { useAuthStore } from '@/stores/auth'
import { useAdminDashboard } from '@/hooks/use-dashboard'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { RefreshCw, Shield } from 'lucide-react'
import { useDrugDashboardStatistics } from '@/hooks/use-ai'
import {
  UserMetricsCard,
  RevenueOverviewCard,
  VerificationOverviewCard,
  ActivityOverviewCard,
  AdminQuickActions,
  PendingReviewsSection,
} from '@/components/admin-dashboard'

function getGreeting(): string {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 17) return 'Good afternoon'
  return 'Good evening'
}

function AdminDashboardContent() {
  const { user } = useAuthStore()
  const { data, isLoading, isError, error, refetch } = useAdminDashboard()
  const { data: drugStats, isLoading: drugStatsLoading } = useDrugDashboardStatistics()
  const adminName = user?.full_name?.split(' ')[0] || 'Admin'

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        {/* Greeting skeleton */}
        <div className="space-y-2">
          <div className="h-8 w-64 bg-slate-200 rounded-md" />
          <div className="h-5 w-96 bg-slate-100 rounded-md" />
        </div>

        {/* Widgets skeleton grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="h-[200px] bg-white border border-slate-200 rounded-lg" />
            <div className="h-[280px] bg-white border border-slate-200 rounded-lg" />
            <div className="h-[140px] bg-white border border-slate-200 rounded-lg" />
          </div>
          <div className="space-y-6">
            <div className="h-[220px] bg-white border border-slate-200 rounded-lg" />
            <div className="h-[220px] bg-white border border-slate-200 rounded-lg" />
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
            {getGreeting()}, {adminName}
          </h1>
        </div>
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="p-4 rounded-full bg-red-50 mb-4">
            <RefreshCw className="h-6 w-6 text-red-400" />
          </div>
          <h3 className="text-lg font-semibold text-slate-800 mb-1">
            Unable to load administration console
          </h3>
          <p className="text-sm text-slate-500 mb-5 max-w-md">
            {(error as Error)?.message || 'Something went wrong while fetching platform aggregation data. Please try again.'}
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
          {getGreeting()}, {adminName}
        </h1>
        <p className="text-slate-500">
          Here is an overview of the Nura platform performance and logs today.
        </p>
      </div>

      {/* 3-Column Layout: Main Dashboard Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Side (col-span-2): User Metrics, Usage Activity, and Quick Actions */}
        <div className="lg:col-span-2 space-y-6">
          <UserMetricsCard 
            totalUsers={data.total_users_count} 
            totalPatients={data.total_patients_count} 
            totalDoctors={data.total_doctors_count} 
          />
          <ActivityOverviewCard 
            appointmentsCount={data.total_appointments_count} 
            consultationsCount={data.active_consultations_count} 
            reportsCount={data.reports_count} 
            remindersCount={data.reminders_count} 
            chatsCount={data.active_chats_count} 
          />
          <PendingReviewsSection />
          <AdminQuickActions />
        </div>

        {/* Right Side (col-span-1): Revenue metrics & Verification approvals overview */}
        <div className="space-y-6">
          <RevenueOverviewCard 
            totalRevenue={data.total_revenue} 
            platformEarnings={data.platform_earnings} 
          />
          <VerificationOverviewCard 
            pendingCount={data.pending_doctor_verifications_count} 
            verifiedCount={data.verified_doctors_count} 
          />

          {/* Drug Safety Monitoring Card */}
          <Card className="border border-slate-200 shadow-sm bg-white p-5 rounded-lg space-y-4">
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              <Shield className="h-4 w-4 text-teal-600 animate-pulse" />
              Drug Safety Monitoring
            </h3>
            {drugStatsLoading ? (
              <div className="flex items-center justify-center py-4">
                <RefreshCw className="h-5 w-5 animate-spin text-teal-600" />
              </div>
            ) : drugStats ? (
              <div className="space-y-3.5 text-xs">
                <div className="flex justify-between border-b pb-1.5">
                  <span className="text-slate-500 font-semibold">Total Checks</span>
                  <strong className="text-slate-800 font-extrabold">{drugStats.validations || 0} runs</strong>
                </div>
                <div className="flex justify-between border-b pb-1.5">
                  <span className="text-slate-500 font-semibold">Active Warnings</span>
                  <strong className="text-amber-600 font-extrabold">{drugStats.active_warnings || 0}</strong>
                </div>
                <div className="flex justify-between border-b pb-1.5">
                  <span className="text-slate-500 font-semibold">Blocked Interactions</span>
                  <strong className="text-rose-600 font-extrabold">{drugStats.blocked_interactions || 0}</strong>
                </div>
                <div className="flex justify-between border-b pb-1.5">
                  <span className="text-slate-500 font-semibold">Physician Overrides</span>
                  <strong className="text-blue-600 font-extrabold">{drugStats.overrides || 0}</strong>
                </div>
                <div className="flex justify-between pb-0">
                  <span className="text-slate-500 font-semibold">Avg Check Latency</span>
                  <strong className="text-slate-800 font-extrabold">{drugStats.avg_latency_ms?.toFixed(1) || '0.0'} ms</strong>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">No drug validation statistics available.</p>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}

export default function AdminDashboardPage() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <AdminDashboardContent />
    </ProtectedRoute>
  )
}
