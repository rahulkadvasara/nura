'use client'

import { useState } from 'react'
import {
  Wallet,
  TrendingUp,
  DollarSign,
  Calendar,
  ArrowUpDown,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  XCircle,
  AlertCircle,
  HelpCircle,
  Percent,
  Download,
  Loader2,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import {
  useDoctorEarnings,
  useDoctorWallet,
  useDoctorTransactions,
} from '@/hooks/use-doctor-earnings'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function DoctorEarningsPage() {
  // Query Filters & States
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [status, setStatus] = useState('')
  const [limit] = useState(10)
  const [skip, setSkip] = useState(0)

  // React Query Hooks
  const {
    data: walletData,
    isLoading: isWalletLoading,
    isError: isWalletError,
  } = useDoctorWallet()

  const {
    data: earningsData,
    isLoading: isEarningsLoading,
    isError: isEarningsError,
    refetch: refetchEarnings,
  } = useDoctorEarnings({
    start_date: startDate || undefined,
    end_date: endDate || undefined,
    limit,
    skip,
  })

  const {
    data: transactionsData,
    isLoading: isTransactionsLoading,
  } = useDoctorTransactions({
    start_date: startDate || undefined,
    end_date: endDate || undefined,
    status: status || undefined,
    limit,
    skip,
  })

  // Format Helper: Indian Rupees (INR)
  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 2,
    }).format(val)
  }

  // Format Helper: ISO Dates
  const formatDate = (isoString: string) => {
    if (!isoString) return ''
    return new Date(isoString).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    })
  }

  // Custom Chart Builders (SVG-based)
  const renderMonthlyBarChart = () => {
    const summary = earningsData?.monthly_earnings_summary || []
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
    const paddingLeft = 40
    const paddingBottom = 25
    const barWidth = Math.max(12, (width - paddingLeft) / summary.length - 12)

    return (
      <div className="relative">
        <svg width="100%" height={height + paddingBottom} viewBox={`0 0 ${width} ${height + paddingBottom}`} className="overflow-visible">
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
            const x = paddingLeft + idx * ((width - paddingLeft) / summary.length) + 6
            const h = (item.amount / maxVal) * (height - 10)
            const y = height - h

            return (
              <g key={idx} className="group cursor-pointer">
                <title>{`${item.month}: ${formatCurrency(item.amount)}`}</title>
                {/* Visual Bar */}
                <rect
                  x={x}
                  y={y}
                  width={barWidth}
                  height={h}
                  rx="4"
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

  const renderRevenueLineChart = () => {
    const trend = earningsData?.revenue_trend || []
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
    const paddingLeft = 40
    const paddingBottom = 25

    // Build SVG Path Coordinates
    const points = trend.map((item, idx) => {
      const x = paddingLeft + (idx * (width - paddingLeft - 10)) / Math.max(1, trend.length - 1)
      const y = height - (item.amount / maxVal) * (height - 15) - 5
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
      <div className="relative">
        <svg width="100%" height={height + paddingBottom} viewBox={`0 0 ${width} ${height + paddingBottom}`} className="overflow-visible">
          <defs>
            <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#0d9488" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#0d9488" stopOpacity="0.0" />
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
          {areaData && <path d={areaData} fill="url(#chartGradient)" />}

          {/* Stroke Line */}
          {pathData && (
            <path
              d={pathData}
              fill="none"
              stroke="#0d9488"
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
                <title>{`${formatDate(item.date)}: ${formatCurrency(item.amount)}`}</title>
                <circle
                  cx={p.x}
                  cy={p.y}
                  r="4"
                  className="fill-teal-700 hover:fill-teal-500 stroke-white stroke-2 transition-all duration-150"
                />
              </g>
            )
          })}

          {/* Date Axis labels (Render first and last labels to avoid congestion) */}
          {trend.length > 0 && (
            <>
              <text x={points[0].x} y={height + 16} textAnchor="start" className="text-[9px] fill-slate-500 font-semibold">
                {formatDate(trend[0].date).split(',')[0]}
              </text>
              {trend.length > 1 && (
                <text x={points[points.length - 1].x} y={height + 16} textAnchor="end" className="text-[9px] fill-slate-500 font-semibold">
                  {formatDate(trend[trend.length - 1].date).split(',')[0]}
                </text>
              )}
            </>
          )}
        </svg>
      </div>
    )
  }

  // Get status badge colors
  const getStatusBadge = (statusStr: string) => {
    const cleanStatus = (statusStr || '').toLowerCase()
    if (cleanStatus === 'completed' || cleanStatus === 'approved') {
      return (
        <Badge className="bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold capitalize gap-1 hover:bg-emerald-50">
          <CheckCircle2 className="h-3 w-3" />
          {cleanStatus}
        </Badge>
      )
    } else if (cleanStatus === 'pending' || cleanStatus === 'held') {
      return (
        <Badge className="bg-amber-50 text-amber-700 border border-amber-200 font-semibold capitalize gap-1 hover:bg-amber-50">
          <Clock className="h-3 w-3" />
          Escrow Held
        </Badge>
      )
    } else {
      return (
        <Badge className="bg-rose-50 text-rose-700 border border-rose-200 font-semibold capitalize gap-1 hover:bg-rose-50">
          <XCircle className="h-3 w-3" />
          {cleanStatus}
        </Badge>
      )
    }
  }

  // Main UI states mapping
  const isLoading = isWalletLoading || isEarningsLoading
  const isError = isWalletError || isEarningsError

  return (
    <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Page Title Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">
            Earnings & Wallet Dashboard
          </h1>
          <p className="text-slate-500 mt-1.5">
            Monitor consultation revenue splits, lifetime wallet metrics, and payout status logs.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={() => refetchEarnings()}
            variant="outline"
            className="border-slate-200 text-slate-700 font-semibold shadow-sm hover:bg-slate-50"
            disabled={isLoading}
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin text-slate-400" />
            ) : (
              <Calendar className="h-4 w-4 mr-2 text-teal-600" />
            )}
            Refresh Metrics
          </Button>
        </div>
      </div>

      {isError ? (
        <div className="flex flex-col items-center justify-center py-16 text-center bg-white border border-slate-200 rounded-xl shadow-sm">
          <div className="p-4 rounded-full bg-rose-50 text-rose-600 mb-4">
            <AlertCircle className="h-8 w-8" />
          </div>
          <h3 className="text-lg font-bold text-slate-800">
            Failed to aggregate financial statements
          </h3>
          <p className="text-sm text-slate-500 mt-1 max-w-md">
            The server encountered an error while calculating transaction distributions. Please try again.
          </p>
          <Button onClick={() => refetchEarnings()} variant="outline" className="mt-5 border-slate-200">
            Retry Connection
          </Button>
        </div>
      ) : (
        <>
          {/* Glassmorphic Summary Card Panels */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Stat Box 1: Available Balance */}
            <Card className="border border-slate-200 bg-white/70 backdrop-blur-md shadow-sm relative overflow-hidden group hover:border-teal-400 transition-all duration-300">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                      Available Balance
                    </p>
                    {isLoading ? (
                      <div className="h-8 w-32 bg-slate-200 rounded-md animate-pulse mt-2" />
                    ) : (
                      <h3 className="text-3xl font-extrabold text-slate-900 mt-1.5">
                        {formatCurrency(walletData?.available_amount ?? 0)}
                      </h3>
                    )}
                  </div>
                  <div className="p-3 bg-teal-50 text-teal-600 rounded-xl group-hover:bg-teal-100 transition-colors">
                    <Wallet className="h-6 w-6" />
                  </div>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-slate-500">Auto-transfers enabled</span>
                  <Badge variant="outline" className="bg-emerald-50/50 text-emerald-700 border-emerald-200 font-bold">
                    Active Wallet
                  </Badge>
                </div>
              </CardContent>
            </Card>

            {/* Stat Box 2: Pending Escrows */}
            <Card className="border border-slate-200 bg-white/70 backdrop-blur-md shadow-sm relative overflow-hidden group hover:border-teal-400 transition-all duration-300">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                      Pending Escrow
                    </p>
                    {isLoading ? (
                      <div className="h-8 w-32 bg-slate-200 rounded-md animate-pulse mt-2" />
                    ) : (
                      <h3 className="text-3xl font-extrabold text-slate-900 mt-1.5">
                        {formatCurrency(walletData?.pending_amount ?? 0)}
                      </h3>
                    )}
                  </div>
                  <div className="p-3 bg-teal-50 text-teal-600 rounded-xl group-hover:bg-teal-100 transition-colors">
                    <Clock className="h-6 w-6" />
                  </div>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-slate-500">Held pending verification</span>
                  <Badge variant="outline" className="bg-amber-50/50 text-amber-700 border-amber-200 font-bold">
                    Escrow Locked
                  </Badge>
                </div>
              </CardContent>
            </Card>

            {/* Stat Box 3: Lifetime Earnings */}
            <Card className="border border-slate-200 bg-white/70 backdrop-blur-md shadow-sm relative overflow-hidden group hover:border-teal-400 transition-all duration-300">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                      Lifetime Earnings
                    </p>
                    {isLoading ? (
                      <div className="h-8 w-32 bg-slate-200 rounded-md animate-pulse mt-2" />
                    ) : (
                      <h3 className="text-3xl font-extrabold text-slate-900 mt-1.5">
                        {formatCurrency(walletData?.lifetime_earnings ?? 0)}
                      </h3>
                    )}
                  </div>
                  <div className="p-3 bg-teal-50 text-teal-600 rounded-xl group-hover:bg-teal-100 transition-colors">
                    <TrendingUp className="h-6 w-6" />
                  </div>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-slate-500">Gross payout history</span>
                  <span className="font-semibold text-slate-600">
                    Withdrawn: {formatCurrency(walletData?.total_withdrawn ?? 0)}
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sub-Metrical Calculations Card */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 bg-slate-50 border border-slate-200 rounded-xl p-5 shadow-sm text-center">
            <div>
              <p className="text-xs font-bold text-slate-400 uppercase">
                Consultation Count
              </p>
              <p className="text-xl font-extrabold text-slate-800 mt-1">
                {isLoading ? '...' : earningsData?.total_consultations ?? 0}
              </p>
            </div>
            <div>
              <p className="text-xs font-bold text-slate-400 uppercase">
                Completed Visits
              </p>
              <p className="text-xl font-extrabold text-slate-800 mt-1">
                {isLoading ? '...' : earningsData?.total_completed_consultations ?? 0}
              </p>
            </div>
            <div>
              <p className="text-xs font-bold text-slate-400 uppercase">
                Average Consultation Fee
              </p>
              <p className="text-xl font-extrabold text-slate-800 mt-1">
                {isLoading ? '...' : formatCurrency(earningsData?.average_consultation_fee ?? 0)}
              </p>
            </div>
            <div>
              <p className="text-xs font-bold text-slate-400 uppercase">
                Revenue Splits (Doctor / Platform)
              </p>
              <p className="text-xl font-extrabold text-slate-800 mt-1 flex items-center justify-center gap-1.5">
                <span>85% / 15%</span>
                <span className="p-0.5 bg-teal-100 rounded text-teal-800 text-[10px] uppercase font-bold">
                  Fixed
                </span>
              </p>
            </div>
          </div>

          {/* SVG Charts section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="border border-slate-200 shadow-sm bg-white">
              <CardHeader className="border-b border-slate-100 pb-4">
                <CardTitle className="text-base font-bold text-slate-800 flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-teal-600" />
                  Monthly Earning Summaries
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                {isLoading ? (
                  <div className="h-48 bg-slate-100 rounded-lg animate-pulse" />
                ) : (
                  renderMonthlyBarChart()
                )}
              </CardContent>
            </Card>

            <Card className="border border-slate-200 shadow-sm bg-white">
              <CardHeader className="border-b border-slate-100 pb-4">
                <CardTitle className="text-base font-bold text-slate-800 flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-teal-600" />
                  Revenue Trends (Daily Doctor Share)
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                {isLoading ? (
                  <div className="h-48 bg-slate-100 rounded-lg animate-pulse" />
                ) : (
                  renderRevenueLineChart()
                )}
              </CardContent>
            </Card>
          </div>

          {/* Filters & Transaction Ledger */}
          <Card className="border border-slate-200 shadow-sm bg-white">
            <CardHeader className="border-b border-slate-100 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <CardTitle className="text-base font-bold text-slate-800 flex items-center gap-2">
                <Filter className="h-5 w-5 text-teal-600" />
                Transaction Statement Logs
              </CardTitle>
              {/* Date Filters & Dropdowns */}
              <div className="flex flex-wrap items-center gap-2.5">
                <div className="flex items-center gap-1.5">
                  <Calendar className="h-4 w-4 text-slate-400" />
                  <Input
                    type="date"
                    value={startDate}
                    onChange={(e) => {
                      setStartDate(e.target.value)
                      setSkip(0)
                    }}
                    className="h-8 py-1 px-2 border-slate-200 text-xs rounded bg-white w-[130px]"
                  />
                  <span className="text-xs text-slate-400">to</span>
                  <Input
                    type="date"
                    value={endDate}
                    onChange={(e) => {
                      setEndDate(e.target.value)
                      setSkip(0)
                    }}
                    className="h-8 py-1 px-2 border-slate-200 text-xs rounded bg-white w-[130px]"
                  />
                </div>
                <select
                  value={status}
                  onChange={(e) => {
                    setStatus(e.target.value)
                    setSkip(0)
                  }}
                  className="h-8 text-xs bg-white border border-slate-200 rounded px-2 text-slate-700 outline-none focus:border-teal-500 cursor-pointer"
                >
                  <option value="">All Transactions</option>
                  <option value="completed">Completed</option>
                  <option value="approved">Approved</option>
                  <option value="pending">Escrow Held</option>
                  <option value="refunded">Refunded</option>
                  <option value="failed">Failed</option>
                </select>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              {isTransactionsLoading ? (
                <div className="p-8 space-y-3">
                  <div className="h-5 bg-slate-100 rounded animate-pulse w-full" />
                  <div className="h-10 bg-slate-50 rounded animate-pulse w-full" />
                  <div className="h-10 bg-slate-50 rounded animate-pulse w-full" />
                </div>
              ) : !transactionsData || transactionsData.transactions.length === 0 ? (
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
                        <th className="py-3.5 px-6">Patient</th>
                        <th className="py-3.5 px-6">Transaction Date</th>
                        <th className="py-3.5 px-6 text-right">Consultation Fee</th>
                        <th className="py-3.5 px-6 text-right">Platform Share (15%)</th>
                        <th className="py-3.5 px-6 text-right text-teal-700">Doctor Share (85%)</th>
                        <th className="py-3.5 px-6">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {transactionsData.transactions.map((tx) => (
                        <tr key={tx.id} className="hover:bg-slate-50/50 transition-colors">
                          <td className="py-4 px-6 font-semibold text-slate-800">
                            <div>{tx.patient_name}</div>
                            {tx.consultation_id && (
                              <div className="text-[10px] text-slate-400 font-normal mt-0.5">
                                Consultation: {tx.consultation_id}
                              </div>
                            )}
                          </td>
                          <td className="py-4 px-6 text-slate-500 text-xs">
                            {formatDate(tx.payment_date || tx.created_at)}
                          </td>
                          <td className="py-4 px-6 text-right text-slate-600">
                            {formatCurrency(tx.consultation_fee)}
                          </td>
                          <td className="py-4 px-6 text-right text-slate-500 text-xs">
                            {formatCurrency(tx.platform_share)}
                          </td>
                          <td className="py-4 px-6 text-right font-bold text-teal-700">
                            {formatCurrency(tx.doctor_share)}
                          </td>
                          <td className="py-4 px-6">
                            {getStatusBadge(tx.status)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>

                  {/* Paginated Controller footer */}
                  {transactionsData.total > limit && (
                    <div className="flex items-center justify-between border-t border-slate-100 py-3.5 px-6 text-xs text-slate-600 bg-slate-50/30">
                      <span>
                        Showing <span className="font-semibold">{skip + 1}</span> to{' '}
                        <span className="font-semibold">
                          {Math.min(skip + limit, transactionsData.total)}
                        </span>{' '}
                        of <span className="font-semibold">{transactionsData.total}</span> records
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
                          disabled={skip + limit >= transactionsData.total}
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

          {/* Placeholders for Future Settlement Status and Withdrawal History */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 opacity-85">
            {/* Razorpay settlements placeholder */}
            <Card className="border border-slate-200 bg-slate-50/50 shadow-sm">
              <CardHeader className="pb-3 flex flex-row items-center justify-between">
                <CardTitle className="text-sm font-bold text-slate-700 flex items-center gap-2">
                  <Download className="h-4 w-4 text-slate-500" />
                  Razorpay Settlement Queue
                </CardTitle>
                <Badge variant="outline" className="bg-slate-100 text-slate-500 text-[10px] font-bold border-slate-200">
                  Ready
                </Badge>
              </CardHeader>
              <CardContent className="text-xs text-slate-500 leading-relaxed">
                Platform checkout features Razorpay payment routes. Upon Phase 7 deployment, auto-settlements will route funds to your registered bank account on a rolling T+2 basis. Current statuses will populate dynamically here.
              </CardContent>
            </Card>

            {/* Payout records placeholder */}
            <Card className="border border-slate-200 bg-slate-50/50 shadow-sm">
              <CardHeader className="pb-3 flex flex-row items-center justify-between">
                <CardTitle className="text-sm font-bold text-slate-700 flex items-center gap-2">
                  <Wallet className="h-4 w-4 text-slate-500" />
                  Withdrawal & Payout History
                </CardTitle>
                <Badge variant="outline" className="bg-slate-100 text-slate-500 text-[10px] font-bold border-slate-200">
                  Suspended
                </Badge>
              </CardHeader>
              <CardContent className="text-xs text-slate-500 leading-relaxed">
                Direct balance withdrawals are temporarily locked. Payout releases are queued to transfer automatically every Saturday morning. Payout history, tax deduction sheets (Form 16A), and gateway IDs will register here once operational.
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  )
}
