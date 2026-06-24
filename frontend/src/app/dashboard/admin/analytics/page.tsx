'use client'

import { useState, useEffect } from 'react'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { adminAnalyticsService } from '@/services/admin-analytics.service'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { toast } from 'react-hot-toast'
import {
  Users,
  TrendingUp,
  IndianRupee,
  Calendar,
  Sparkles,
  Award,
  Power,
  Shield,
  Activity,
  FileText,
  Clock,
  Loader2,
  Stethoscope,
  Pill,
} from 'lucide-react'
import { AdminAnalyticsData, DailyGrowthItem, DailyRevenueItem } from '@/types'

export default function AdminAnalyticsPage() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <AdminAnalyticsContent />
    </ProtectedRoute>
  )
}

function AdminAnalyticsContent() {
  const [data, setData] = useState<AdminAnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [userPeriod, setUserPeriod] = useState<'7d' | '30d'>('7d')
  const [appointmentPeriod, setAppointmentPeriod] = useState<'7d' | '30d'>('7d')
  const [revenuePeriod, setRevenuePeriod] = useState<'7d' | '30d'>('7d')

  const fetchAnalytics = async () => {
    try {
      setLoading(true)
      const res = await adminAnalyticsService.getAnalytics()
      if (res.success && res.data) {
        setData(res.data)
      } else {
        toast.error(res.message || 'Failed to retrieve analytics data')
      }
    } catch (err) {
      console.error(err)
      toast.error('An error occurred while fetching platform analytics')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAnalytics()
  }, [])

  const formatINR = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(val)
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px] gap-3">
        <Loader2 className="h-10 w-10 animate-spin text-teal-600" />
        <p className="text-sm text-slate-500 font-medium">Aggregating real-time database metrics...</p>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="text-center py-16 text-slate-400">
        <Shield className="h-12 w-12 mx-auto mb-3 text-slate-300 animate-pulse" />
        <p className="text-sm font-semibold text-slate-800">No Analytics Available</p>
        <p className="text-xs text-slate-400 mt-1 max-w-[200px] mx-auto">
          Please verify connection database and indexes setup.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Platform Analytics</h1>
          <p className="mt-2 text-sm text-slate-500">
            Real-time calculations and aggregates directly sourced from operational database records.
          </p>
        </div>
        <Button onClick={fetchAnalytics} variant="outline" className="border-slate-200">
          Refresh Data
        </Button>
      </div>

      {/* Platform Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <Card className="border-slate-200 shadow-sm hover:shadow-md transition-all duration-200 bg-gradient-to-br from-white to-slate-50">
          <CardContent className="p-6 flex items-center justify-between">
            <div>
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Users</p>
              <h3 className="text-3xl font-extrabold text-slate-900 mt-2">{data.users.total_users}</h3>
              <p className="text-xs text-slate-500 mt-1">Patients, Doctors, Admins</p>
            </div>
            <div className="h-12 w-12 rounded-2xl bg-teal-50 flex items-center justify-center text-teal-600 border border-teal-100">
              <Users className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm hover:shadow-md transition-all duration-200 bg-gradient-to-br from-white to-slate-50">
          <CardContent className="p-6 flex items-center justify-between">
            <div>
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Doctors</p>
              <h3 className="text-3xl font-extrabold text-slate-900 mt-2">{data.doctors.total_doctors}</h3>
              <p className="text-xs text-slate-500 mt-1">Verified & onboarding</p>
            </div>
            <div className="h-12 w-12 rounded-2xl bg-blue-50 flex items-center justify-center text-blue-600 border border-blue-100">
              <Award className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm hover:shadow-md transition-all duration-200 bg-gradient-to-br from-white to-slate-50">
          <CardContent className="p-6 flex items-center justify-between">
            <div>
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Appointments</p>
              <h3 className="text-3xl font-extrabold text-slate-900 mt-2">{data.appointments.total_appointments}</h3>
              <p className="text-xs text-slate-500 mt-1">Platform bookings</p>
            </div>
            <div className="h-12 w-12 rounded-2xl bg-indigo-50 flex items-center justify-center text-indigo-600 border border-indigo-100">
              <Calendar className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm hover:shadow-md transition-all duration-200 bg-gradient-to-br from-white to-slate-50">
          <CardContent className="p-6 flex items-center justify-between">
            <div>
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Revenue</p>
              <h3 className="text-3xl font-extrabold text-slate-900 mt-2">{formatINR(data.revenue.total_revenue)}</h3>
              <p className="text-xs text-slate-500 mt-1">Cleansed gateway checkout</p>
            </div>
            <div className="h-12 w-12 rounded-2xl bg-emerald-50 flex items-center justify-center text-emerald-600 border border-emerald-100">
              <IndianRupee className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* User Growth & Distribution */}
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between border-b pb-4 flex-wrap gap-2">
            <div>
              <CardTitle className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <Users className="h-5 w-5 text-teal-600" />
                User base growth
              </CardTitle>
              <CardDescription className="text-xs">Cumulative user counts over time</CardDescription>
            </div>
            <div className="flex gap-1 bg-slate-100 p-0.5 rounded-md">
              <button
                onClick={() => setUserPeriod('7d')}
                className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors ${
                  userPeriod === '7d' ? 'bg-white text-teal-600 shadow-sm' : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                7 Days
              </button>
              <button
                onClick={() => setUserPeriod('30d')}
                className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors ${
                  userPeriod === '30d' ? 'bg-white text-teal-600 shadow-sm' : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                30 Days
              </button>
            </div>
          </CardHeader>
          <CardContent className="p-6 space-y-6">
            {/* SVG Line Chart */}
            <div className="h-64 w-full bg-slate-50/50 rounded-xl p-2 border border-slate-100">
              <UserGrowthChart
                dataList={userPeriod === '7d' ? data.users.users_last_7_days : data.users.users_last_30_days}
                totalCount={data.users.total_users}
              />
            </div>

            {/* Distribution metrics */}
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                <p className="text-xs font-bold text-slate-400">PATIENTS</p>
                <p className="text-xl font-bold text-slate-800 mt-1">{data.users.patients_count}</p>
              </div>
              <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                <p className="text-xs font-bold text-slate-400">DOCTORS</p>
                <p className="text-xl font-bold text-slate-800 mt-1">{data.users.doctors_count}</p>
              </div>
              <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                <p className="text-xs font-bold text-slate-400">ADMINS</p>
                <p className="text-xl font-bold text-slate-800 mt-1">{data.users.admins_count}</p>
              </div>
            </div>

            <div className="flex justify-between text-sm border-t pt-4">
              <span className="text-slate-500 font-medium">Account Status</span>
              <span className="font-semibold text-slate-800">
                {data.users.active_users} Active / {data.users.inactive_users} Inactive
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Appointment Trends */}
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between border-b pb-4 flex-wrap gap-2">
            <div>
              <CardTitle className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <Calendar className="h-5 w-5 text-indigo-600" />
                Appointment Trends
              </CardTitle>
              <CardDescription className="text-xs">Daily bookings volume charts</CardDescription>
            </div>
            <div className="flex gap-1 bg-slate-100 p-0.5 rounded-md">
              <button
                onClick={() => setAppointmentPeriod('7d')}
                className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors ${
                  appointmentPeriod === '7d' ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                7 Days
              </button>
              <button
                onClick={() => setAppointmentPeriod('30d')}
                className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors ${
                  appointmentPeriod === '30d' ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                30 Days
              </button>
            </div>
          </CardHeader>
          <CardContent className="p-6 space-y-6">
            {/* SVG Bar Chart */}
            <div className="h-64 w-full bg-slate-50/50 rounded-xl p-2 border border-slate-100">
              <AppointmentTrendsChart
                dataList={appointmentPeriod === '7d' ? data.appointments.appointments_last_7_days : data.appointments.appointments_last_30_days}
              />
            </div>

            {/* Distribution metrics */}
            <div className="grid grid-cols-3 gap-2 text-center text-xs">
              <div className="bg-slate-50 p-2 rounded border border-slate-100">
                <p className="font-semibold text-slate-500">PENDING</p>
                <p className="font-bold text-slate-800 mt-1">{data.appointments.pending_appointments}</p>
              </div>
              <div className="bg-slate-50 p-2 rounded border border-slate-100">
                <p className="font-semibold text-slate-500">APPROVED</p>
                <p className="font-bold text-slate-800 mt-1">{data.appointments.approved_appointments}</p>
              </div>
              <div className="bg-slate-50 p-2 rounded border border-slate-100">
                <p className="font-semibold text-slate-500">COMPLETED</p>
                <p className="font-bold text-slate-800 mt-1">{data.appointments.completed_appointments}</p>
              </div>
              <div className="bg-slate-50 p-2 rounded border border-slate-100">
                <p className="font-semibold text-slate-500">CANCELLED</p>
                <p className="font-bold text-slate-800 mt-1">{data.appointments.cancelled_appointments}</p>
              </div>
              <div className="bg-slate-50 p-2 rounded border border-slate-100">
                <p className="font-semibold text-slate-500">REJECTED</p>
                <p className="font-bold text-slate-800 mt-1">{data.appointments.rejected_appointments}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Doctor Analytics */}
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="border-b pb-4">
            <CardTitle className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Award className="h-5 w-5 text-blue-600" />
              Doctor Analytics
            </CardTitle>
            <CardDescription className="text-xs">Professional metrics & onboarding</CardDescription>
          </CardHeader>
          <CardContent className="p-6 space-y-4">
            <div className="space-y-3">
              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-500 font-medium">Verified Profile</span>
                <span className="font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100">
                  {data.doctors.verified_doctors}
                </span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-500 font-medium">Pending Review</span>
                <span className="font-semibold text-amber-600 bg-amber-50 px-2 py-0.5 rounded border border-amber-100">
                  {data.doctors.pending_doctors}
                </span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-500 font-medium">Rejected Application</span>
                <span className="font-semibold text-slate-600 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
                  {data.doctors.rejected_doctors}
                </span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-500 font-medium">Suspended Practitioner</span>
                <span className="font-semibold text-rose-600 bg-rose-50 px-2 py-0.5 rounded border border-rose-100 animate-pulse">
                  {data.doctors.suspended_doctors}
                </span>
              </div>
            </div>

            <div className="border-t pt-4 space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">Doctors with Availability:</span>
                <span className="font-bold text-slate-800">{data.doctors.doctors_with_availability}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Active Doctor Accounts:</span>
                <span className="font-bold text-slate-800">{data.doctors.active_doctors}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Revenue splits */}
        <Card className="border-slate-200 shadow-sm lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between border-b pb-4 flex-wrap gap-2">
            <div>
              <CardTitle className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <IndianRupee className="h-5 w-5 text-emerald-600" />
                Revenue Analytics
              </CardTitle>
              <CardDescription className="text-xs">Cleansed platform and provider share trends</CardDescription>
            </div>
            <div className="flex gap-1 bg-slate-100 p-0.5 rounded-md">
              <button
                onClick={() => setRevenuePeriod('7d')}
                className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors ${
                  revenuePeriod === '7d' ? 'bg-white text-emerald-600 shadow-sm' : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                7 Days
              </button>
              <button
                onClick={() => setRevenuePeriod('30d')}
                className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors ${
                  revenuePeriod === '30d' ? 'bg-white text-emerald-600 shadow-sm' : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                30 Days
              </button>
            </div>
          </CardHeader>
          <CardContent className="p-6 space-y-6">
            {/* SVG Line Chart */}
            <div className="h-60 w-full bg-slate-50/50 rounded-xl p-2 border border-slate-100">
              <RevenueTrendsChart
                dataList={revenuePeriod === '7d' ? data.revenue.revenue_last_7_days : data.revenue.revenue_last_30_days}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 text-center">
                <p className="text-xs font-bold text-slate-400 uppercase">Doctor Earnings (85%)</p>
                <p className="text-2xl font-black text-slate-850 mt-1">{formatINR(data.revenue.doctor_earnings)}</p>
              </div>
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 text-center">
                <p className="text-xs font-bold text-slate-400 uppercase">Platform Revenue (15%)</p>
                <p className="text-2xl font-black text-teal-700 mt-1">{formatINR(data.revenue.platform_revenue)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Healthcare Activity */}
      <Card className="border-slate-200 shadow-sm">
        <CardHeader className="border-b pb-4">
          <CardTitle className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <Activity className="h-5 w-5 text-indigo-650" />
            Healthcare Operations Activity
          </CardTitle>
          <CardDescription className="text-xs">Summarized upload and coordination events</CardDescription>
        </CardHeader>
        <CardContent className="p-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="flex items-center gap-4 bg-slate-50 p-4 rounded-xl border border-slate-100">
              <div className="h-10 w-10 bg-indigo-50 rounded-lg text-indigo-600 flex items-center justify-center">
                <FileText className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs font-bold text-slate-400 uppercase">Reports Uploaded</p>
                <p className="text-2xl font-bold text-slate-900">{data.healthcare.reports_uploaded}</p>
              </div>
            </div>

            <div className="flex items-center gap-4 bg-slate-50 p-4 rounded-xl border border-slate-100">
              <div className="h-10 w-10 bg-teal-50 rounded-lg text-teal-605 flex items-center justify-center">
                <Stethoscope className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs font-bold text-slate-400 uppercase">Consultations</p>
                <p className="text-2xl font-bold text-slate-900">{data.healthcare.consultations_completed}</p>
              </div>
            </div>

            <div className="flex items-center gap-4 bg-slate-50 p-4 rounded-xl border border-slate-100">
              <div className="h-10 w-10 bg-blue-50 rounded-lg text-blue-600 flex items-center justify-center">
                <Pill className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs font-bold text-slate-400 uppercase">Prescriptions</p>
                <p className="text-2xl font-bold text-slate-900">{data.healthcare.prescriptions_created}</p>
              </div>
            </div>

            <div className="flex items-center gap-4 bg-slate-50 p-4 rounded-xl border border-slate-100">
              <div className="h-10 w-10 bg-purple-50 rounded-lg text-purple-600 flex items-center justify-center">
                <Clock className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs font-bold text-slate-400 uppercase">Active Reminders</p>
                <p className="text-2xl font-bold text-slate-900">{data.healthcare.reminders_created}</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

/* ---------------------------------------------------------------------------
 * SVG Line Chart Component - User Growth
 * Calculates cumulative sum of growth to show actual growth.
 * ------------------------------------------------------------------------- */
function UserGrowthChart({ dataList, totalCount }: { dataList: DailyGrowthItem[]; totalCount: number }) {
  if (!dataList || dataList.length === 0) return <EmptyChart />

  // Calculate cumulative list backward from totalCount
  const sumInPeriod = dataList.reduce((acc, d) => acc + d.count, 0)
  let baseCount = totalCount - sumInPeriod

  const points = dataList.map((d) => {
    baseCount += d.count
    return {
      date: d.date,
      value: baseCount
    }
  })

  const values = points.map((p) => p.value)
  const maxVal = Math.max(...values, 5)
  const minVal = Math.min(...values, 0)
  const range = maxVal - minVal || 1

  const width = 500
  const height = 200
  const padLeft = 40
  const padRight = 10
  const padTop = 15
  const padBottom = 25

  const getX = (idx: number) => padLeft + (idx / (points.length - 1)) * (width - padLeft - padRight)
  const getY = (val: number) => padTop + (1 - (val - minVal) / range) * (height - padTop - padBottom)

  // Construct Path
  const linePoints = points.map((p, idx) => `${getX(idx)},${getY(p.value)}`).join(' L ')
  const linePath = `M ${linePoints}`
  const areaPath = `${linePath} L ${getX(points.length - 1)},${getY(minVal)} L ${getX(0)},${getY(minVal)} Z`

  return (
    <svg className="w-full h-full" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id="lineGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#0d9488" />
          <stop offset="100%" stopColor="#0284c7" />
        </linearGradient>
        <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#0d9488" stopOpacity="0.25" />
          <stop offset="100%" stopColor="#0d9488" stopOpacity="0.0" />
        </linearGradient>
      </defs>

      {/* Grid lines */}
      <line x1={padLeft} y1={getY(minVal)} x2={width - padRight} y2={getY(minVal)} stroke="#e2e8f0" strokeWidth="1" />
      <line x1={padLeft} y1={getY(maxVal)} x2={width - padRight} y2={getY(maxVal)} stroke="#e2e8f0" strokeWidth="1" strokeDasharray="4" />

      {/* Area & Line */}
      <path d={areaPath} fill="url(#areaGrad)" />
      <path d={linePath} fill="none" stroke="url(#lineGrad)" strokeWidth="3.5" strokeLinecap="round" />

      {/* Nodes */}
      {points.map((p, idx) => (
        <g key={idx} className="group cursor-pointer">
          <circle
            cx={getX(idx)}
            cy={getY(p.value)}
            r="4"
            fill="#ffffff"
            stroke="#0d9488"
            strokeWidth="2.5"
            className="transition-all group-hover:r-6"
          />
          <title>{`${p.date}: ${p.value} Users`}</title>
        </g>
      ))}

      {/* Y Axis text */}
      <text x={padLeft - 8} y={getY(maxVal) + 4} textAnchor="end" className="text-[10px] font-bold fill-slate-400">
        {Math.round(maxVal)}
      </text>
      <text x={padLeft - 8} y={getY(minVal) + 2} textAnchor="end" className="text-[10px] font-bold fill-slate-400">
        {Math.round(minVal)}
      </text>

      {/* X Axis Date labels */}
      <text x={getX(0)} y={height - 6} textAnchor="start" className="text-[9px] font-medium fill-slate-400">
        {points[0]?.date.split('-').slice(1).join('/')}
      </text>
      <text x={getX(points.length - 1)} y={height - 6} textAnchor="end" className="text-[9px] font-medium fill-slate-400">
        {points[points.length - 1]?.date.split('-').slice(1).join('/')}
      </text>
    </svg>
  )
}

/* ---------------------------------------------------------------------------
 * SVG Bar Chart Component - Appointment Trends
 * ------------------------------------------------------------------------- */
function AppointmentTrendsChart({ dataList }: { dataList: DailyGrowthItem[] }) {
  if (!dataList || dataList.length === 0) return <EmptyChart />

  const values = dataList.map((d) => d.count)
  const maxVal = Math.max(...values, 5)
  const minVal = 0
  const range = maxVal - minVal

  const width = 500
  const height = 200
  const padLeft = 35
  const padRight = 10
  const padTop = 15
  const padBottom = 25

  const chartWidth = width - padLeft - padRight
  const chartHeight = height - padTop - padBottom
  const barWidth = (chartWidth / dataList.length) * 0.7
  const gap = (chartWidth / dataList.length) * 0.3

  const getX = (idx: number) => padLeft + idx * (barWidth + gap) + gap / 2
  const getBarHeight = (val: number) => (val / range) * chartHeight

  return (
    <svg className="w-full h-full" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#4f46e5" />
          <stop offset="100%" stopColor="#6366f1" stopOpacity="0.75" />
        </linearGradient>
      </defs>

      {/* Grid lines */}
      <line x1={padLeft} y1={height - padBottom} x2={width - padRight} y2={height - padBottom} stroke="#e2e8f0" strokeWidth="1" />
      <line x1={padLeft} y1={padTop} x2={width - padRight} y2={padTop} stroke="#e2e8f0" strokeWidth="1" strokeDasharray="4" />

      {/* Bars */}
      {dataList.map((d, idx) => {
        const bHeight = getBarHeight(d.count)
        return (
          <g key={idx} className="group cursor-pointer">
            <rect
              x={getX(idx)}
              y={height - padBottom - bHeight}
              width={barWidth}
              height={Math.max(bHeight, 2)} // at least 2px height
              rx="3"
              fill="url(#barGrad)"
              className="hover:opacity-85 transition-opacity"
            />
            <title>{`${d.date}: ${d.count} Appts`}</title>
          </g>
        )
      })}

      {/* Y Axis text */}
      <text x={padLeft - 8} y={padTop + 4} textAnchor="end" className="text-[10px] font-bold fill-slate-400">
        {Math.round(maxVal)}
      </text>
      <text x={padLeft - 8} y={height - padBottom} textAnchor="end" className="text-[10px] font-bold fill-slate-400">
        0
      </text>

      {/* X Axis Date labels */}
      <text x={getX(0) + barWidth / 2} y={height - 6} textAnchor="start" className="text-[9px] font-medium fill-slate-400">
        {dataList[0]?.date.split('-').slice(1).join('/')}
      </text>
      <text x={getX(dataList.length - 1) + barWidth / 2} y={height - 6} textAnchor="end" className="text-[9px] font-medium fill-slate-400">
        {dataList[dataList.length - 1]?.date.split('-').slice(1).join('/')}
      </text>
    </svg>
  )
}

/* ---------------------------------------------------------------------------
 * SVG Line Chart Component - Revenue Trends
 * ------------------------------------------------------------------------- */
function RevenueTrendsChart({ dataList }: { dataList: DailyRevenueItem[] }) {
  if (!dataList || dataList.length === 0) return <EmptyChart />

  const values = dataList.map((d) => d.amount)
  const maxVal = Math.max(...values, 1000)
  const minVal = 0
  const range = maxVal - minVal

  const width = 500
  const height = 200
  const padLeft = 45
  const padRight = 10
  const padTop = 15
  const padBottom = 25

  const getX = (idx: number) => padLeft + (idx / (dataList.length - 1)) * (width - padLeft - padRight)
  const getY = (val: number) => padTop + (1 - (val - minVal) / range) * (height - padTop - padBottom)

  // Construct Paths
  const linePoints = dataList.map((d, idx) => `${getX(idx)},${getY(d.amount)}`).join(' L ')
  const linePath = `M ${linePoints}`
  const areaPath = `${linePath} L ${getX(dataList.length - 1)},${getY(minVal)} L ${getX(0)},${getY(minVal)} Z`

  return (
    <svg className="w-full h-full" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id="revLineGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#10b981" />
          <stop offset="100%" stopColor="#059669" />
        </linearGradient>
        <linearGradient id="revAreaGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#10b981" stopOpacity="0.2" />
          <stop offset="100%" stopColor="#10b981" stopOpacity="0.0" />
        </linearGradient>
      </defs>

      {/* Grid lines */}
      <line x1={padLeft} y1={height - padBottom} x2={width - padRight} y2={height - padBottom} stroke="#e2e8f0" strokeWidth="1" />
      <line x1={padLeft} y1={padTop} x2={width - padRight} y2={padTop} stroke="#e2e8f0" strokeWidth="1" strokeDasharray="4" />

      {/* Area & Line */}
      <path d={areaPath} fill="url(#revAreaGrad)" />
      <path d={linePath} fill="none" stroke="url(#revLineGrad)" strokeWidth="3" strokeLinecap="round" />

      {/* Nodes */}
      {dataList.map((d, idx) => (
        <g key={idx} className="group cursor-pointer">
          <circle
            cx={getX(idx)}
            cy={getY(d.amount)}
            r="3.5"
            fill="#ffffff"
            stroke="#10b981"
            strokeWidth="2"
          />
          <title>{`${d.date}: ₹${d.amount}`}</title>
        </g>
      ))}

      {/* Y Axis text */}
      <text x={padLeft - 8} y={padTop + 4} textAnchor="end" className="text-[9px] font-bold fill-slate-400">
        {Math.round(maxVal)}
      </text>
      <text x={padLeft - 8} y={height - padBottom} textAnchor="end" className="text-[9px] font-bold fill-slate-400">
        0
      </text>

      {/* X Axis Date labels */}
      <text x={getX(0)} y={height - 6} textAnchor="start" className="text-[9px] font-medium fill-slate-400">
        {dataList[0]?.date.split('-').slice(1).join('/')}
      </text>
      <text x={getX(dataList.length - 1)} y={height - 6} textAnchor="end" className="text-[9px] font-medium fill-slate-400">
        {dataList[dataList.length - 1]?.date.split('-').slice(1).join('/')}
      </text>
    </svg>
  )
}

/* ---------------------------------------------------------------------------
 * Empty Fallback Chart Component
 * ------------------------------------------------------------------------- */
function EmptyChart() {
  return (
    <div className="h-full w-full flex items-center justify-center text-slate-350 text-xs">
      No data points available for this period.
    </div>
  )
}
