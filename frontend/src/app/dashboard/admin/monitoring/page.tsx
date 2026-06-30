'use client'

import { useState, useEffect } from 'react'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { toast } from 'react-hot-toast'
import {
  Activity,
  Cpu,
  Database,
  Layers,
  RefreshCw,
  Clock,
  Sparkles,
  Server,
  AlertTriangle,
  CheckCircle,
  AlertCircle,
  Loader2,
  TrendingUp,
  Shield,
  Zap,
  BarChart3,
  DollarSign
} from 'lucide-react'
import {
  useDrugHealth,
  useDrugCacheStats,
  useDrugWorkerStatus,
  useDrugTelemetryStats
} from '@/hooks/use-ai'

export default function AdminDrugMonitoringDashboard() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <AdminDrugMonitoringContent />
    </ProtectedRoute>
  )
}

function AdminDrugMonitoringContent() {
  const { data: healthData, isLoading: healthLoading, refetch: refetchHealth, isRefetching: healthRefetching } = useDrugHealth()
  const { data: cacheData, isLoading: cacheLoading, refetch: refetchCache } = useDrugCacheStats()
  const { data: workerData, isLoading: workerLoading, refetch: refetchWorkers, isRefetching: workersRefetching } = useDrugWorkerStatus()
  const { data: statsData, isLoading: statsLoading, refetch: refetchStats, isRefetching: statsRefetching } = useDrugTelemetryStats()

  const [activeTab, setActiveTab] = useState<'cache' | 'workers' | 'queue' | 'health'>('health')

  const handleRefreshAll = async () => {
    await Promise.all([refetchHealth(), refetchCache(), refetchWorkers(), refetchStats()])
    toast.success('Drug safety monitoring metrics refreshed')
  }

  const getStatusBadge = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'active':
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400">
            <CheckCircle className="h-3.5 w-3.5" />
            Healthy
          </span>
        )
      case 'degraded':
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-700 dark:bg-amber-950/30 dark:text-amber-400">
            <AlertTriangle className="h-3.5 w-3.5" />
            Degraded
          </span>
        )
      case 'unhealthy':
      case 'offline':
      case 'failed':
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2 py-1 text-xs font-semibold text-rose-700 dark:bg-rose-950/30 dark:text-rose-400">
            <AlertCircle className="h-3.5 w-3.5" />
            Unhealthy
          </span>
        )
      default:
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-400">
            <Clock className="h-3.5 w-3.5" />
            {status || 'Unknown'}
          </span>
        )
    }
  }

  const formatLatency = (val?: number) => {
    if (val === undefined || val === null) return '0.0ms'
    return `${val.toFixed(1)}ms`
  }

  // Derived metrics
  const lookupHitRatio = statsData?.core?.cache_hit_ratio ?? 0.0
  const validationThroughput = statsData?.core?.validation_checks ?? 0
  const avgValidationLatency = statsData?.core?.validation_avg_latency_ms ?? 0.0
  const avgExplanationLatency = statsData?.core?.explanation_avg_latency_ms ?? 0.0
  const fallbackCount = statsData?.core?.fallback_executions ?? 0
  const aiCost = statsData?.core?.ai_cost ?? 0.0
  const totalTokens = statsData?.core?.total_tokens ?? 0

  return (
    <div className="space-y-6 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 bg-slate-900 min-h-screen text-slate-200">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
            <Shield className="h-8 w-8 text-teal-400" />
            Drug Safety Production Monitor
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            Real-time lookups, multi-level TTL caches, background validation jobs, and AI token billing metrics.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={handleRefreshAll}
            variant="outline"
            className="flex items-center gap-2 border-slate-700 bg-slate-800 text-white hover:bg-slate-700"
            disabled={healthRefetching || workersRefetching || statsRefetching}
          >
            <RefreshCw className={`h-4 w-4 ${healthRefetching || workersRefetching || statsRefetching ? 'animate-spin' : ''}`} />
            Refresh Diagnostics
          </Button>
        </div>
      </div>

      {/* Overview Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Validation throughput */}
        <Card className="bg-slate-950 border-slate-800 shadow-lg text-white">
          <CardContent className="pt-5 flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Validations Run</span>
              <strong className="text-2xl font-black text-white block">{validationThroughput}</strong>
              <span className="text-[9px] text-teal-400 block">Avg delay: {formatLatency(avgValidationLatency)}</span>
            </div>
            <TrendingUp className="h-8 w-8 text-teal-500/20 shrink-0" />
          </CardContent>
        </Card>

        {/* Cache Hit Ratio */}
        <Card className="bg-slate-950 border-slate-800 shadow-lg text-white">
          <CardContent className="pt-5 flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Lookup Cache Hit Rate</span>
              <strong className="text-2xl font-black text-teal-400 block">{(lookupHitRatio * 100).toFixed(1)}%</strong>
              <span className="text-[9px] text-slate-400 block">Total queries: {statsData?.core?.total_lookups ?? 0}</span>
            </div>
            <Layers className="h-8 w-8 text-teal-500/20 shrink-0" />
          </CardContent>
        </Card>

        {/* Worker Status */}
        <Card className="bg-slate-950 border-slate-800 shadow-lg text-white">
          <CardContent className="pt-5 flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Background Workers</span>
              <strong className="text-2xl font-black text-indigo-400 block">
                {workerData?.active_workers ?? 0} / {workerData?.total_workers ?? 0} Active
              </strong>
              <span className="text-[9px] text-slate-400 block">Idle: {workerData?.idle_workers ?? 0}</span>
            </div>
            <Cpu className="h-8 w-8 text-indigo-500/20 shrink-0" />
          </CardContent>
        </Card>

        {/* Queue Depth */}
        <Card className="bg-slate-950 border-slate-800 shadow-lg text-white">
          <CardContent className="pt-5 flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Queue Depth</span>
              <strong className="text-2xl font-black text-amber-500 block">
                {healthData?.queue_depth ?? 0} Jobs
              </strong>
              <span className="text-[9px] text-rose-400 block">DLQ fails: {statsData?.background?.throughput?.total_failed ?? 0}</span>
            </div>
            <Activity className="h-8 w-8 text-amber-500/20 shrink-0" />
          </CardContent>
        </Card>
      </div>

      {/* Latency & AI Cost Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Explanation Latency */}
        <Card className="bg-slate-950 border-slate-800 shadow-lg text-white">
          <CardContent className="pt-5 flex items-center justify-between">
            <div>
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">AI Explanation Duration</span>
              <strong className="text-lg font-bold text-white mt-1 block">{formatLatency(avgExplanationLatency)}</strong>
              <span className="text-[9px] text-slate-400 block">Total generated: {statsData?.core?.explanation_checks ?? 0}</span>
            </div>
            <Zap className="h-7 w-7 text-indigo-400/20" />
          </CardContent>
        </Card>

        {/* Fallbacks */}
        <Card className="bg-slate-950 border-slate-800 shadow-lg text-white">
          <CardContent className="pt-5 flex items-center justify-between">
            <div>
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Explanation Fallbacks</span>
              <strong className="text-lg font-bold text-rose-500 mt-1 block">{fallbackCount}</strong>
              <span className="text-[9px] text-slate-400 block">Offline recommendations served</span>
            </div>
            <AlertTriangle className="h-7 w-7 text-rose-500/20" />
          </CardContent>
        </Card>

        {/* AI tokens */}
        <Card className="bg-slate-950 border-slate-800 shadow-lg text-white">
          <CardContent className="pt-5 flex items-center justify-between">
            <div>
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">AI Token Usage</span>
              <strong className="text-lg font-bold text-teal-400 mt-1 block">{totalTokens.toLocaleString()}</strong>
              <span className="text-[9px] text-slate-400 block">In: {statsData?.core?.prompt_tokens?.toLocaleString() ?? 0} | Out: {statsData?.core?.completion_tokens?.toLocaleString() ?? 0}</span>
            </div>
            <BarChart3 className="h-7 w-7 text-teal-400/20" />
          </CardContent>
        </Card>

        {/* AI Cost */}
        <Card className="bg-slate-950 border-slate-800 shadow-lg text-white">
          <CardContent className="pt-5 flex items-center justify-between">
            <div>
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Estimated AI Cost</span>
              <strong className="text-lg font-bold text-white mt-1 block">${aiCost.toFixed(4)}</strong>
              <span className="text-[9px] text-teal-400 block">Estimated Groq cost</span>
            </div>
            <DollarSign className="h-7 w-7 text-teal-500/20" />
          </CardContent>
        </Card>
      </div>

      {/* Tabs and Details */}
      <Card className="bg-slate-950 border-slate-800 shadow-lg text-white">
        <CardHeader className="pb-3 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <CardTitle className="text-base font-bold text-white flex items-center gap-2">
              <Server className="w-5 h-5 text-teal-400" />
              Subsystem Diagnostic Terminal
            </CardTitle>
            <CardDescription className="text-xs text-slate-400 mt-1">
              Select a subsystem console to inspect caches, claim heartbeats, check the queue status, or check service health.
            </CardDescription>
          </div>
          {/* Tabs switch */}
          <div className="flex gap-1 bg-slate-900 rounded-lg p-1 border border-slate-800 self-start sm:self-auto">
            {(['health', 'cache', 'workers', 'queue'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`text-xs font-semibold px-3.5 py-1.5 rounded-md capitalize transition-all ${
                  activeTab === tab ? 'bg-teal-500 text-slate-950 font-bold shadow-sm' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          {/* Health Tab */}
          {activeTab === 'health' && (
            <div className="space-y-6">
              {healthLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-teal-400" />
                </div>
              ) : healthData ? (
                <div className="space-y-6">
                  {/* Status Banner */}
                  <div className={`p-4 rounded-lg flex items-center gap-3 border ${
                    healthData.status === 'healthy' 
                      ? 'bg-emerald-950/20 border-emerald-900 text-emerald-300' 
                      : 'bg-amber-950/20 border-amber-900 text-amber-300'
                  }`}>
                    {healthData.status === 'healthy' ? (
                      <CheckCircle className="h-6 w-6 text-emerald-400" />
                    ) : (
                      <AlertTriangle className="h-6 w-6 text-amber-400" />
                    )}
                    <div>
                      <p className="font-bold text-sm">System Health: {healthData.status?.toUpperCase() || 'UNKNOWN'}</p>
                      <p className="text-xs opacity-80 mt-0.5">All core lookup caches, background worker heartbeats, and database operations are actively operating.</p>
                    </div>
                  </div>

                  {/* Grid Gauges */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {[
                      { name: 'Database (MongoDB)', val: healthData.mongodb, icon: Database },
                      { name: 'Caching Layer', val: healthData.cache, icon: Layers },
                      { name: 'Background Workers', val: healthData.workers, icon: Cpu },
                      { name: 'AI Integration (Groq)', val: healthData.ai, icon: Sparkles }
                    ].map((item, idx) => (
                      <div key={idx} className="border border-slate-800 bg-slate-900/50 rounded-lg p-4 space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-slate-400 font-semibold">{item.name}</span>
                          <item.icon className="h-4 w-4 text-slate-500" />
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-bold">Status</span>
                          {getStatusBadge(item.val)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="text-center text-xs text-slate-500 py-10">Failed to load subsystem health indicators</p>
              )}
            </div>
          )}

          {/* Cache Tab */}
          {activeTab === 'cache' && (
            <div className="space-y-4">
              {cacheLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-teal-400" />
                </div>
              ) : cacheData ? (
                <div className="space-y-4">
                  {[
                    { label: 'Drug Normalization Lookup Cache', data: cacheData.lookup_cache, cls: 'border-emerald-950 bg-emerald-950/5' },
                    { label: 'Drug-Drug Interaction Matrix Cache', data: cacheData.interaction_cache, cls: 'border-violet-950 bg-violet-950/5' },
                    { label: 'AI Patient Explanations Cache', data: cacheData.explanation_cache, cls: 'border-teal-950 bg-teal-950/5' }
                  ].map((level, idx) => {
                    const ratio = level.data?.hit_ratio ?? 0.0
                    const pct = Math.round(ratio * 100)
                    return (
                      <div key={idx} className={`border border-slate-800 rounded-lg p-4 ${level.cls}`}>
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                          <strong className="text-sm text-slate-200">{level.label}</strong>
                          <div className="flex items-center gap-3 text-xs text-slate-400">
                            <span>Size: <strong>{level.data?.size ?? 0}</strong> entries</span>
                            <span>TTL: <strong>{((level.data?.ttl_seconds ?? 0) / 3600).toFixed(1)}h</strong></span>
                            <span className="text-teal-400 font-bold">{pct}% hit</span>
                          </div>
                        </div>
                        <div className="w-full bg-slate-900 border border-slate-800 rounded-full h-2.5 overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-teal-500 to-teal-400 rounded-full transition-all duration-500"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                        <div className="flex justify-between text-[10px] text-slate-400 mt-2 font-mono">
                          <span>Hits: {level.data?.hits ?? 0}</span>
                          <span>Misses: {level.data?.misses ?? 0}</span>
                        </div>
                      </div>
                    )
                  })}
                  <div className="flex items-center justify-between text-xs text-slate-400 pt-3 border-t border-slate-800">
                    <span>Total Invalidations Registered: <strong>{cacheData.total_invalidations ?? 0}</strong></span>
                    <span>Tracked Active Patients: <strong>{cacheData.tracked_patients ?? 0}</strong></span>
                  </div>
                </div>
              ) : (
                <p className="text-center text-xs text-slate-500 py-10">Failed to load cache sizing matrices</p>
              )}
            </div>
          )}

          {/* Workers Tab */}
          {activeTab === 'workers' && (
            <div className="space-y-4">
              {workerLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-teal-400" />
                </div>
              ) : workerData ? (
                <div className="space-y-4">
                  {/* Workers List */}
                  <div className="space-y-2">
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-wide">Heartbeats & Worker Health Registers</p>
                    {workerData.workers && workerData.workers.length > 0 ? (
                      workerData.workers.map((w: any, idx: number) => {
                        // find heartbeat if exists
                        const hb = workerData.heartbeats?.find((h: any) => h.worker_id === w.worker_id)
                        const lastSeenStr = hb?.last_seen 
                          ? new Date(hb.last_seen).toLocaleTimeString()
                          : 'Never'
                        return (
                          <div key={idx} className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs bg-slate-900 border border-slate-800 rounded px-4 py-3">
                            <div className="space-y-1">
                              <span className="font-mono text-slate-300 font-bold block">{w.worker_id}</span>
                              <span className="text-[10px] text-slate-400 block">Last heartbeat register seen: {lastSeenStr}</span>
                            </div>
                            <div className="flex items-center gap-3">
                              {w.current_job_id && (
                                <Badge className="bg-amber-950 border border-amber-800 text-amber-300 font-mono text-[10px]">
                                  Job: {w.current_job_id.slice(-8)}
                                </Badge>
                              )}
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                w.is_active ? 'bg-emerald-950 text-emerald-400 border border-emerald-900' : 'bg-slate-800 text-slate-400'
                              }`}>
                                {w.is_active ? 'PROCESSING' : 'IDLE'}
                              </span>
                            </div>
                          </div>
                        )
                      })
                    ) : (
                      <p className="text-xs text-slate-500 italic py-4">No workers connected to scheduler pool.</p>
                    )}
                  </div>
                </div>
              ) : (
                <p className="text-center text-xs text-slate-500 py-10">Failed to claim worker registry status</p>
              )}
            </div>
          )}

          {/* Queue Tab */}
          {activeTab === 'queue' && (
            <div className="space-y-4">
              {workerLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-teal-400" />
                </div>
              ) : workerData ? (
                <div className="space-y-4">
                  <p className="text-xs font-bold text-slate-400 uppercase tracking-wide">Active / Pending Validation Queue Tasks ({workerData.active_jobs?.length ?? 0})</p>
                  
                  {workerData.active_jobs && workerData.active_jobs.length > 0 ? (
                    <div className="overflow-x-auto border border-slate-800 rounded">
                      <table className="w-full text-left text-xs text-slate-300">
                        <thead>
                          <tr className="bg-slate-900 text-slate-400 uppercase font-semibold border-b border-slate-800">
                            <th className="p-3">Job ID</th>
                            <th className="p-3">Patient ID</th>
                            <th className="p-3">Priority</th>
                            <th className="p-3 text-center">Retry</th>
                            <th className="p-3">Status</th>
                            <th className="p-3">Created At</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800 font-mono">
                          {workerData.active_jobs.map((job: any) => (
                            <tr key={job._id} className="hover:bg-slate-900/50">
                              <td className="p-3 font-semibold text-slate-200">{job._id.slice(-8)}</td>
                              <td className="p-3 text-slate-400">{job.patient_id?.slice(-8) || job.patient_id}</td>
                              <td className="p-3">
                                <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase ${
                                  job.priority === 'high' ? 'bg-rose-950 text-rose-400 border border-rose-900' : 'bg-slate-800 text-slate-400'
                                }`}>
                                  {job.priority}
                                </span>
                              </td>
                              <td className="p-3 text-center">{job.retry_count} / {job.max_retries}</td>
                              <td className="p-3 capitalize">{job.status}</td>
                              <td className="p-3 text-[10px] text-slate-400">
                                {job.created_at ? new Date(job.created_at).toLocaleTimeString() : 'N/A'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="text-center py-10 border border-dashed border-slate-800 rounded bg-slate-950/20 text-slate-500 text-xs">
                      ✓ Background queue is empty — all patient records synchronized
                    </div>
                  )}

                  {/* Telemetry details */}
                  {statsData?.background?.throughput && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-3 border-t border-slate-800 text-xs">
                      <div className="bg-slate-900/30 p-3 rounded border border-slate-800 text-center">
                        <span className="text-slate-400 block text-[10px] uppercase">Completed (Hour)</span>
                        <strong className="text-base text-slate-200 mt-1 block">{statsData.background.throughput.jobs_completed_per_hour}</strong>
                      </div>
                      <div className="bg-slate-900/30 p-3 rounded border border-slate-800 text-center">
                        <span className="text-slate-400 block text-[10px] uppercase">Total Completed</span>
                        <strong className="text-base text-slate-200 mt-1 block">{statsData.background.throughput.total_completed}</strong>
                      </div>
                      <div className="bg-slate-900/30 p-3 rounded border border-slate-800 text-center">
                        <span className="text-slate-400 block text-[10px] uppercase">Avg Queue Wait</span>
                        <strong className="text-base text-slate-200 mt-1 block">{statsData.background.throughput.avg_queue_wait_ms?.toFixed(1) || 0}ms</strong>
                      </div>
                      <div className="bg-slate-900/30 p-3 rounded border border-slate-800 text-center">
                        <span className="text-slate-400 block text-[10px] uppercase">Avg Exec Duration</span>
                        <strong className="text-base text-slate-200 mt-1 block">{statsData.background.throughput.avg_execution_latency_ms?.toFixed(1) || 0}ms</strong>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-center text-xs text-slate-500 py-10">Failed to load queue details</p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Core Block and Override Counters Row */}
      {statsData?.core && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="bg-slate-950 border-slate-800 shadow-lg text-white">
            <CardContent className="pt-5 flex items-center justify-between">
              <div>
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Blocked Patient Reminders</span>
                <strong className="text-2xl font-black text-rose-500 mt-1 block">
                  {statsData.core.reminder_blocks ?? 0}
                </strong>
                <span className="text-[9px] text-slate-400 block">Critical drug-drug interactions intercepted in reminders</span>
              </div>
              <AlertTriangle className="h-8 w-8 text-rose-500/20" />
            </CardContent>
          </Card>

          <Card className="bg-slate-950 border-slate-800 shadow-lg text-white">
            <CardContent className="pt-5 flex items-center justify-between">
              <div>
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Prescription Overrides Authorized</span>
                <strong className="text-2xl font-black text-teal-400 mt-1 block">
                  {statsData.core.prescription_overrides ?? 0}
                </strong>
                <span className="text-[9px] text-slate-400 block">Authorized clinical overrides registered in logs</span>
              </div>
              <CheckCircle className="h-8 w-8 text-teal-400/20" />
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
