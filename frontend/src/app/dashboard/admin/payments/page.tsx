'use client'

import { useState } from 'react'
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
  ArrowUpDown,
  Loader2,
} from 'lucide-react'
import {
  useAdminPayments,
  useRevenueSummary,
  useAdminPaymentDetail,
} from '@/hooks/use-payment-admin'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'

function AdminPaymentsContent() {
  // Filters & States
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [limit] = useState(10)
  const [skip, setSkip] = useState(0)
  
  // Selected payment for Detail Audit Drawer
  const [selectedPaymentId, setSelectedPaymentId] = useState<string | null>(null)

  // React Query Hooks
  const {
    data: paymentsData,
    isLoading: isPaymentsLoading,
    isError: isPaymentsError,
    refetch: refetchPayments,
  } = useAdminPayments({
    search: search || undefined,
    status_filter: statusFilter || undefined,
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

          {/* Date Axis labels (Render first and last labels to avoid congestion) */}
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
    const total = success + pending + failed

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
              title={`Held: ${pending} (${pendingPct.toFixed(1)}%)`}
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
        </div>

        {/* Legend Grid */}
        <div className="grid grid-cols-3 gap-2.5 text-xs">
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
          <CheckCircle2 className="h-3 w-3 animate-pulse" />
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
          {/* Glassmorphic Summary Card Panels */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Stat Box 1: Total Revenue */}
            <Card className="border border-slate-200 bg-white shadow-sm relative overflow-hidden group hover:border-indigo-400 transition-all duration-300">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                      Total Revenue
                    </p>
                    {isSummaryLoading ? (
                      <div className="h-8 w-28 bg-slate-200 rounded animate-pulse mt-2" />
                    ) : (
                      <h3 className="text-2xl font-extrabold text-slate-900 mt-1.5">
                        {formatCurrency(summaryData?.total_revenue ?? 0)}
                      </h3>
                    )}
                  </div>
                  <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl group-hover:bg-indigo-100 transition-colors">
                    <DollarSign className="h-6 w-6" />
                  </div>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-slate-500">Gross consultations</span>
                  <Badge variant="outline" className="bg-indigo-50/50 text-indigo-700 border-indigo-200 font-bold">
                    Platform Volume
                  </Badge>
                </div>
              </CardContent>
            </Card>

            {/* Stat Box 2: Platform Earnings */}
            <Card className="border border-slate-200 bg-white shadow-sm relative overflow-hidden group hover:border-indigo-400 transition-all duration-300">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                      Platform Share (15%)
                    </p>
                    {isSummaryLoading ? (
                      <div className="h-8 w-28 bg-slate-200 rounded animate-pulse mt-2" />
                    ) : (
                      <h3 className="text-2xl font-extrabold text-indigo-600 mt-1.5">
                        {formatCurrency(summaryData?.platform_earnings ?? 0)}
                      </h3>
                    )}
                  </div>
                  <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl group-hover:bg-indigo-100 transition-colors">
                    <TrendingUp className="h-6 w-6" />
                  </div>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-slate-500">Net platform margins</span>
                  <Badge variant="outline" className="bg-emerald-50/50 text-emerald-700 border-emerald-200 font-bold">
                    Profits Logged
                  </Badge>
                </div>
              </CardContent>
            </Card>

            {/* Stat Box 3: Doctor Earnings */}
            <Card className="border border-slate-200 bg-white shadow-sm relative overflow-hidden group hover:border-indigo-400 transition-all duration-300">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                      Doctor Share (85%)
                    </p>
                    {isSummaryLoading ? (
                      <div className="h-8 w-28 bg-slate-200 rounded animate-pulse mt-2" />
                    ) : (
                      <h3 className="text-2xl font-extrabold text-slate-900 mt-1.5">
                        {formatCurrency(summaryData?.doctor_payouts ?? 0)}
                      </h3>
                    )}
                  </div>
                  <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl group-hover:bg-indigo-100 transition-colors">
                    <User className="h-6 w-6" />
                  </div>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-slate-500">Gross doctor payouts</span>
                  <span className="font-semibold text-slate-600 text-[10px]">
                    Avg: {formatCurrency(summaryData?.average_consultation_fee ?? 0)}
                  </span>
                </div>
              </CardContent>
            </Card>

            {/* Stat Box 4: Total Transactions */}
            <Card className="border border-slate-200 bg-white shadow-sm relative overflow-hidden group hover:border-indigo-400 transition-all duration-300">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                      Checkout Logs
                    </p>
                    {isSummaryLoading ? (
                      <div className="h-8 w-28 bg-slate-200 rounded animate-pulse mt-2" />
                    ) : (
                      <h3 className="text-2xl font-extrabold text-slate-900 mt-1.5">
                        {summaryData?.total_transactions ?? 0}
                      </h3>
                    )}
                  </div>
                  <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl group-hover:bg-indigo-100 transition-colors">
                    <Activity className="h-6 w-6" />
                  </div>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-slate-500">Success: {summaryData?.successful_payments ?? 0}</span>
                  <span className="font-semibold text-rose-600">
                    Failed: {summaryData?.failed_payments ?? 0}
                  </span>
                </div>
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
                <div className="relative w-full sm:w-[220px]">
                  <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
                  <Input
                    placeholder="Search doctor or patient..."
                    value={search}
                    onChange={(e) => {
                      setSearch(e.target.value)
                      setSkip(0)
                    }}
                    className="h-9 pl-8 text-xs border-slate-200 rounded"
                  />
                </div>
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
                  <div className="p-3 bg-slate-50 text-slate-400 w-fit mx-auto rounded-full mb-3">
                    <Search className="h-6 w-6" />
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

          <div className="pointer-events-none absolute inset-y-0 right-0 flex max-w-full pl-10">
            <div className="pointer-events-auto w-screen max-w-lg">
              <div className="flex h-full flex-col bg-white shadow-2xl border-l border-slate-200">
                {/* Header */}
                <div className="bg-indigo-900 px-6 py-5 flex items-center justify-between text-white shadow-md">
                  <div>
                    <h2 className="text-lg font-bold flex items-center gap-2">
                      <ShieldCheck className="h-5 w-5 text-indigo-300" />
                      Transaction Audit Ledger
                    </h2>
                    <p className="text-[10px] text-indigo-200 font-mono mt-0.5">
                      PAYMENT_VIEWED_ADMIN Log Triggered
                    </p>
                  </div>
                  <button
                    onClick={() => setSelectedPaymentId(null)}
                    className="p-1 rounded-full text-indigo-200 hover:text-white hover:bg-indigo-800 transition-colors"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
                  {isDetailLoading ? (
                    <div className="space-y-4">
                      <div className="h-4 bg-slate-100 rounded animate-pulse w-3/4" />
                      <div className="h-24 bg-slate-50 rounded animate-pulse w-full" />
                      <div className="h-32 bg-slate-50 rounded animate-pulse w-full" />
                    </div>
                  ) : isDetailError || !detailData ? (
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                      <AlertCircle className="h-8 w-8 text-rose-500 mb-2 animate-bounce" />
                      <p className="text-sm font-semibold text-slate-800">
                        Failed to fetch payment details
                      </p>
                      <p className="text-xs text-slate-400 mt-1 max-w-xs">
                        Audit reference record could not be found or connection timed out.
                      </p>
                    </div>
                  ) : (
                    <>
                      {/* Status Header info */}
                      <div className="flex items-center justify-between p-4 bg-slate-50 border border-slate-200 rounded-lg">
                        <div>
                          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">
                            Payment ID
                          </span>
                          <span className="text-xs font-mono font-bold text-slate-800">
                            {detailData.payment_id}
                          </span>
                        </div>
                        <div>
                          {getStatusBadge(detailData.payment_status)}
                        </div>
                      </div>

                      {/* Itemized Payout Splits */}
                      <div className="space-y-2">
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                          Itemized Revenue Distribution
                        </h4>
                        <div className="bg-slate-50/50 border border-slate-100 rounded-lg p-4 space-y-3.5">
                          <div className="flex justify-between items-center text-sm text-slate-600">
                            <span>Consultation Fee (Gross)</span>
                            <span className="font-semibold text-slate-800">
                              {formatCurrency(detailData.amount)}
                            </span>
                          </div>
                          <div className="flex justify-between items-center text-sm text-teal-700">
                            <span className="flex items-center gap-1.5">
                              Doctor Share (85%)
                            </span>
                            <span className="font-bold">
                              {formatCurrency(detailData.doctor_share)}
                            </span>
                          </div>
                          <div className="flex justify-between items-center text-sm text-indigo-600">
                            <span className="flex items-center gap-1.5">
                              Platform Fee (15%)
                            </span>
                            <span className="font-bold">
                              {formatCurrency(detailData.platform_share)}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Gateway Payload Metadata */}
                      <div className="space-y-2">
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                          Gateway Verification Details
                        </h4>
                        <div className="bg-slate-50/50 border border-slate-100 rounded-lg p-4 space-y-3 text-xs">
                          <div className="flex justify-between">
                            <span className="text-slate-500">Order Link ID</span>
                            <span className="font-mono font-semibold text-slate-800 select-all">
                              {detailData.razorpay_order_id || 'N/A'}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">Razorpay Payment ID</span>
                            <span className="font-mono font-semibold text-slate-800 select-all">
                              {detailData.razorpay_payment_id || 'N/A'}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">Verified Timestamp</span>
                            <span className="text-slate-700">
                              {formatDate(detailData.verified_at)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">Created Timestamp</span>
                            <span className="text-slate-700">
                              {formatDate(detailData.created_at)}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Stakeholder Details */}
                      <div className="grid grid-cols-2 gap-4">
                        <div className="border border-slate-100 rounded-lg p-3 bg-slate-50/20">
                          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">
                            Patient Record
                          </span>
                          <span className="text-xs font-bold text-slate-800 block mt-1">
                            {detailData.patient.full_name}
                          </span>
                          <span className="text-[10px] text-slate-500 block truncate font-mono">
                            {detailData.patient.email}
                          </span>
                        </div>
                        <div className="border border-slate-100 rounded-lg p-3 bg-slate-50/20">
                          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">
                            Doctor Record
                          </span>
                          <span className="text-xs font-bold text-slate-800 block mt-1">
                            {detailData.doctor.full_name}
                          </span>
                          <span className="text-[10px] text-slate-500 block">
                            {detailData.doctor.specialization}
                          </span>
                        </div>
                      </div>

                      {/* Appointment Summary */}
                      <div className="space-y-2">
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                          Appointment Slot Summary
                        </h4>
                        <div className="bg-slate-50/50 border border-slate-100 rounded-lg p-4 space-y-3 text-xs">
                          <div className="flex justify-between">
                            <span className="text-slate-500">Schedule Time</span>
                            <span className="font-semibold text-slate-800">
                              {detailData.appointment.slot_date} @ {detailData.appointment.slot_time}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">Visit Status</span>
                            <span className="capitalize font-semibold text-slate-800">
                              {detailData.appointment.status}
                            </span>
                          </div>
                          {detailData.appointment.reason && (
                            <div className="pt-2 border-t border-slate-100">
                              <span className="text-slate-400 block mb-0.5">Reason for consult</span>
                              <span className="text-slate-600 leading-normal block italic bg-white p-2 rounded border border-slate-100">
                                &ldquo;{detailData.appointment.reason}&rdquo;
                              </span>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Raw JSON Audit Payload */}
                      {detailData.gateway_response && (
                        <div className="space-y-2">
                          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                            <Info className="h-3 w-3" />
                            Raw Gateway Response Metadata
                          </h4>
                          <pre className="text-[10px] text-slate-600 bg-slate-900 text-slate-100 p-4 rounded-lg overflow-x-auto font-mono max-h-48 border border-slate-800">
                            {JSON.stringify(detailData.gateway_response, null, 2)}
                          </pre>
                        </div>
                      )}
                    </>
                  )}
                </div>

                {/* Footer */}
                <div className="bg-slate-50 border-t border-slate-200 px-6 py-4 flex justify-end">
                  <Button
                    onClick={() => setSelectedPaymentId(null)}
                    variant="outline"
                    className="border-slate-200 text-xs shadow-sm hover:bg-slate-100"
                  >
                    Close Ledger Details
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function AdminPaymentsPage() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <AdminPaymentsContent />
    </ProtectedRoute>
  )
}
