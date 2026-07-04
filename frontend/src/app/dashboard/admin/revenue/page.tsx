'use client'

import { useState, useEffect } from 'react'
import {
  TrendingUp,
  DollarSign,
  Calendar,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  XCircle,
  AlertCircle,
  Eye,
  X,
  FileText,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Info,
  ShieldCheck,
  User,
  Activity,
  Award,
  ArrowUpDown,
  Loader2,
  Undo2,
} from 'lucide-react'
import {
  useAdminPayments,
  useRevenueSummary,
  useAdminPaymentDetail,
} from '@/hooks/use-payment-admin'
import { adminDoctorService } from '@/services/admin-doctor.service'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { AdminDoctorListResponse } from '@/types'

export default function AdminRevenuePage() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <AdminRevenueContent />
    </ProtectedRoute>
  )
}

function AdminRevenueContent() {
  // Filters & States
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [doctorFilter, setDoctorFilter] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [limit] = useState(10)
  const [skip, setSkip] = useState(0)

  // Dynamic Doctors List for filter dropdown
  const [doctors, setDoctors] = useState<AdminDoctorListResponse[]>([])
  const [loadingDoctors, setLoadingDoctors] = useState(false)

  // Selected payment for Detail Audit Drawer
  const [selectedPaymentId, setSelectedPaymentId] = useState<string | null>(null)

  // Load doctors list for dynamic filter dropdown
  useEffect(() => {
    const loadDoctors = async () => {
      try {
        setLoadingDoctors(true)
        const res = await adminDoctorService.getDoctors()
        if (res.success && res.data) {
          setDoctors(res.data)
        }
      } catch (err) {
        console.error('Failed to load doctors list for filter', err)
      } finally {
        setLoadingDoctors(false)
      }
    }
    loadDoctors()
  }, [])

  // React Query Hooks
  const {
    data: paymentsData,
    isLoading: isPaymentsLoading,
    isError: isPaymentsError,
    refetch: refetchPayments,
  } = useAdminPayments({
    search: search || undefined,
    status_filter: statusFilter || undefined,
    doctor_id: doctorFilter || undefined,
    start_date: startDate || undefined,
    end_date: endDate || undefined,
    limit,
    skip,
  })

  const {
    data: summaryData,
    isLoading: isSummaryLoading,
    isError: isSummaryError,
    refetch: refetchSummary,
  } = useRevenueSummary()

  const {
    data: detailData,
    isLoading: isDetailLoading,
    isError: isDetailError,
  } = useAdminPaymentDetail(selectedPaymentId)

  // Format Helper: Indian Rupees (INR)
  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 2,
    }).format(val)
  }

  // Format Helper: ISO Dates
  const formatDate = (isoString?: string) => {
    if (!isoString) return 'N/A'
    return new Date(isoString).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const handleRefreshAll = () => {
    refetchPayments()
    refetchSummary()
  }

  // Custom Chart Builders (SVG-based)
  const renderMonthlyBarChart = () => {
    const summary = summaryData?.monthly_revenue || []
    if (summary.length === 0) {
      return (
        <div className="flex h-48 items-center justify-center border border-dashed border-slate-200 rounded-lg text-slate-400 text-sm">
          No monthly earnings data to display
        </div>
      )
    }

    const maxVal = Math.max(...summary.map((d) => d.amount), 100)
    const height = 160
    const width = 460
    const paddingLeft = 50
    const paddingBottom = 25
    const barWidth = Math.max(12, (width - paddingLeft) / summary.length - 16)

    return (
      <div className="relative overflow-x-auto">
        <svg width="100%" height={height + paddingBottom} viewBox={`0 0 ${width} ${height + paddingBottom}`} className="overflow-visible min-w-[360px]">
          {/* Y Axis Gridlines */}
          {Array.from({ length: 4 }).map((_, idx) => {
            const y = (height / 3) * idx
            const gridVal = maxVal - (maxVal / 3) * idx
            return (
              <g key={idx} className="opacity-40">
                <line x1={paddingLeft} y1={y} x2={width} y2={y} stroke="#cbd5e1" strokeWidth="1" strokeDasharray="4" />
                <text x={paddingLeft - 8} y={y + 4} textAnchor="end" className="text-[10px] fill-slate-500 font-medium">
                  {formatCurrency(gridVal).replace('₹', '')}
                </text>
              </g>
            )
          })}

          {/* Bar elements */}
          {summary.map((item, idx) => {
            const x = paddingLeft + idx * ((width - paddingLeft) / summary.length) + 8
            const h = (item.amount / maxVal) * (height - 15)
            const y = height - h

            return (
              <g key={idx} className="group cursor-pointer">
                <title>{`${item.month}: ${formatCurrency(item.amount)} (Doc: ${formatCurrency(item.doctor_share)}, Platform: ${formatCurrency(item.platform_share)})`}</title>
                {/* Visual Bar - Platform share stack */}
                <rect
                  x={x}
                  y={y}
                  width={barWidth}
                  height={h}
                  rx="3"
                  className="fill-indigo-600 hover:fill-indigo-500 transition-all duration-200"
                />
                {/* Visual Bar - Doctor share overlay/stack */}
                <rect
                  x={x}
                  y={y + (item.platform_share / item.amount) * h}
                  width={barWidth}
                  height={Math.max(0, h - (item.platform_share / item.amount) * h)}
                  rx="3"
                  className="fill-teal-600 hover:fill-teal-500 transition-all duration-200"
                />
                {/* Axis Label */}
                <text
                  x={x + barWidth / 2}
                  y={height + 16}
                  textAnchor="middle"
                  className="text-[9px] fill-slate-500 font-semibold uppercase"
                >
                  {item.month.split('-')[1]}/{item.month.split('-')[0].substring(2)}
                </text>
              </g>
            )
          })}
        </svg>
      </div>
    )
  }

  const renderDailyRevenueLineChart = () => {
    const trend = summaryData?.daily_revenue || []
    if (trend.length === 0) {
      return (
        <div className="flex h-48 items-center justify-center border border-dashed border-slate-200 rounded-lg text-slate-400 text-sm">
          No daily revenue trend data to display
        </div>
      )
    }

    const maxVal = Math.max(...trend.map((d) => d.amount), 100)
    const height = 160
    const width = 460
    const paddingLeft = 50
    const paddingBottom = 25

    // Build SVG Path Coordinates
    const points = trend.map((item, idx) => {
      const x = paddingLeft + (idx * (width - paddingLeft - 10)) / Math.max(1, trend.length - 1)
      const y = height - (item.amount / maxVal) * (height - 20) - 5
      return { x, y }
    })

    const pathData = points.reduce(
      (acc, p, idx) => (idx === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`),
      ''
    )

    const areaData =
      points.length > 0
        ? `${pathData} L ${points[points.length - 1].x} ${height} L ${points[0].x} ${height} Z`
        : ''

    return (
      <div className="relative overflow-x-auto">
        <svg width="100%" height={height + paddingBottom} viewBox={`0 0 ${width} ${height + paddingBottom}`} className="overflow-visible min-w-[360px]">
          <defs>
            <linearGradient id="adminChartGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#4f46e5" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#4f46e5" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Y Axis Gridlines */}
          {Array.from({ length: 4 }).map((_, idx) => {
            const y = (height / 3) * idx
            const gridVal = maxVal - (maxVal / 3) * idx
            return (
              <g key={idx} className="opacity-40">
                <line x1={paddingLeft} y1={y} x2={width} y2={y} stroke="#cbd5e1" strokeWidth="1" strokeDasharray="4" />
                <text x={paddingLeft - 8} y={y + 4} textAnchor="end" className="text-[10px] fill-slate-500 font-medium">
                  {formatCurrency(gridVal).replace('₹', '')}
                </text>
              </g>
            )
          })}

          {/* Gradient Fill Area */}
          {areaData && <path d={areaData} fill="url(#adminChartGradient)" />}

          {/* Stroke Line */}
          {pathData && (
            <path
              d={pathData}
              fill="none"
              stroke="#4f46e5"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}

          {/* Point Tooltips */}
          {points.map((p, idx) => {
            const item = trend[idx]
            return (
              <g key={idx} className="group cursor-pointer">
                <title>{`${item.date}: ${formatCurrency(item.amount)}`}</title>
                <circle
                  cx={p.x}
                  cy={p.y}
                  r="4"
                  className="fill-indigo-700 hover:fill-indigo-500 stroke-white stroke-2 transition-all duration-150"
                />
              </g>
            )
          })}

          {/* Date Axis labels */}
          {trend.length > 0 && (
            <>
              <text x={points[0].x} y={height + 16} textAnchor="start" className="text-[9px] fill-slate-500 font-semibold">
                {trend[0].date}
              </text>
              {trend.length > 1 && (
                <text x={points[points.length - 1].x} y={height + 16} textAnchor="end" className="text-[9px] fill-slate-500 font-semibold">
                  {trend[trend.length - 1].date}
                </text>
              )}
            </>
          )}
        </svg>
      </div>
    )
  }

  const renderStatusDistribution = () => {
    const success = summaryData?.successful_payments ?? 0
    const pending = summaryData?.pending_payments ?? 0
    const failed = summaryData?.failed_payments ?? 0
    const refunded = summaryData?.refunded_payments ?? 0
    const total = success + pending + failed + refunded

    if (total === 0) {
      return (
        <div className="flex h-24 items-center justify-center text-slate-400 text-xs">
          No checkout status logs available
        </div>
      )
    }

    const successPct = (success / total) * 100
    const pendingPct = (pending / total) * 100
    const failedPct = (failed / total) * 100
    const refundedPct = (refunded / total) * 100

    return (
      <div className="space-y-4 pt-2">
        {/* Horizontal Stacked Bar */}
        <div className="h-6 w-full flex rounded-lg overflow-hidden border border-slate-200 shadow-inner">
          {success > 0 && (
            <div
              style={{ width: `${successPct}%` }}
              className="bg-emerald-500 hover:bg-emerald-400 transition-colors flex items-center justify-center text-[10px] text-white font-bold"
              title={`Success: ${success} (${successPct.toFixed(1)}%)`}
            >
              {successPct > 15 && `${successPct.toFixed(0)}%`}
            </div>
          )}
          {pending > 0 && (
            <div
              style={{ width: `${pendingPct}%` }}
              className="bg-amber-500 hover:bg-amber-400 transition-colors flex items-center justify-center text-[10px] text-white font-bold"
              title={`Held/Pending: ${pending} (${pendingPct.toFixed(1)}%)`}
            >
              {pendingPct > 15 && `${pendingPct.toFixed(0)}%`}
            </div>
          )}
          {failed > 0 && (
            <div
              style={{ width: `${failedPct}%` }}
              className="bg-rose-500 hover:bg-rose-400 transition-colors flex items-center justify-center text-[10px] text-white font-bold"
              title={`Failed: ${failed} (${failedPct.toFixed(1)}%)`}
            >
              {failedPct > 15 && `${failedPct.toFixed(0)}%`}
            </div>
          )}
          {refunded > 0 && (
            <div
              style={{ width: `${refundedPct}%` }}
              className="bg-slate-500 hover:bg-slate-400 transition-colors flex items-center justify-center text-[10px] text-white font-bold"
              title={`Refunded: ${refunded} (${refundedPct.toFixed(1)}%)`}
            >
              {refundedPct > 15 && `${refundedPct.toFixed(0)}%`}
            </div>
          )}
        </div>

        {/* Legend Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="h-3 w-3 bg-emerald-500 rounded-sm" />
            <span className="font-semibold text-slate-700">Success ({success})</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-3 w-3 bg-amber-500 rounded-sm" />
            <span className="font-semibold text-slate-700">Held ({pending})</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-3 w-3 bg-rose-500 rounded-sm" />
            <span className="font-semibold text-slate-700">Failed ({failed})</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-3 w-3 bg-slate-500 rounded-sm" />
            <span className="font-semibold text-slate-700">Refunded ({refunded})</span>
          </div>
        </div>
      </div>
    )
  }

  // Get status badge colors
  const getStatusBadge = (statusStr: string) => {
    const cleanStatus = (statusStr || '').toLowerCase()
    if (cleanStatus === 'completed' || cleanStatus === 'success') {
      return (
        <Badge className="bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold capitalize gap-1 hover:bg-emerald-50 shadow-none">
          <CheckCircle2 className="h-3 w-3" />
          Success
        </Badge>
      )
    } else if (cleanStatus === 'pending' || cleanStatus === 'held') {
      return (
        <Badge className="bg-amber-50 text-amber-700 border border-amber-200 font-semibold capitalize gap-1 hover:bg-amber-50 shadow-none">
          <Clock className="h-3 w-3" />
          Held
        </Badge>
      )
    } else if (cleanStatus === 'refunded') {
      return (
        <Badge className="bg-slate-100 text-slate-700 border border-slate-300 font-semibold capitalize gap-1 hover:bg-slate-100 shadow-none">
          <Undo2 className="h-3 w-3" />
          Refunded
        </Badge>
      )
    } else {
      return (
        <Badge className="bg-rose-50 text-rose-700 border border-rose-200 font-semibold capitalize gap-1 hover:bg-rose-50 shadow-none">
          <XCircle className="h-3 w-3" />
          {cleanStatus}
        </Badge>
      )
    }
  }

  const isLoading = isPaymentsLoading || isSummaryLoading
  const isError = isPaymentsError || isSummaryError

  return (
    <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 relative">
      {/* Page Title Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 flex items-center gap-2.5">
            <ShieldCheck className="h-8 w-8 text-indigo-600" />
            Financial Operations Dashboard
          </h1>
          <p className="text-slate-500 mt-1.5">
            Platform revenue metrics, transaction audits, and gateway settlements status.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={handleRefreshAll}
            variant="outline"
            className="border-slate-200 text-slate-700 font-semibold shadow-sm hover:bg-slate-50"
            disabled={isLoading}
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin text-slate-400" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-2 text-indigo-600" />
            )}
            Refresh Operations
          </Button>
        </div>
      </div>

      {isError ? (
        <div className="flex flex-col items-center justify-center py-16 text-center bg-white border border-slate-200 rounded-xl shadow-sm">
          <div className="p-4 rounded-full bg-rose-50 text-rose-600 mb-4">
            <AlertCircle className="h-8 w-8 animate-bounce" />
          </div>
          <h3 className="text-lg font-bold text-slate-800">
            Failed to aggregate financial statements
          </h3>
          <p className="text-sm text-slate-500 mt-1 max-w-md">
            The server encountered an error while calculating transaction distributions. Please try again.
          </p>
          <Button onClick={handleRefreshAll} variant="outline" className="mt-5 border-slate-200">
            Retry Connection
          </Button>
        </div>
      ) : (
        <>
          {/* Grid of 8 Metrics Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {/* Card 1: Platform Gross Volume */}
            <Card className="border border-slate-200 bg-white shadow-sm relative overflow-hidden group hover:border-indigo-400 transition-all duration-300">
              <CardContent className="p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                      Platform Gross Volume
                    </p>
                    {isSummaryLoading ? (
                      <div className="h-8 w-28 bg-slate-200 rounded animate-pulse mt-2" />
                    ) : (
                      <h3 className="text-2xl font-extrabold text-slate-900 mt-1.5">
                        {formatCurrency(summaryData?.total_revenue ?? 0)}
                      </h3>
                    )}
                  </div>
                  <div className="p-2.5 bg-indigo-50 text-indigo-600 rounded-xl group-hover:bg-indigo-100 transition-colors">
                    <DollarSign className="h-5 w-5" />
                  </div>
                </div>
                <p className="text-[10px] text-slate-400 mt-3 border-t pt-2">Total amount processed successfully</p>
              </CardContent>
            </Card>

            {/* Card 2: Platform Revenue */}
            <Card className="border border-slate-200 bg-white shadow-sm relative overflow-hidden group hover:border-indigo-400 transition-all duration-300">
              <CardContent className="p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                      Platform Revenue (15%)
                    </p>
                    {isSummaryLoading ? (
                      <div className="h-8 w-28 bg-slate-200 rounded animate-pulse mt-2" />
                    ) : (
                      <h3 className="text-2xl font-extrabold text-indigo-600 mt-1.5">
                        {formatCurrency(summaryData?.platform_earnings ?? 0)}
                      </h3>
                    )}
                  </div>
                  <div className="p-2.5 bg-indigo-50 text-indigo-600 rounded-xl group-hover:bg-indigo-100 transition-colors">
                    <TrendingUp className="h-5 w-5" />
                  </div>
                </div>
                <p className="text-[10px] text-slate-400 mt-3 border-t pt-2">Platform commission share earnings</p>
              </CardContent>
            </Card>

            {/* Card 3: Doctor Payouts */}
            <Card className="border border-slate-200 bg-white shadow-sm relative overflow-hidden group hover:border-indigo-400 transition-all duration-300">
              <CardContent className="p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                      Doctor Payouts (85%)
                    </p>
                    {isSummaryLoading ? (
                      <div className="h-8 w-28 bg-slate-200 rounded animate-pulse mt-2" />
                    ) : (
                      <h3 className="text-2xl font-extrabold text-slate-900 mt-1.5">
                        {formatCurrency(summaryData?.doctor_payouts ?? 0)}
                      </h3>
                    )}
                  </div>
                  <div className="p-2.5 bg-indigo-50 text-indigo-600 rounded-xl group-hover:bg-indigo-100 transition-colors">
                    <User className="h-5 w-5" />
                  </div>
                </div>
                <p className="text-[10px] text-slate-400 mt-3 border-t pt-2">Total share transferred to providers</p>
              </CardContent>
            </Card>

            {/* Card 4: Pending Payouts */}
            <Card className="border border-slate-200 bg-white shadow-sm relative overflow-hidden group hover:border-indigo-400 transition-all duration-300">
              <CardContent className="p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                      Pending Payouts
                    </p>
                    {isSummaryLoading ? (
                      <div className="h-8 w-28 bg-slate-200 rounded animate-pulse mt-2" />
                    ) : (
                      <h3 className="text-2xl font-extrabold text-amber-600 mt-1.5">
                        {formatCurrency(summaryData?.pending_payouts ?? 0)}
                      </h3>
                    )}
                  </div>
                  <div className="p-2.5 bg-amber-50 text-amber-600 rounded-xl group-hover:bg-amber-100 transition-colors">
                    <Clock className="h-5 w-5" />
                  </div>
                </div>
                <p className="text-[10px] text-slate-400 mt-3 border-t pt-2">Doctor share held in pending/escrow</p>
              </CardContent>
            </Card>

            {/* Card 5: Successful Payments */}
            <Card className="border border-slate-200 bg-white shadow-sm relative overflow-hidden group hover:border-indigo-400 transition-all duration-300">
              <CardContent className="p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                      Successful Payments
                    </p>
                    {isSummaryLoading ? (
                      <div className="h-8 w-28 bg-slate-200 rounded animate-pulse mt-2" />
                    ) : (
                      <h3 className="text-2xl font-extrabold text-emerald-600 mt-1.5">
                        {summaryData?.successful_payments ?? 0}
                      </h3>
                    )}
                  </div>
                  <div className="p-2.5 bg-emerald-50 text-emerald-650 rounded-xl">
                    <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                  </div>
                </div>
                <p className="text-[10px] text-slate-400 mt-3 border-t pt-2">Count of successful consultations paid</p>
              </CardContent>
            </Card>

            {/* Card 6: Failed Payments */}
            <Card className="border border-slate-200 bg-white shadow-sm relative overflow-hidden group hover:border-indigo-400 transition-all duration-300">
              <CardContent className="p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                      Failed Payments
                    </p>
                    {isSummaryLoading ? (
                      <div className="h-8 w-28 bg-slate-200 rounded animate-pulse mt-2" />
                    ) : (
                      <h3 className="text-2xl font-extrabold text-rose-650 mt-1.5 text-rose-600">
                        {summaryData?.failed_payments ?? 0}
                      </h3>
                    )}
                  </div>
                  <div className="p-2.5 bg-rose-50 text-rose-600 rounded-xl">
                    <XCircle className="h-5 w-5" />
                  </div>
                </div>
                <p className="text-[10px] text-slate-405 mt-3 border-t pt-2 text-rose-500">
                  Failed: {formatCurrency(summaryData?.failed_revenue ?? 0)} volume
                </p>
              </CardContent>
            </Card>

            {/* Card 7: Refunded Payments */}
            <Card className="border border-slate-200 bg-white shadow-sm relative overflow-hidden group hover:border-indigo-400 transition-all duration-300">
              <CardContent className="p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                      Refunded Payments
                    </p>
                    {isSummaryLoading ? (
                      <div className="h-8 w-28 bg-slate-200 rounded animate-pulse mt-2" />
                    ) : (
                      <h3 className="text-2xl font-extrabold text-slate-700 mt-1.5">
                        {summaryData?.refunded_payments ?? 0}
                      </h3>
                    )}
                  </div>
                  <div className="p-2.5 bg-slate-100 text-slate-600 rounded-xl">
                    <Undo2 className="h-5 w-5" />
                  </div>
                </div>
                <p className="text-[10px] text-slate-405 mt-3 border-t pt-2">
                  Refunded: {formatCurrency(summaryData?.refunded_revenue ?? 0)} volume
                </p>
              </CardContent>
            </Card>

            {/* Card 8: Total Transactions */}
            <Card className="border border-slate-200 bg-white shadow-sm relative overflow-hidden group hover:border-indigo-400 transition-all duration-300">
              <CardContent className="p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                      Total Transaction Logs
                    </p>
                    {isSummaryLoading ? (
                      <div className="h-8 w-28 bg-slate-200 rounded animate-pulse mt-2" />
                    ) : (
                      <h3 className="text-2xl font-extrabold text-slate-900 mt-1.5">
                        {summaryData?.total_transactions ?? 0}
                      </h3>
                    )}
                  </div>
                  <div className="p-2.5 bg-indigo-50 text-indigo-600 rounded-xl group-hover:bg-indigo-100 transition-colors">
                    <Activity className="h-5 w-5" />
                  </div>
                </div>
                <p className="text-[10px] text-slate-400 mt-3 border-t pt-2">All checkout references combined</p>
              </CardContent>
            </Card>
          </div>

          {/* SVG Charts section */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="border border-slate-200 shadow-sm bg-white lg:col-span-1">
              <CardHeader className="border-b border-slate-100 pb-4">
                <CardTitle className="text-base font-bold text-slate-800 flex items-center gap-2">
                  <Activity className="h-5 w-5 text-indigo-600" />
                  Gateway Status Distribution
                </CardTitle>
                <CardDescription className="text-xs">Checkout status metrics</CardDescription>
              </CardHeader>
              <CardContent className="pt-6">
                {isSummaryLoading ? (
                  <div className="h-32 bg-slate-100 rounded animate-pulse" />
                ) : (
                  renderStatusDistribution()
                )}
              </CardContent>
            </Card>

            <Card className="border border-slate-200 shadow-sm bg-white lg:col-span-1">
              <CardHeader className="border-b border-slate-100 pb-4">
                <CardTitle className="text-base font-bold text-slate-800 flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-indigo-600" />
                  Monthly Payout Splits
                </CardTitle>
                <CardDescription className="text-xs">Doctor & platform splits stack</CardDescription>
              </CardHeader>
              <CardContent className="pt-6">
                {isSummaryLoading ? (
                  <div className="h-48 bg-slate-100 rounded animate-pulse" />
                ) : (
                  renderMonthlyBarChart()
                )}
              </CardContent>
            </Card>

            <Card className="border border-slate-200 shadow-sm bg-white lg:col-span-1">
              <CardHeader className="border-b border-slate-100 pb-4">
                <CardTitle className="text-base font-bold text-slate-800 flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-indigo-600" />
                  Daily Revenue Trend
                </CardTitle>
                <CardDescription className="text-xs">Aggregate daily consult volumes</CardDescription>
              </CardHeader>
              <CardContent className="pt-6">
                {isSummaryLoading ? (
                  <div className="h-48 bg-slate-100 rounded animate-pulse" />
                ) : (
                  renderDailyRevenueLineChart()
                )}
              </CardContent>
            </Card>
          </div>

          {/* Filters & Transaction Ledger */}
          <Card className="border border-slate-200 shadow-sm bg-white">
            <CardHeader className="border-b border-slate-100 pb-4 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              <CardTitle className="text-base font-bold text-slate-800 flex items-center gap-2">
                <FileText className="h-5 w-5 text-indigo-600" />
                Transaction Statement Logs
              </CardTitle>
              {/* Date Filters & Dropdowns */}
              <div className="flex flex-wrap items-center gap-3">
                <div className="relative w-full sm:w-[200px]">
                  <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
                  <Input
                    placeholder="Search patient/email..."
                    value={search}
                    onChange={(e) => {
                      setSearch(e.target.value)
                      setSkip(0)
                    }}
                    className="h-9 pl-8 text-xs border-slate-200 rounded"
                  />
                </div>
                {/* Doctor Filter Dropdown */}
                <select
                  value={doctorFilter}
                  onChange={(e) => {
                    setDoctorFilter(e.target.value)
                    setSkip(0)
                  }}
                  disabled={loadingDoctors}
                  className="h-9 text-xs bg-white border border-slate-200 rounded px-2.5 text-slate-700 outline-none focus:border-indigo-500 cursor-pointer max-w-[180px]"
                >
                  <option value="">All Doctors</option>
                  {doctors.map((doc) => (
                    <option key={doc.user_id} value={doc.user_id}>
                      {doc.full_name}
                    </option>
                  ))}
                </select>

                <div className="flex items-center gap-1.5">
                  <Calendar className="h-4 w-4 text-slate-400" />
                  <Input
                    type="date"
                    value={startDate}
                    onChange={(e) => {
                      setStartDate(e.target.value)
                      setSkip(0)
                    }}
                    className="h-9 py-1 px-2 border-slate-200 text-xs rounded bg-white w-[130px]"
                  />
                  <span className="text-xs text-slate-400">to</span>
                  <Input
                    type="date"
                    value={endDate}
                    onChange={(e) => {
                      setEndDate(e.target.value)
                      setSkip(0)
                    }}
                    className="h-9 py-1 px-2 border-slate-200 text-xs rounded bg-white w-[130px]"
                  />
                </div>
                <select
                  value={statusFilter}
                  onChange={(e) => {
                    setStatusFilter(e.target.value)
                    setSkip(0)
                  }}
                  className="h-9 text-xs bg-white border border-slate-200 rounded px-2.5 text-slate-700 outline-none focus:border-indigo-500 cursor-pointer"
                >
                  <option value="">All Statuses</option>
                  <option value="success">Success</option>
                  <option value="pending">Held</option>
                  <option value="refunded">Refunded</option>
                  <option value="failed">Failed</option>
                </select>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              {isPaymentsLoading ? (
                <div className="p-8 space-y-3">
                  <div className="h-5 bg-slate-100 rounded animate-pulse w-full" />
                  <div className="h-10 bg-slate-50 rounded animate-pulse w-full" />
                  <div className="h-10 bg-slate-50 rounded animate-pulse w-full" />
                </div>
              ) : !paymentsData || paymentsData.payments.length === 0 ? (
                <div className="py-16 text-center">
                  <div className="p-4 bg-slate-50 text-slate-400 w-fit mx-auto rounded-full mb-3">
                    <Search className="h-6 w-6 text-slate-350" />
                  </div>
                  <h4 className="text-slate-800 font-bold text-sm">No transaction entries found</h4>
                  <p className="text-slate-500 text-xs mt-1">
                    No checkout events matched your current filters.
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm border-collapse">
                     <thead>
                       <tr className="bg-slate-50 border-b border-slate-100 text-slate-500 font-semibold text-xs uppercase tracking-wider">
                         <th className="py-3.5 px-6">ID & Date</th>
                         <th className="py-3.5 px-6">Patient</th>
                         <th className="py-3.5 px-6">Doctor</th>
                         <th className="py-3.5 px-6 text-right">Consultation Fee</th>
                         <th className="py-3.5 px-6 text-right">Doctor Share (85%)</th>
                         <th className="py-3.5 px-6 text-right">Platform Fee (15%)</th>
                         <th className="py-3.5 px-6">Status</th>
                         <th className="py-3.5 px-6 text-center">Audit</th>
                       </tr>
                     </thead>
                     <tbody className="divide-y divide-slate-100">
                       {paymentsData.payments.map((p) => (
                         <tr key={p.payment_id} className="hover:bg-slate-50/50 transition-colors">
                           <td className="py-4 px-6">
                             <span className="font-mono text-xs text-slate-400">
                               #{p.payment_id.substring(18)}
                             </span>
                             <div className="text-[10px] text-slate-500 mt-0.5">
                               {formatDate(p.verified_at || p.created_at)}
                             </div>
                           </td>
                           <td className="py-4 px-6">
                             <div className="font-semibold text-slate-800">
                               {p.patient.full_name}
                             </div>
                             <div className="text-[10px] text-slate-400">
                               {p.patient.email}
                             </div>
                           </td>
                           <td className="py-4 px-6">
                             <div className="font-semibold text-slate-800">
                               {p.doctor.full_name}
                             </div>
                             <div className="text-[10px] text-slate-400">
                               {p.doctor.specialization}
                             </div>
                           </td>
                           <td className="py-4 px-6 text-right text-slate-700 font-semibold">
                             {formatCurrency(p.amount)}
                           </td>
                           <td className="py-4 px-6 text-right text-teal-700 text-xs">
                             {formatCurrency(p.doctor_share)}
                           </td>
                           <td className="py-4 px-6 text-right text-indigo-600 text-xs font-semibold">
                             {formatCurrency(p.platform_share)}
                           </td>
                           <td className="py-4 px-6">
                             {getStatusBadge(p.payment_status)}
                           </td>
                           <td className="py-4 px-6 text-center">
                             <Button
                               onClick={() => setSelectedPaymentId(p.payment_id)}
                               variant="ghost"
                               size="icon"
                               className="h-8 w-8 hover:bg-indigo-50 hover:text-indigo-600 rounded-full"
                               title="Audit Details"
                             >
                               <Eye className="h-4 w-4" />
                             </Button>
                           </td>
                         </tr>
                       ))}
                     </tbody>
                   </table>

                   {/* Paginated Controller footer */}
                   {paymentsData.total > limit && (
                     <div className="flex items-center justify-between border-t border-slate-100 py-3.5 px-6 text-xs text-slate-600 bg-slate-50/30">
                       <span>
                         Showing <span className="font-semibold">{skip + 1}</span> to{' '}
                         <span className="font-semibold">
                           {Math.min(skip + limit, paymentsData.total)}
                         </span>{' '}
                         of <span className="font-semibold">{paymentsData.total}</span> records
                       </span>
                       <div className="flex gap-2">
                         <Button
                           onClick={() => setSkip(Math.max(0, skip - limit))}
                           disabled={skip === 0}
                           variant="outline"
                           size="sm"
                           className="h-7 text-[10px] border-slate-200"
                         >
                           <ChevronLeft className="h-3 w-3 mr-1" />
                           Prev
                         </Button>
                         <Button
                           onClick={() => setSkip(skip + limit)}
                           disabled={skip + limit >= paymentsData.total}
                           variant="outline"
                           size="sm"
                           className="h-7 text-[10px] border-slate-200"
                         >
                           Next
                           <ChevronRight className="h-3 w-3 ml-1" />
                         </Button>
                       </div>
                     </div>
                   )}
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {/* Slide-out Audit Details Drawer */}
      {selectedPaymentId && (
        <div className="fixed inset-0 z-50 overflow-hidden">
          {/* Backdrop */}
          <div
            onClick={() => setSelectedPaymentId(null)}
            className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm transition-opacity duration-300"
          />

          <div className="absolute inset-y-0 right-0 max-w-full flex pl-10">
            <div className="w-screen max-w-md bg-white shadow-2xl flex flex-col border-l border-slate-200">
              {/* Drawer Header */}
              <div className="px-6 py-5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">Payment Audit Details</h2>
                  <p className="text-xs text-slate-500 mt-1">Detailed verification log of gateway events.</p>
                </div>
                <Button
                  onClick={() => setSelectedPaymentId(null)}
                  variant="ghost"
                  size="icon"
                  className="rounded-full hover:bg-slate-200 text-slate-500"
                >
                  <X className="h-5 w-5" />
                </Button>
              </div>

              {/* Drawer Content */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {isDetailLoading ? (
                  <div className="flex flex-col items-center justify-center py-20 gap-3">
                    <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
                    <p className="text-xs text-slate-500">Retrieving settlement records...</p>
                  </div>
                ) : isDetailError || !detailData ? (
                  <div className="text-center py-10">
                    <AlertCircle className="h-8 w-8 text-rose-500 mx-auto mb-2" />
                    <p className="text-sm font-semibold text-slate-800">Failed to load detail logs</p>
                  </div>
                ) : (
                  <div className="space-y-6 text-sm">
                    {/* Status Overview Card */}
                    <div className="p-4 rounded-xl border border-slate-100 bg-slate-50 flex items-center justify-between">
                      <div>
                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Settlement Status</p>
                        <div className="mt-1">{getStatusBadge(detailData.payment_status)}</div>
                      </div>
                      <div className="text-right">
                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Gross Fee</p>
                        <p className="text-lg font-extrabold text-slate-900 mt-0.5">{formatCurrency(detailData.amount)}</p>
                      </div>
                    </div>

                    {/* Parties involved */}
                    <div className="space-y-4">
                      <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider border-b pb-1">Parties & Appointment</h4>
                      
                      <div className="space-y-3">
                        <div>
                          <p className="text-[10px] text-slate-400 font-semibold uppercase">Patient</p>
                          <p className="font-semibold text-slate-800">{detailData.patient.full_name}</p>
                          <p className="text-xs text-slate-500">{detailData.patient.email}</p>
                          <p className="text-[10px] text-slate-400 mt-0.5 font-mono">ID: {detailData.patient.id}</p>
                        </div>
                        
                        <div>
                          <p className="text-[10px] text-slate-400 font-semibold uppercase">Practitioner</p>
                          <p className="font-semibold text-slate-800">{detailData.doctor.full_name}</p>
                          <p className="text-xs text-slate-500">{detailData.doctor.specialization}</p>
                          <p className="text-[10px] text-slate-400 mt-0.5 font-mono">ID: {detailData.doctor.id}</p>
                        </div>

                        <div>
                          <p className="text-[10px] text-slate-400 font-semibold uppercase">Appointment Link</p>
                          <p className="text-xs text-slate-700">
                            Slot: {detailData.appointment?.slot_date || 'N/A'} ({detailData.appointment?.slot_time || 'N/A'})
                          </p>
                          {detailData.appointment?.reason && (
                            <p className="text-xs text-slate-500 italic mt-0.5">Reason: "{detailData.appointment.reason}"</p>
                          )}
                          <p className="text-[10px] text-slate-400 mt-0.5 font-mono">Appt ID: {detailData.appointment_id}</p>
                        </div>
                      </div>
                    </div>

                    {/* Financial split ledger */}
                    <div className="space-y-3">
                      <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider border-b pb-1">Earnings Splitting</h4>
                      <div className="space-y-2 bg-slate-50 p-3 rounded-lg border border-slate-100">
                        <div className="flex justify-between">
                          <span className="text-slate-500">Gross Total paid:</span>
                          <span className="font-bold text-slate-800">{formatCurrency(detailData.amount)}</span>
                        </div>
                        <div className="flex justify-between text-teal-700">
                          <span>Doctor Payout (85%):</span>
                          <span className="font-semibold">{formatCurrency(detailData.doctor_share)}</span>
                        </div>
                        <div className="flex justify-between text-indigo-600 font-semibold">
                          <span>Platform Commission (15%):</span>
                          <span>{formatCurrency(detailData.platform_share)}</span>
                        </div>
                      </div>
                    </div>

                    {/* Transaction metadata */}
                    <div className="space-y-4">
                      <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider border-b pb-1">Gateway Transaction Meta</h4>
                      <div className="space-y-2.5 text-xs">
                        <div>
                          <p className="text-[10px] text-slate-400 font-semibold uppercase">Razorpay Order ID</p>
                          <p className="font-mono text-slate-700">{detailData.razorpay_order_id || 'N/A'}</p>
                        </div>
                        <div>
                          <p className="text-[10px] text-slate-400 font-semibold uppercase">Razorpay Payment ID</p>
                          <p className="font-mono text-slate-700">{detailData.razorpay_payment_id || 'N/A'}</p>
                        </div>
                        <div>
                          <p className="text-[10px] text-slate-400 font-semibold uppercase">Checkout Created At</p>
                          <p className="text-slate-700">{formatDate(detailData.created_at)}</p>
                        </div>
                        <div>
                          <p className="text-[10px] text-slate-400 font-semibold uppercase">Settled / Verified At</p>
                          <p className="text-slate-700">{formatDate(detailData.verified_at)}</p>
                        </div>
                      </div>
                    </div>

                    {/* Raw response logger */}
                    {detailData.gateway_response && (
                      <div className="space-y-2">
                        <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider border-b pb-1">Raw Gateway Callback Payload</h4>
                        <pre className="bg-slate-900 text-emerald-400 p-3 rounded-lg overflow-x-auto text-[10px] max-h-48 font-mono">
                          {JSON.stringify(detailData.gateway_response, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
