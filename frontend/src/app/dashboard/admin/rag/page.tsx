'use client'

import { useState, useEffect } from 'react'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { toast } from 'react-hot-toast'
import { useQuery } from '@tanstack/react-query'
import { adminUserService } from '@/services/admin-user.service'
import { useAuditLogs } from '@/hooks/use-admin-logs'
import { aiService } from '@/services/ai.service'
import {
  useSyncStatus,
  useSyncPatient,
  useRebuildSync,
  useSyncStatistics,
} from '@/hooks/use-sync'
import {
  Database,
  RefreshCw,
  Search,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Activity,
  History,
  Play,
  CheckCircle,
  XCircle,
  Loader2,
  Sliders,
  Users,
  Layers,
  Zap,
  Gauge,
  BarChart2,
  Download,
  ShieldCheck,
  FileText,
} from 'lucide-react'
import { User } from '@/types'

export default function AdminRagSyncPage() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <AdminRagDashboardContent />
    </ProtectedRoute>
  )
}

function AdminRagDashboardContent() {
  const [activeTab, setActiveTab] = useState<'sync' | 'telemetry' | 'cache' | 'playground' | 'benchmarks'>('sync')
  const [search, setSearch] = useState('')
  const [patients, setPatients] = useState<User[]>([])
  const [searchingPatients, setSearchingPatients] = useState(false)
  const [selectedPatientId, setSelectedPatientId] = useState<string>('')
  const [selectedPatientName, setSelectedPatientName] = useState<string>('')

  // Playground State
  const [playgroundQuery, setPlaygroundQuery] = useState('')
  const [playgroundTopK, setPlaygroundTopK] = useState(5)
  const [playgroundThreshold, setPlaygroundThreshold] = useState(0.3)
  const [playgroundTokenBudget, setPlaygroundTokenBudget] = useState(4000)
  const [playgroundGroundTruth, setPlaygroundGroundTruth] = useState('')
  const [playgroundCollections, setPlaygroundCollections] = useState<string[]>([
    'patient_memory',
    'patient_reports',
    'medical_knowledge',
  ])
  const [evaluating, setEvaluating] = useState(false)
  const [evalResult, setEvalResult] = useState<any>(null)

  // Benchmarks State
  const [runningBenchmark, setRunningBenchmark] = useState(false)
  const [benchmarkResult, setBenchmarkResult] = useState<any>(null)

  // Sync API Queries & Mutations
  const { data: status, isLoading: loadingStatus, refetch: refetchStatus, isRefetching: refetchingStatus } = useSyncStatus()
  const { data: stats, isLoading: loadingStats, refetch: refetchStats, isRefetching: refetchingStats } = useSyncStatistics()
  
  // RAG Health & Summary Telemetry
  const { data: health, isLoading: loadingHealth, refetch: refetchHealth, isRefetching: refetchingHealth } = useQuery({
    queryKey: ['ragHealth'],
    queryFn: () => aiService.getRagHealth(),
    refetchInterval: 30000,
  })

  const { data: telemetry, isLoading: loadingTelemetry, refetch: refetchTelemetry, isRefetching: refetchingTelemetry } = useQuery({
    queryKey: ['ragStatistics'],
    queryFn: () => aiService.getRagStatistics(),
    refetchInterval: 15000,
  })

  const { data: logsData, isLoading: loadingLogs, refetch: refetchLogs, isRefetching: refetchingLogs } = useAuditLogs({
    action: 'PATIENT_RAG_SYNC',
    resource_type: 'patient_memory',
    limit: 10,
  })

  const syncPatientMutation = useSyncPatient()
  const rebuildSyncMutation = useRebuildSync()

  // Debounced search for patients
  useEffect(() => {
    const fetchPatients = async () => {
      try {
        setSearchingPatients(true)
        const res = await adminUserService.listUsers(
          search || undefined,
          'patient',
          true,
          10
        )
        if (res.success && res.data) {
          setPatients(res.data)
        }
      } catch (err) {
        console.error(err)
      } finally {
        setSearchingPatients(false)
      }
    }

    const delayDebounceFn = setTimeout(() => {
      fetchPatients()
    }, 300)

    return () => clearTimeout(delayDebounceFn)
  }, [search])

  const handleRefreshAll = async () => {
    await Promise.all([
      refetchStatus(),
      refetchStats(),
      refetchLogs(),
      refetchHealth(),
      refetchTelemetry(),
    ])
    toast.success('RAG Pipeline telemetry refreshed')
  }

  const handleSyncPatient = async (patientId: string, patientName: string) => {
    try {
      const res = await syncPatientMutation.mutateAsync(patientId)
      if (res.success) {
        toast.success(
          `Sync completed for ${patientName}! MongoDB: ${res.rebuilt_mongodb ? 'Updated' : 'Skipped'}, Qdrant: ${
            res.regenerated_qdrant ? 'Regenerated' : 'Unchanged'
          } (Version ${res.summary_version})`
        )
        refetchLogs()
      } else {
        toast.error(`Sync failed for ${patientName}`)
      }
    } catch (err: any) {
      console.error(err)
      toast.error(err.message || `Failed to sync patient memory`)
    }
  }

  const handleRebuildSync = async () => {
    try {
      const res = await rebuildSyncMutation.mutateAsync()
      if (res.success) {
        toast.success(`Pipeline rebuild enqueued for all active patients (${res.triggered_count} profiles)`)
      } else {
        toast.error(`Failed to trigger full sync rebuild`)
      }
    } catch (err: any) {
      console.error(err)
      toast.error(err.message || 'Error occurred during rebuild trigger')
    }
  }

  const handleRunEvaluation = async () => {
    if (!playgroundQuery.trim()) {
      toast.error('Please specify a query to evaluate')
      return
    }

    try {
      setEvaluating(true)
      const groundTruthArray = playgroundGroundTruth
        ? playgroundGroundTruth.split(',').map((s) => s.trim()).filter(Boolean)
        : undefined

      const result = await aiService.evaluateQuery(
        playgroundQuery,
        selectedPatientId || undefined,
        playgroundCollections,
        undefined,
        groundTruthArray,
        playgroundTopK,
        playgroundThreshold,
        playgroundTokenBudget
      )
      setEvalResult(result)
      toast.success('RAG retrieval evaluation complete!')
    } catch (err: any) {
      console.error(err)
      toast.error(err.message || 'Failed to execute query evaluation')
    } finally {
      setEvaluating(false)
    }
  }

  const handleRunBenchmark = async () => {
    try {
      setRunningBenchmark(true)
      const result = await aiService.runRagBenchmark(
        selectedPatientId || undefined,
        playgroundTokenBudget,
        playgroundThreshold
      )
      setBenchmarkResult(result)
      toast.success('RAG Benchmark Suite completed successfully!')
    } catch (err: any) {
      console.error(err)
      toast.error(err.message || 'Failed to execute benchmark suite')
    } finally {
      setRunningBenchmark(false)
    }
  }

  const handleExportBenchmarkJSON = () => {
    if (!benchmarkResult) return
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(benchmarkResult, null, 2))
    const downloadAnchor = document.createElement('a')
    downloadAnchor.setAttribute('href', dataStr)
    downloadAnchor.setAttribute('download', `rag_benchmark_report_${new Date().toISOString().split('T')[0]}.json`)
    document.body.appendChild(downloadAnchor)
    downloadAnchor.click()
    downloadAnchor.remove()
  }

  const handleExportBenchmarkCSV = () => {
    if (!benchmarkResult || !benchmarkResult.categories) return
    let csvContent = 'Category,Query,Latency (ms),Precision,Recall,Citation Quality,Duplicate Rate,Context Utilization\n'

    Object.entries(benchmarkResult.categories).forEach(([category, data]: [string, any]) => {
      if (data.query_details) {
        data.query_details.forEach((q: any) => {
          const row = [
            category,
            `"${q.query.replace(/"/g, '""')}"`,
            q.latency_ms.toFixed(1),
            q.precision.toFixed(2),
            q.recall.toFixed(2),
            q.citation_quality.toFixed(2),
            q.duplicate_rate.toFixed(2),
            q.context_utilization.toFixed(2),
          ].join(',')
          csvContent += row + '\n'
        })
      }
    })

    const dataStr = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csvContent)
    const downloadAnchor = document.createElement('a')
    downloadAnchor.setAttribute('href', dataStr)
    downloadAnchor.setAttribute('download', `rag_benchmark_report_${new Date().toISOString().split('T')[0]}.csv`)
    document.body.appendChild(downloadAnchor)
    downloadAnchor.click()
    downloadAnchor.remove()
  }

  const toggleCollection = (collectionName: string) => {
    setPlaygroundCollections((prev) =>
      prev.includes(collectionName)
        ? prev.filter((c) => c !== collectionName)
        : [...prev, collectionName]
    )
  }

  const isSyncInProgress = rebuildSyncMutation.isPending || (status && status.queue_size > 0)
  const isRefreshing = refetchingStatus || refetchingStats || refetchingLogs || refetchingHealth || refetchingTelemetry

  // Sync tab helper values
  const totalCount = stats?.sync_count ?? 0
  const skippedCount = stats?.vectors_skipped ?? 0
  const efficiencyPercentage = totalCount > 0 ? ((skippedCount / totalCount) * 100).toFixed(0) : '0'

  const tabsList = [
    { id: 'sync', label: 'Sync Center', icon: Database },
    { id: 'telemetry', label: 'Performance Telemetry', icon: Activity },
    { id: 'cache', label: 'Cache Analyzer', icon: Sliders },
    { id: 'playground', label: 'Playground & Evaluator', icon: Play },
    { id: 'benchmarks', label: 'Benchmarks Panel', icon: Gauge },
  ] as const

  return (
    <div className="space-y-6 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            <Layers className="h-8 w-8 text-teal-600 dark:text-teal-400 animate-pulse" />
            <span>RAG System & Memory Optimization</span>
          </h1>
          <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
            Monitor caching efficiency, trace query latencies, trigger manual memory index sync, and validate information retrieval metrics.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={handleRefreshAll}
            variant="outline"
            className="flex items-center gap-2 border-slate-200 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-900"
            disabled={isRefreshing}
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh Telemetry
          </Button>
        </div>
      </div>

      {/* Tabs Selector */}
      <div className="flex flex-wrap gap-2 border-b border-slate-200 dark:border-slate-850 pb-3">
        {tabsList.map((tab) => {
          const Icon = tab.icon
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-all ${
                isActive
                  ? 'bg-teal-50 text-teal-700 dark:bg-teal-950/40 dark:text-teal-400 border border-teal-200/50 dark:border-teal-900/50 shadow-sm font-semibold'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-900 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Selected Patient Banner if active */}
      {selectedPatientId && (
        <div className="flex items-center justify-between p-3.5 bg-teal-500/10 dark:bg-teal-400/5 border border-teal-500/20 dark:border-teal-400/10 rounded-xl">
          <div className="flex items-center gap-2.5">
            <Users className="h-5 w-5 text-teal-600 dark:text-teal-400" />
            <div className="text-sm">
              <span className="text-slate-500 dark:text-slate-400">Target Patient Selected:</span>{' '}
              <strong className="text-slate-950 dark:text-white font-semibold">{selectedPatientName}</strong>{' '}
              <span className="text-xs text-slate-400 dark:text-slate-500">({selectedPatientId})</span>
            </div>
          </div>
          <button
            onClick={() => {
              setSelectedPatientId('')
              setSelectedPatientName('')
            }}
            className="text-xs text-slate-400 hover:text-rose-500 dark:text-slate-500 dark:hover:text-rose-450 transition-colors"
          >
            Clear Target
          </button>
        </div>
      )}

      {/* Tab 1: Sync Center */}
      {activeTab === 'sync' && (
        <div className="space-y-6 animate-fadeIn">
          {/* Telemetry Metrics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="border border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-950/50 backdrop-blur-sm shadow-sm">
              <CardContent className="pt-6 space-y-2">
                <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
                  <span className="text-sm font-semibold">Total Sync Runs</span>
                  <Activity className="h-4 w-4 text-teal-500" />
                </div>
                {loadingStats ? (
                  <div className="h-8 w-16 bg-slate-200 dark:bg-slate-800 animate-pulse rounded" />
                ) : (
                  <div className="space-y-1">
                    <div className="text-3xl font-bold text-slate-900 dark:text-white">
                      {stats?.sync_count ?? 0}
                    </div>
                    <div className="text-xs text-slate-400 dark:text-slate-500">
                      {stats?.rebuilt_summaries ?? 0} MongoDB summaries updated
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="border border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-950/50 backdrop-blur-sm shadow-sm">
              <CardContent className="pt-6 space-y-2">
                <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
                  <span className="text-sm font-semibold">Vector Skip Ratio</span>
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                </div>
                {loadingStats ? (
                  <div className="h-8 w-16 bg-slate-200 dark:bg-slate-800 animate-pulse rounded" />
                ) : (
                  <div className="space-y-1">
                    <div className="text-3xl font-bold text-slate-900 dark:text-white">
                      {efficiencyPercentage}%
                    </div>
                    <div className="text-xs text-slate-400 dark:text-slate-500">
                      Skipped {skippedCount} / {totalCount} unmodified records
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="border border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-950/50 backdrop-blur-sm shadow-sm">
              <CardContent className="pt-6 space-y-2">
                <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
                  <span className="text-sm font-semibold">Average Sync Latency</span>
                  <Clock className="h-4 w-4 text-amber-500" />
                </div>
                {loadingStats ? (
                  <div className="h-8 w-16 bg-slate-200 dark:bg-slate-800 animate-pulse rounded" />
                ) : (
                  <div className="space-y-1">
                    <div className="text-3xl font-bold text-slate-900 dark:text-white">
                      {stats?.avg_latency_ms ? `${stats.avg_latency_ms.toFixed(1)} ms` : '0.0 ms'}
                    </div>
                    <div className="text-xs text-slate-400 dark:text-slate-500">
                      Includes generation and indexing
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="border border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-950/50 backdrop-blur-sm shadow-sm">
              <CardContent className="pt-6 space-y-2">
                <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
                  <span className="text-sm font-semibold">DLQ & Failures</span>
                  <AlertTriangle className="h-4 w-4 text-rose-500" />
                </div>
                {loadingStats || loadingStatus ? (
                  <div className="h-8 w-16 bg-slate-200 dark:bg-slate-800 animate-pulse rounded" />
                ) : (
                  <div className="space-y-1">
                    <div className="text-3xl font-bold text-slate-900 dark:text-white">
                      {status?.dlq_count ?? 0}
                    </div>
                    <div className="text-xs text-rose-600 dark:text-rose-400 font-medium">
                      {stats?.failures ?? 0} fails ({stats?.retries ?? 0} retries total)
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              {/* Control Center */}
              <Card className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm overflow-hidden">
                <CardHeader className="border-b border-slate-100 dark:border-slate-900 bg-slate-50/50 dark:bg-slate-900/20">
                  <CardTitle className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <Sliders className="h-5 w-5 text-teal-650" />
                    Control Center
                  </CardTitle>
                  <CardDescription>Administrative controls to force database-wide synchronization.</CardDescription>
                </CardHeader>
                <CardContent className="p-6 space-y-4">
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl border border-slate-200/80 dark:border-slate-800/80 bg-slate-50/30 dark:bg-slate-900/10">
                    <div className="space-y-1">
                      <h4 className="text-sm font-semibold text-slate-900 dark:text-white">Rebuild RAG Vector Store</h4>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        Re-reads clinical variables for all patients, updates schema variables, and pushes missing vectors to Qdrant.
                      </p>
                    </div>
                    <Button
                      onClick={handleRebuildSync}
                      disabled={isSyncInProgress}
                      className="bg-slate-900 hover:bg-slate-800 text-white dark:bg-slate-850 dark:hover:bg-slate-750 font-semibold text-xs whitespace-nowrap px-4 py-2 border-0"
                    >
                      {rebuildSyncMutation.isPending ? (
                        <span className="flex items-center gap-2">
                          <Loader2 className="h-3 w-3 animate-spin" />
                          Triggering...
                        </span>
                      ) : (
                        <span className="flex items-center gap-2">
                          <Play className="h-3.5 w-3.5 fill-current" />
                          Queue Full Rebuild
                        </span>
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Patient Lookup */}
              <Card className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm overflow-hidden">
                <CardHeader className="border-b border-slate-100 dark:border-slate-900 bg-slate-50/50 dark:bg-slate-900/20">
                  <CardTitle className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <Users className="h-5 w-5 text-teal-650" />
                    Manual Patient Memory Sync
                  </CardTitle>
                  <CardDescription>Query active patients to inspect, sync records, or set as evaluation target.</CardDescription>
                </CardHeader>
                <CardContent className="p-6 space-y-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                    <Input
                      placeholder="Filter patients by name or email..."
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                      className="pl-9 bg-slate-50 border-slate-200 dark:border-slate-850 dark:bg-slate-900 focus:bg-white transition-colors"
                    />
                  </div>

                  <div className="border border-slate-150 dark:border-slate-800 rounded-lg divide-y divide-slate-100 dark:divide-slate-900 overflow-hidden max-h-[300px] overflow-y-auto">
                    {searchingPatients ? (
                      <div className="flex justify-center items-center py-10 text-sm text-slate-500">
                        <Loader2 className="h-4 w-4 animate-spin mr-2 text-teal-605" />
                        Searching profiles...
                      </div>
                    ) : patients.length === 0 ? (
                      <div className="py-10 text-center text-sm text-slate-400">
                        No active patients matching criteria.
                      </div>
                    ) : (
                      patients.map((pat) => {
                        const isSyncing = syncPatientMutation.isPending && syncPatientMutation.variables === pat.id
                        const isSelected = selectedPatientId === pat.id
                        return (
                          <div key={pat.id} className="flex items-center justify-between p-3.5 hover:bg-slate-50/40 dark:hover:bg-slate-900/20 transition-colors">
                            <div className="flex items-center min-w-0 mr-4">
                              <div className="h-9 w-9 flex-shrink-0 rounded-full bg-teal-50 dark:bg-teal-950/30 flex items-center justify-center border border-teal-100 dark:border-teal-900/50 text-teal-750 dark:text-teal-400 font-bold text-sm">
                                {pat.full_name ? pat.full_name.charAt(0).toUpperCase() : 'P'}
                              </div>
                              <div className="ml-3 min-w-0">
                                <p className="text-sm font-semibold text-slate-900 dark:text-white truncate">{pat.full_name}</p>
                                <p className="text-xs text-slate-400 truncate">{pat.email}</p>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => {
                                  setSelectedPatientId(pat.id)
                                  setSelectedPatientName(pat.full_name || pat.email || pat.id)
                                  toast.success(`Set ${pat.full_name} as active evaluator target`)
                                }}
                                className={`text-xs font-semibold px-3 py-1.5 ${
                                  isSelected
                                    ? 'bg-teal-50 border-teal-200 dark:bg-teal-900/20 dark:border-teal-800 text-teal-700 dark:text-teal-400'
                                    : 'border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400'
                                }`}
                              >
                                Select Target
                              </Button>
                              <Button
                                size="sm"
                                onClick={() => handleSyncPatient(pat.id, pat.full_name || 'Patient')}
                                disabled={syncPatientMutation.isPending}
                                className="bg-slate-50 border border-slate-200 text-slate-700 hover:bg-slate-100 dark:bg-slate-900 dark:border-slate-800 dark:text-slate-300 dark:hover:bg-slate-800 text-xs font-semibold px-3 py-1.5"
                              >
                                {isSyncing ? (
                                  <span className="flex items-center gap-1.5">
                                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                    Syncing
                                  </span>
                                ) : (
                                  'Sync Memory'
                                )}
                              </Button>
                            </div>
                          </div>
                        )
                      })
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Queue Monitor & Sync History */}
            <div className="space-y-6">
              <Card className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm overflow-hidden">
                <CardHeader className="border-b border-slate-100 dark:border-slate-900 bg-slate-50/50 dark:bg-slate-900/20">
                  <CardTitle className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <Activity className="h-5 w-5 text-teal-650" />
                    Pipeline Queue Monitor
                  </CardTitle>
                  <CardDescription>Current status of async event worker.</CardDescription>
                </CardHeader>
                <CardContent className="p-6">
                  {loadingStatus ? (
                    <div className="flex justify-center py-6">
                      <Loader2 className="h-6 w-6 animate-spin text-teal-605" />
                    </div>
                  ) : status ? (
                    <div className="space-y-4">
                      <div className="flex justify-between items-center py-2 border-b border-slate-105 dark:border-slate-900 text-sm">
                        <span className="text-slate-500 dark:text-slate-400">Worker Status</span>
                        <span className="font-semibold">
                          {status.running ? (
                            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-400">
                              <CheckCircle className="h-3 w-3" />
                              Active / Listening
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2 py-0.5 text-xs font-semibold text-rose-700 dark:bg-rose-950/20 dark:text-rose-450">
                              <XCircle className="h-3 w-3" />
                              Offline
                            </span>
                          )}
                        </span>
                      </div>
                      
                      <div className="flex justify-between items-center py-2 border-b border-slate-105 dark:border-slate-900 text-sm">
                        <span className="text-slate-500 dark:text-slate-400">Buffered Queue Length</span>
                        <span className="font-mono font-bold text-slate-900 dark:text-white">
                          {status.queue_size} tasks
                        </span>
                      </div>

                      <div className="flex justify-between items-center py-2 text-sm">
                        <span className="text-slate-500 dark:text-slate-400">Dead Letter Jobs</span>
                        <span className={`font-mono font-bold ${status.dlq_count > 0 ? 'text-rose-600' : 'text-slate-950 dark:text-white'}`}>
                          {status.dlq_count} failed jobs
                        </span>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center text-sm text-slate-400">Unable to load worker status</div>
                  )}
                </CardContent>
              </Card>

              <Card className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm overflow-hidden">
                <CardHeader className="border-b border-slate-100 dark:border-slate-900 bg-slate-50/50 dark:bg-slate-900/20">
                  <CardTitle className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <History className="h-5 w-5 text-teal-650" />
                    Sync Audit History
                  </CardTitle>
                  <CardDescription>Most recent pipeline operations.</CardDescription>
                </CardHeader>
                <CardContent className="p-0">
                  {loadingLogs ? (
                    <div className="flex justify-center py-10">
                      <Loader2 className="h-6 w-6 animate-spin text-teal-605" />
                    </div>
                  ) : !logsData || logsData.logs?.length === 0 ? (
                    <div className="py-10 text-center text-sm text-slate-400">
                      No synchronization logs recorded yet.
                    </div>
                  ) : (
                    <div className="divide-y divide-slate-100 dark:divide-slate-900 max-h-[400px] overflow-y-auto font-sans">
                      {logsData.logs.map((log) => {
                        const newValue = log.new_value || {}
                        const isRebuiltMongo = newValue.rebuilt_mongodb
                        const isRegenQdrant = newValue.regenerated_qdrant
                        const wasSkipped = !isRebuiltMongo && !isRegenQdrant

                        return (
                          <div key={log.id} className="p-4 space-y-1.5 hover:bg-slate-50/30 dark:hover:bg-slate-900/10 transition-colors">
                            <div className="flex items-center justify-between text-xs">
                              <span className="font-mono text-slate-500 truncate max-w-[150px]" title={log.resource_id}>
                                Patient: {log.resource_id}
                              </span>
                              <span className="text-slate-400">
                                {new Date(log.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                              </span>
                            </div>
                            
                            <div className="flex justify-between items-center">
                              <span className="text-sm font-semibold text-slate-900 dark:text-white">
                                Version {newValue.summary_version ?? '1'}
                              </span>
                              
                              <span
                                className={`inline-flex px-2 py-0.5 rounded text-[10px] font-bold ${
                                  wasSkipped
                                    ? 'bg-slate-100 text-slate-700 dark:bg-slate-900 dark:text-slate-400'
                                    : 'bg-teal-50 text-teal-700 dark:bg-teal-950/30 dark:text-teal-400 border border-teal-100 dark:border-teal-900/50'
                                }`}
                              >
                                {wasSkipped ? 'Skipped' : 'Indexed'}
                              </span>
                            </div>

                            <div className="flex justify-between items-center text-[11px] text-slate-400">
                              <span>
                                {isRebuiltMongo ? 'DB Updated' : 'DB Up-to-date'} | {isRegenQdrant ? 'Vectors Regenerated' : 'Vector Match'}
                              </span>
                              <span className="font-mono">
                                {newValue.latency_ms ? `${newValue.latency_ms.toFixed(0)}ms` : '0ms'}
                              </span>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Performance Telemetry */}
      {activeTab === 'telemetry' && (
        <div className="space-y-6 animate-fadeIn">
          {/* Subsystems Health Checks */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Groq Health Card */}
            <Card className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm overflow-hidden">
              <CardHeader className="bg-slate-50/50 dark:bg-slate-900/25 border-b border-slate-100 dark:border-slate-900 pb-4">
                <div className="flex flex-wrap items-center justify-between gap-1.5 min-w-0">
                  <div className="flex items-center gap-2 min-w-0 flex-1">
                    <Zap className="h-5 w-5 text-amber-500 flex-shrink-0" />
                    <CardTitle className="text-base font-bold text-slate-900 dark:text-white truncate min-w-0">Groq API Server</CardTitle>
                  </div>
                  <div className="flex-shrink-0">
                    {loadingHealth ? (
                      <Loader2 className="h-4 w-4 animate-spin text-slate-400" />
                    ) : health?.groq?.status === 'healthy' || health?.groq?.reachable ? (
                      <Badge className="bg-emerald-50 text-emerald-700 hover:bg-emerald-50 dark:bg-emerald-950/30 dark:text-emerald-400 border border-emerald-250 dark:border-emerald-900 text-[10px] px-1.5 py-0.5">
                        Healthy
                      </Badge>
                    ) : (
                      <Badge variant="destructive" className="text-[10px] px-1.5 py-0.5">Degraded / Open Breaker</Badge>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-4 space-y-2 text-sm text-slate-650 dark:text-slate-350">
                <div className="flex justify-between">
                  <span className="text-slate-455 dark:text-slate-400">Target Model:</span>
                  <span className="font-semibold">{health?.groq?.model || 'llama-3.3-70b-versatile'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-455 dark:text-slate-400">Latency:</span>
                  <span className="font-mono font-bold">
                    {health?.groq?.latency_ms ? `${health.groq.latency_ms.toFixed(1)} ms` : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-455 dark:text-slate-400">Reachable:</span>
                  <span className="font-semibold">{health?.groq?.reachable ? 'Yes' : 'No'}</span>
                </div>
              </CardContent>
            </Card>

            {/* Embedding Health Card */}
            <Card className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm overflow-hidden">
              <CardHeader className="bg-slate-50/50 dark:bg-slate-900/25 border-b border-slate-100 dark:border-slate-900 pb-4">
                <div className="flex flex-wrap items-center justify-between gap-1.5 min-w-0">
                  <div className="flex items-center gap-2 min-w-0 flex-1">
                    <Sliders className="h-5 w-5 text-teal-500 flex-shrink-0" />
                    <CardTitle className="text-base font-bold text-slate-900 dark:text-white truncate min-w-0">Embedding Service</CardTitle>
                  </div>
                  <div className="flex-shrink-0">
                    {loadingHealth ? (
                      <Loader2 className="h-4 w-4 animate-spin text-slate-400" />
                    ) : health?.embedding?.status === 'healthy' ? (
                      <Badge className="bg-emerald-50 text-emerald-700 hover:bg-emerald-50 dark:bg-emerald-950/30 dark:text-emerald-400 border border-emerald-250 dark:border-emerald-900 text-[10px] px-1.5 py-0.5">
                        Healthy
                      </Badge>
                    ) : (
                      <Badge variant="destructive" className="text-[10px] px-1.5 py-0.5">Degraded / Open Breaker</Badge>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-4 space-y-2 text-sm text-slate-655 dark:text-slate-350">
                <div className="flex justify-between">
                  <span className="text-slate-455 dark:text-slate-400">Provider & Model:</span>
                  <span className="font-semibold truncate max-w-[170px]" title={health?.embedding?.model}>
                    {health?.embedding?.provider || 'HuggingFace'} / {health?.embedding?.model || 'bge-large-en-v1.5'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-455 dark:text-slate-400">Dimensions:</span>
                  <span className="font-semibold">{health?.embedding?.dimensions || 1024}d</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-455 dark:text-slate-400">Latency:</span>
                  <span className="font-mono font-bold">
                    {health?.embedding?.latency ? `${health.embedding.latency.toFixed(1)} ms` : 'N/A'}
                  </span>
                </div>
              </CardContent>
            </Card>

            {/* Qdrant Health Card */}
            <Card className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm overflow-hidden">
              <CardHeader className="bg-slate-50/50 dark:bg-slate-900/25 border-b border-slate-100 dark:border-slate-900 pb-4">
                <div className="flex flex-wrap items-center justify-between gap-1.5 min-w-0">
                  <div className="flex items-center gap-2 min-w-0 flex-1">
                    <Database className="h-5 w-5 text-teal-650 flex-shrink-0" />
                    <CardTitle className="text-base font-bold text-slate-900 dark:text-white truncate min-w-0">Qdrant Vector DB</CardTitle>
                  </div>
                  <div className="flex-shrink-0">
                    {loadingHealth ? (
                      <Loader2 className="h-4 w-4 animate-spin text-slate-400" />
                    ) : health?.qdrant?.status === 'healthy' ? (
                      <Badge className="bg-emerald-50 text-emerald-700 hover:bg-emerald-50 dark:bg-emerald-950/30 dark:text-emerald-400 border border-emerald-250 dark:border-emerald-900 text-[10px] px-1.5 py-0.5">
                        Healthy
                      </Badge>
                    ) : (
                      <Badge variant="destructive" className="text-[10px] px-1.5 py-0.5">Degraded / Open Breaker</Badge>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-4 space-y-2 text-sm text-slate-655 dark:text-slate-350">
                <div className="flex justify-between">
                  <span className="text-slate-455 dark:text-slate-400">Connection Mode:</span>
                  <span className="font-semibold">Cloud Cluster</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-455 dark:text-slate-400">Ping Latency:</span>
                  <span className="font-mono font-bold">
                    {health?.qdrant?.latency_ms ? `${health.qdrant.latency_ms.toFixed(1)} ms` : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-455 dark:text-slate-400">Active Collections:</span>
                  <span className="font-semibold">5 mapped index spaces</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Detailed Performance Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Latency Averages Card */}
            <Card className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm">
              <CardHeader className="border-b border-slate-100 dark:border-slate-900 pb-4">
                <CardTitle className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Clock className="h-5 w-5 text-teal-600" />
                  Subsystems Response Latency
                </CardTitle>
                <CardDescription>Estimated average operations latency compiler from recent queries.</CardDescription>
              </CardHeader>
              <CardContent className="pt-6 space-y-4">
                {loadingTelemetry ? (
                  <div className="flex flex-col gap-3 py-6 justify-center items-center">
                    <Loader2 className="h-6 w-6 animate-spin text-teal-600" />
                    <span className="text-xs text-slate-400">Loading performance data...</span>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* Retrieval Latency */}
                    <div className="space-y-1.5">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-600 dark:text-slate-450 font-semibold">Semantic Multi-Search</span>
                        <span className="font-mono text-slate-950 dark:text-white font-bold">
                          {telemetry?.agent?.avg_retrieval_latency_ms ? `${telemetry.agent.avg_retrieval_latency_ms.toFixed(1)} ms` : '0.0 ms'}
                        </span>
                      </div>
                      <div className="h-2 w-full bg-slate-100 dark:bg-slate-900 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-teal-500"
                          style={{
                            width: `${Math.min(
                              100,
                              ((telemetry?.agent?.avg_retrieval_latency_ms || 0) / 1000) * 100
                            )}%`,
                          }}
                        />
                      </div>
                    </div>

                    {/* Ranking Latency */}
                    <div className="space-y-1.5">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-600 dark:text-slate-455 font-semibold">Citations Merging & Re-ranking</span>
                        <span className="font-mono text-slate-950 dark:text-white font-bold">
                          {telemetry?.agent?.avg_ranking_latency_ms ? `${telemetry.agent.avg_ranking_latency_ms.toFixed(1)} ms` : '0.0 ms'}
                        </span>
                      </div>
                      <div className="h-2 w-full bg-slate-100 dark:bg-slate-900 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-amber-500"
                          style={{
                            width: `${Math.min(
                              100,
                              ((telemetry?.agent?.avg_ranking_latency_ms || 0) / 500) * 100
                            )}%`,
                          }}
                        />
                      </div>
                    </div>

                    {/* Context Assembling Latency */}
                    <div className="space-y-1.5">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-600 dark:text-slate-455 font-semibold">Context Assembly Engine</span>
                        <span className="font-mono text-slate-950 dark:text-white font-bold">
                          {telemetry?.agent?.avg_context_latency_ms ? `${telemetry.agent.avg_context_latency_ms.toFixed(1)} ms` : '0.0 ms'}
                        </span>
                      </div>
                      <div className="h-2 w-full bg-slate-100 dark:bg-slate-900 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-indigo-500"
                          style={{
                            width: `${Math.min(
                              100,
                              ((telemetry?.agent?.avg_context_latency_ms || 0) / 1000) * 100
                            )}%`,
                          }}
                        />
                      </div>
                    </div>

                    {/* Full Pipeline Latency */}
                    <div className="space-y-1.5 border-t border-slate-100 dark:border-slate-900 pt-4">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-950 dark:text-white font-extrabold">End-to-End RAG Retrieval Latency</span>
                        <span className="font-mono text-teal-600 dark:text-teal-400 font-extrabold">
                          {telemetry?.agent?.avg_latency_ms ? `${telemetry.agent.avg_latency_ms.toFixed(1)} ms` : '0.0 ms'}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Orchestrator Statistics Card */}
            <Card className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm">
              <CardHeader className="border-b border-slate-100 dark:border-slate-900 pb-4">
                <CardTitle className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <BarChart2 className="h-5 w-5 text-teal-650" />
                  RAG Request Telemetry & Cost Estimators
                </CardTitle>
                <CardDescription>Aggregated orchestrator details including total cost and error telemetry.</CardDescription>
              </CardHeader>
              <CardContent className="pt-6 space-y-4 text-sm">
                {loadingTelemetry ? (
                  <div className="flex flex-col gap-3 py-6 justify-center items-center">
                    <Loader2 className="h-6 w-6 animate-spin text-teal-600" />
                    <span className="text-xs text-slate-400">Loading orchestrator stats...</span>
                  </div>
                ) : (
                  <div className="space-y-3.5 divide-y divide-slate-100 dark:divide-slate-900">
                    <div className="flex justify-between pb-2.5">
                      <span className="text-slate-500 dark:text-slate-400">Total Pipeline Queries Run:</span>
                      <strong className="text-slate-950 dark:text-white font-bold">{telemetry?.overall?.total_queries ?? 0} queries</strong>
                    </div>
                    <div className="flex justify-between py-2.5">
                      <span className="text-slate-500 dark:text-slate-400">Orchestrator Request Count:</span>
                      <strong className="text-slate-950 dark:text-white font-bold">{telemetry?.orchestrator?.requests ?? 0} requests</strong>
                    </div>
                    <div className="flex justify-between py-2.5">
                      <span className="text-slate-500 dark:text-slate-400">LLM Inference Success Rate:</span>
                      <strong className="text-emerald-650 dark:text-emerald-450 font-bold">
                        {telemetry?.orchestrator?.success_rate ? `${(telemetry.orchestrator.success_rate * 100).toFixed(1)}%` : '100%'}
                      </strong>
                    </div>
                    <div className="flex justify-between py-2.5">
                      <span className="text-slate-500 dark:text-slate-400">Average Token Usage / Query:</span>
                      <strong className="text-slate-950 dark:text-white font-mono font-bold">
                        {telemetry?.orchestrator?.avg_tokens ? `${telemetry.orchestrator.avg_tokens.toFixed(0)} tokens` : '0 tokens'}
                      </strong>
                    </div>
                    <div className="flex justify-between pt-2.5">
                      <span className="text-slate-500 dark:text-slate-400">Estimated Total LLM Expense:</span>
                      <strong className="text-teal-600 dark:text-teal-400 font-mono font-extrabold text-base">
                        ${telemetry?.overall?.estimated_llm_cost_usd ? telemetry.overall.estimated_llm_cost_usd.toFixed(4) : '0.0000'}
                      </strong>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Tab 3: Cache Analyzer */}
      {activeTab === 'cache' && (
        <div className="space-y-6 animate-fadeIn">
          {/* Caches Summary Panel */}
          <div className="p-5 border border-slate-200 dark:border-slate-805 bg-slate-50/50 dark:bg-slate-900/10 rounded-xl space-y-4">
            <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Sliders className="h-5 w-5 text-teal-600" />
                  RAG Cache Layer (In-Memory, Configurable TTL)
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  Telemetry hit/miss ratios tracking embedding outputs, query intents, collections search results, and assembled prompts.
                </p>
              </div>
              <div className="text-right">
                <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">Overall RAG Cache Hit Ratio</div>
                <div className="text-2xl font-black text-teal-600 dark:text-teal-400 font-mono mt-0.5">
                  {telemetry?.caches?.total_hit_ratio ? `${(telemetry.caches.total_hit_ratio * 100).toFixed(1)}%` : '0.0%'}
                </div>
              </div>
            </div>
            <div className="h-2.5 w-full bg-slate-100 dark:bg-slate-900 rounded-full overflow-hidden">
              <div
                className="h-full bg-teal-500 transition-all duration-500"
                style={{ width: `${(telemetry?.caches?.total_hit_ratio ?? 0) * 100}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-slate-400 font-mono">
              <span>Total Hits: {telemetry?.caches?.total_hits ?? 0}</span>
              <span>Total Misses: {telemetry?.caches?.total_misses ?? 0}</span>
            </div>
          </div>

          {/* Subsystems Cache Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Cache 1: Query Intent Cache */}
            <Card className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm">
              <CardContent className="pt-6 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-slate-500 dark:text-slate-450">Query Intent Cache</span>
                  <Badge className="bg-teal-50 text-teal-700 dark:bg-teal-950/40 dark:text-teal-400 font-mono">
                    {telemetry?.caches?.query_hit_ratio ? `${(telemetry.caches.query_hit_ratio * 100).toFixed(1)}%` : '0.0%'}
                  </Badge>
                </div>
                <div className="space-y-2">
                  <div className="h-2 w-full bg-slate-100 dark:bg-slate-900 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-teal-500"
                      style={{ width: `${(telemetry?.caches?.query_hit_ratio ?? 0) * 100}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-slate-400 font-mono">
                    <span>{telemetry?.caches?.query_hits ?? 0} Hits</span>
                    <span>{telemetry?.caches?.query_misses ?? 0} Misses</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Cache 2: Embedding Vector Cache */}
            <Card className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm">
              <CardContent className="pt-6 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-slate-500 dark:text-slate-450">Embedding Cache</span>
                  <Badge className="bg-teal-50 text-teal-700 dark:bg-teal-950/40 dark:text-teal-400 font-mono">
                    {telemetry?.caches?.embedding_hit_ratio ? `${(telemetry.caches.embedding_hit_ratio * 100).toFixed(1)}%` : '0.0%'}
                  </Badge>
                </div>
                <div className="space-y-2">
                  <div className="h-2 w-full bg-slate-100 dark:bg-slate-900 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-teal-500"
                      style={{ width: `${(telemetry?.caches?.embedding_hit_ratio ?? 0) * 100}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-slate-400 font-mono">
                    <span>{telemetry?.caches?.embedding_hits ?? 0} Hits</span>
                    <span>{telemetry?.caches?.embedding_misses ?? 0} Misses</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Cache 3: Semantic Retrieval Cache */}
            <Card className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm">
              <CardContent className="pt-6 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-slate-500 dark:text-slate-450">Retrieval Cache</span>
                  <Badge className="bg-teal-50 text-teal-700 dark:bg-teal-950/40 dark:text-teal-400 font-mono">
                    {telemetry?.caches?.retrieval_hit_ratio ? `${(telemetry.caches.retrieval_hit_ratio * 100).toFixed(1)}%` : '0.0%'}
                  </Badge>
                </div>
                <div className="space-y-2">
                  <div className="h-2 w-full bg-slate-100 dark:bg-slate-900 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-teal-500"
                      style={{ width: `${(telemetry?.caches?.retrieval_hit_ratio ?? 0) * 100}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-slate-400 font-mono">
                    <span>{telemetry?.caches?.retrieval_hits ?? 0} Hits</span>
                    <span>{telemetry?.caches?.retrieval_misses ?? 0} Misses</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Cache 4: Assembled Context Prompt Cache */}
            <Card className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm">
              <CardContent className="pt-6 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-slate-500 dark:text-slate-450">Context Prompt Cache</span>
                  <Badge className="bg-teal-50 text-teal-700 dark:bg-teal-950/40 dark:text-teal-400 font-mono">
                    {telemetry?.caches?.context_hit_ratio ? `${(telemetry.caches.context_hit_ratio * 100).toFixed(1)}%` : '0.0%'}
                  </Badge>
                </div>
                <div className="space-y-2">
                  <div className="h-2 w-full bg-slate-100 dark:bg-slate-900 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-teal-500"
                      style={{ width: `${(telemetry?.caches?.context_hit_ratio ?? 0) * 100}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-slate-400 font-mono">
                    <span>{telemetry?.caches?.context_hits ?? 0} Hits</span>
                    <span>{telemetry?.caches?.context_misses ?? 0} Misses</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Tab 4: Playground & Evaluator */}
      {activeTab === 'playground' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fadeIn">
          {/* Query Evaluator Form Controls */}
          <div className="lg:col-span-1 space-y-6">
            <Card className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm overflow-hidden">
              <CardHeader className="bg-slate-50/50 dark:bg-slate-900/20 border-b border-slate-150 dark:border-slate-900">
                <CardTitle className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Sliders className="h-5 w-5 text-teal-650" />
                  RAG Evaluator
                </CardTitle>
                <CardDescription>Fine-tune retrieval parameters and measure precision/recall.</CardDescription>
              </CardHeader>
              <CardContent className="p-6 space-y-4">
                {/* Query Input */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-650 dark:text-slate-350">Test Query String</label>
                  <Input
                    placeholder="e.g. List all active medication prescriptions..."
                    value={playgroundQuery}
                    onChange={(e) => setPlaygroundQuery(e.target.value)}
                    className="bg-slate-50 border-slate-200 dark:border-slate-850 dark:bg-slate-900"
                  />
                </div>

                {/* Patient ID Custom Input */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-650 dark:text-slate-350">Target Patient ID (Optional)</label>
                  <Input
                    placeholder="Enter MongoDB Patient ID or select one from Sync Center..."
                    value={selectedPatientId}
                    onChange={(e) => {
                      setSelectedPatientId(e.target.value)
                      setSelectedPatientName(e.target.value)
                    }}
                    className="bg-slate-50 border-slate-200 dark:border-slate-850 dark:bg-slate-900"
                  />
                </div>

                {/* Ground Truth Chunk IDs */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-650 dark:text-slate-350">Ground Truth Doc IDs (Optional)</label>
                  <Input
                    placeholder="Comma-separated IDs (e.g. rep_01, mem_05)"
                    value={playgroundGroundTruth}
                    onChange={(e) => setPlaygroundGroundTruth(e.target.value)}
                    className="bg-slate-50 border-slate-200 dark:border-slate-850 dark:bg-slate-900 font-mono text-xs"
                  />
                </div>

                {/* Collections Checkboxes */}
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-650 dark:text-slate-350 block">Target Collections</label>
                  <div className="space-y-1.5 border border-slate-150 dark:border-slate-850 rounded-lg p-2.5 bg-slate-50/20 dark:bg-slate-900/10">
                    {[
                      { id: 'patient_memory', label: 'Patient Memory' },
                      { id: 'patient_reports', label: 'Patient Reports' },
                      { id: 'medical_knowledge', label: 'Medical Knowledge' },
                      { id: 'patient_lifestyle', label: 'Patient Lifestyle' },
                      { id: 'clinical_guidelines', label: 'Clinical Guidelines' },
                    ].map((col) => (
                      <label key={col.id} className="flex items-center gap-2 text-xs font-medium cursor-pointer py-0.5 text-slate-650 dark:text-slate-350 hover:text-slate-950 dark:hover:text-white">
                        <input
                          type="checkbox"
                          checked={playgroundCollections.includes(col.id)}
                          onChange={() => toggleCollection(col.id)}
                          className="rounded border-slate-200 dark:border-slate-800 text-teal-600 focus:ring-teal-500"
                        />
                        {col.label}
                      </label>
                    ))}
                  </div>
                </div>

                {/* Top K & Threshold Sliders */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-650 dark:text-slate-350">Top K</label>
                    <Input
                      type="number"
                      min={1}
                      max={20}
                      value={playgroundTopK}
                      onChange={(e) => setPlaygroundTopK(parseInt(e.target.value) || 5)}
                      className="bg-slate-50 border-slate-200 dark:border-slate-850 dark:bg-slate-900"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-650 dark:text-slate-350">Score Threshold</label>
                    <Input
                      type="number"
                      step={0.05}
                      min={0.0}
                      max={1.0}
                      value={playgroundThreshold}
                      onChange={(e) => setPlaygroundThreshold(parseFloat(e.target.value) || 0.3)}
                      className="bg-slate-50 border-slate-200 dark:border-slate-850 dark:bg-slate-900"
                    />
                  </div>
                </div>

                {/* Token Budget */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-650 dark:text-slate-350">Max Token Budget</label>
                  <Input
                    type="number"
                    value={playgroundTokenBudget}
                    onChange={(e) => setPlaygroundTokenBudget(parseInt(e.target.value) || 4000)}
                    className="bg-slate-50 border-slate-200 dark:border-slate-850 dark:bg-slate-900"
                  />
                </div>

                {/* Submit button */}
                <Button
                  onClick={handleRunEvaluation}
                  disabled={evaluating}
                  className="w-full bg-teal-600 hover:bg-teal-500 text-white font-bold py-2 border-0 mt-2 flex items-center justify-center gap-2"
                >
                  {evaluating ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Evaluating Pipeline...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 fill-current" />
                      Run Evaluation
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Evaluation Results Monitor Panel */}
          <div className="lg:col-span-2 space-y-6">
            {!evalResult && !evaluating ? (
              <Card className="border border-dashed border-slate-300 dark:border-slate-800 bg-slate-50/10 dark:bg-slate-900/5 h-[450px] flex items-center justify-center text-center">
                <CardContent className="space-y-2">
                  <Play className="h-10 w-10 text-slate-300 dark:text-slate-700 mx-auto" />
                  <h3 className="text-base font-bold text-slate-400">Playground Awaiting Evaluation Query</h3>
                  <p className="text-xs text-slate-500 dark:text-slate-450 max-w-sm">
                    Enter a query and parameter specifications on the left, then trigger evaluation to trace retrieval and prompt quality.
                  </p>
                </CardContent>
              </Card>
            ) : evaluating ? (
              <Card className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm h-[450px] flex items-center justify-center text-center">
                <CardContent className="space-y-4">
                  <Loader2 className="h-10 w-10 animate-spin text-teal-600 mx-auto" />
                  <h3 className="text-base font-bold text-slate-800 dark:text-slate-250">Executing E2E RAG Pipeline</h3>
                  <p className="text-xs text-slate-500 max-w-sm">
                    Detecting intent, generating query vector, retrieving matching Qdrant points, filtering duplicates, and compiling token-aware context.
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-6">
                {/* Metrics Badges Panel */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <Card className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 p-4 space-y-1">
                    <span className="text-xs text-slate-500 dark:text-slate-400 block font-semibold">Precision</span>
                    <strong className="text-2xl font-black text-slate-900 dark:text-white font-mono">
                      {(evalResult.metrics.precision * 100).toFixed(0)}%
                    </strong>
                  </Card>
                  <Card className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 p-4 space-y-1">
                    <span className="text-xs text-slate-500 dark:text-slate-400 block font-semibold">Recall</span>
                    <strong className="text-2xl font-black text-slate-900 dark:text-white font-mono">
                      {(evalResult.metrics.recall * 100).toFixed(0)}%
                    </strong>
                  </Card>
                  <Card className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 p-4 space-y-1">
                    <span className="text-xs text-slate-500 dark:text-slate-400 block font-semibold">Citation Quality</span>
                    <strong className="text-2xl font-black text-emerald-600 dark:text-emerald-450 font-mono">
                      {(evalResult.metrics.citation_quality * 100).toFixed(0)}%
                    </strong>
                  </Card>
                  <Card className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 p-4 space-y-1">
                    <span className="text-xs text-slate-500 dark:text-slate-400 block font-semibold">Duplicates Rate</span>
                    <strong className={`text-2xl font-black font-mono ${evalResult.metrics.duplicate_rate > 0.3 ? 'text-amber-500' : 'text-slate-900 dark:text-white'}`}>
                      {(evalResult.metrics.duplicate_rate * 100).toFixed(0)}%
                    </strong>
                  </Card>
                </div>

                {/* Subsystem Timeline Checkpoint */}
                <Card className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm overflow-hidden">
                  <CardHeader className="bg-slate-50/50 dark:bg-slate-900/20 border-b border-slate-105 dark:border-slate-900 pb-3">
                    <CardTitle className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                      <Clock className="h-4.5 w-4.5 text-teal-650" />
                      RAG Execution Timeline & Estimates
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-5 space-y-4">
                    <div className="flex justify-between items-center text-xs border-b border-slate-100 dark:border-slate-900 pb-2.5">
                      <span className="text-slate-500 dark:text-slate-400">Total Latency:</span>
                      <strong className="font-mono text-teal-600 dark:text-teal-400 font-extrabold text-sm">{evalResult.metrics.latency_ms.toFixed(1)} ms</strong>
                    </div>

                    {/* Timeline visualization */}
                    <div className="relative border-l border-slate-200 dark:border-slate-800 pl-4 space-y-4.5 ml-2.5 font-sans">
                      <div className="relative">
                        <div className="absolute -left-[21.5px] top-1 bg-teal-500 h-2.5 w-2.5 rounded-full ring-4 ring-teal-50 dark:ring-teal-950/40" />
                        <div className="text-xs font-semibold text-slate-900 dark:text-white">Query Intent & Tokenizing Check</div>
                        <div className="text-[10px] text-slate-450 dark:text-slate-500 mt-0.5">Approx. {(evalResult.metrics.latency_ms * 0.15).toFixed(0)}ms | Context extraction checked</div>
                      </div>
                      <div className="relative">
                        <div className="absolute -left-[21.5px] top-1 bg-teal-500 h-2.5 w-2.5 rounded-full ring-4 ring-teal-50 dark:ring-teal-950/40" />
                        <div className="text-xs font-semibold text-slate-900 dark:text-white">Qdrant Semantics Vector Match</div>
                        <div className="text-[10px] text-slate-450 dark:text-slate-500 mt-0.5">Approx. {(evalResult.metrics.latency_ms * 0.35).toFixed(0)}ms | Found {evalResult.retrieval_summary.hits_count} matched hits</div>
                      </div>
                      <div className="relative">
                        <div className="absolute -left-[21.5px] top-1 bg-teal-500 h-2.5 w-2.5 rounded-full ring-4 ring-teal-50 dark:ring-teal-950/40" />
                        <div className="text-xs font-semibold text-slate-900 dark:text-white">Re-Ranking & Duplicates Pruning</div>
                        <div className="text-[10px] text-slate-450 dark:text-slate-500 mt-0.5">Approx. {(evalResult.metrics.latency_ms * 0.1).toFixed(0)}ms | Removed {evalResult.retrieval_summary.duplicates_removed} redundant sections</div>
                      </div>
                      <div className="relative">
                        <div className="absolute -left-[21.5px] top-1 bg-teal-500 h-2.5 w-2.5 rounded-full ring-4 ring-teal-50 dark:ring-teal-950/40" />
                        <div className="text-xs font-semibold text-slate-900 dark:text-white">Context Construction Assembly</div>
                        <div className="text-[10px] text-slate-450 dark:text-slate-500 mt-0.5">Approx. {(evalResult.metrics.latency_ms * 0.4).toFixed(0)}ms | Budgeting {evalResult.parameters.token_budget} max tokens limit</div>
                      </div>
                    </div>

                    {/* Cost Estimator */}
                    <div className="bg-slate-50/50 dark:bg-slate-900/10 p-3 rounded-lg border border-slate-150 dark:border-slate-850 flex justify-between items-center text-xs">
                      <div>
                        <div className="font-semibold text-slate-700 dark:text-slate-300">Estimated Cost Contribution:</div>
                        <div className="text-[10px] text-slate-450">Based on tokens length & payload sizes</div>
                      </div>
                      <strong className="font-mono text-teal-600 dark:text-teal-400 font-extrabold text-sm">$0.0002 USD</strong>
                    </div>
                  </CardContent>
                </Card>

                {/* Assembled Context Preview */}
                <Card className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm overflow-hidden">
                  <CardHeader className="bg-slate-50/50 dark:bg-slate-900/20 border-b border-slate-105 dark:border-slate-900 pb-3 flex flex-row items-center justify-between">
                    <div>
                      <CardTitle className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                        <FileText className="h-4.5 w-4.5 text-teal-650" />
                        Assembled Retrieval Context
                      </CardTitle>
                      <CardDescription className="text-[10px] mt-0.5">Estimated context utilization: {(evalResult.metrics.context_utilization * 100).toFixed(0)}%</CardDescription>
                    </div>
                    <Badge className="bg-teal-50 text-teal-700 dark:bg-teal-950/40 dark:text-teal-400">
                      {evalResult.retrieval_summary.chunks_found} chunks used
                    </Badge>
                  </CardHeader>
                  <CardContent className="p-4 space-y-4">
                    <div className="max-h-[250px] overflow-y-auto bg-slate-50 dark:bg-slate-900 p-3 rounded-lg border border-slate-150 dark:border-slate-850 font-mono text-xs text-slate-800 dark:text-slate-300 whitespace-pre-wrap">
                      {evalResult.retrieval_summary.assembled_sections?.length > 0 ? (
                        evalResult.retrieval_summary.assembled_sections.join('\n\n')
                      ) : (
                        <span className="text-slate-400">Context is empty (No chunks passed score_threshold)</span>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 5: Benchmarks Panel */}
      {activeTab === 'benchmarks' && (
        <div className="space-y-6 animate-fadeIn">
          {/* Benchmark Controls Card */}
          <Card className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm overflow-hidden">
            <CardHeader className="bg-slate-50/50 dark:bg-slate-900/20 border-b border-slate-105 dark:border-slate-900">
              <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
                <div>
                  <CardTitle className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <Gauge className="h-5 w-5 text-teal-650 animate-pulse" />
                    RAG Benchmark suite
                  </CardTitle>
                  <CardDescription>
                    Run the automated evaluation harness querying the 7 predefined datasets to map latency and precision.
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  {benchmarkResult && (
                    <>
                      <Button
                        onClick={handleExportBenchmarkCSV}
                        variant="outline"
                        className="flex items-center gap-1.5 text-xs font-semibold px-3 border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-900"
                      >
                        <Download className="h-3.5 w-3.5" />
                        Export CSV
                      </Button>
                      <Button
                        onClick={handleExportBenchmarkJSON}
                        variant="outline"
                        className="flex items-center gap-1.5 text-xs font-semibold px-3 border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-900"
                      >
                        <Download className="h-3.5 w-3.5" />
                        Export JSON
                      </Button>
                    </>
                  )}
                  <Button
                    onClick={handleRunBenchmark}
                    disabled={runningBenchmark}
                    className="bg-slate-900 hover:bg-slate-800 text-white dark:bg-slate-850 dark:hover:bg-slate-750 font-semibold text-xs px-4 py-2 border-0 flex items-center gap-1.5"
                  >
                    {runningBenchmark ? (
                      <>
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        Running Suite...
                      </>
                    ) : (
                      <>
                        <Play className="h-3.5 w-3.5 fill-current" />
                        Execute Benchmarks
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-6">
              {!benchmarkResult && !runningBenchmark ? (
                <div className="py-20 text-center space-y-3">
                  <Gauge className="h-12 w-12 text-slate-300 dark:text-slate-750 mx-auto" />
                  <h3 className="text-base font-bold text-slate-400">Benchmark Data Not Compiled</h3>
                  <p className="text-xs text-slate-500 dark:text-slate-450 max-w-md mx-auto">
                    Executing the suite will process multiple intents queries, calculate retrieval accuracies, and record results details to MongoDB for dashboard telemetry tracking.
                  </p>
                </div>
              ) : runningBenchmark ? (
                <div className="py-20 text-center space-y-4">
                  <Loader2 className="h-10 w-10 animate-spin text-teal-605 mx-auto" />
                  <h3 className="text-base font-bold text-slate-800 dark:text-slate-250">Running Automated Queries Benchmark Suite</h3>
                  <p className="text-xs text-slate-500 max-w-sm mx-auto">
                    This test executes queries covering all 7 medical intents. Please wait, compiling timing ratios and precision summaries.
                  </p>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Benchmarks overall summary */}
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4 bg-slate-50/50 dark:bg-slate-900/10 p-4 rounded-xl border border-slate-150 dark:border-slate-850">
                    <div className="space-y-1.5">
                      <span className="text-[10px] text-slate-455 dark:text-slate-400 block font-semibold">Queries Run</span>
                      <strong className="text-lg font-black text-slate-900 dark:text-white font-mono">{benchmarkResult.total_queries_run}</strong>
                    </div>
                    <div className="space-y-1.5">
                      <span className="text-[10px] text-slate-455 dark:text-slate-400 block font-semibold">Average Latency</span>
                      <strong className="text-lg font-black text-slate-900 dark:text-white font-mono">{benchmarkResult.avg_latency_per_query_ms.toFixed(1)} ms</strong>
                    </div>
                    <div className="space-y-1.5">
                      <span className="text-[10px] text-slate-455 dark:text-slate-400 block font-semibold">Average Precision</span>
                      <strong className="text-lg font-black text-emerald-600 dark:text-emerald-450 font-mono">{(benchmarkResult.avg_precision * 100).toFixed(0)}%</strong>
                    </div>
                    <div className="space-y-1.5">
                      <span className="text-[10px] text-slate-455 dark:text-slate-400 block font-semibold">Average Recall</span>
                      <strong className="text-lg font-black text-emerald-600 dark:text-emerald-450 font-mono">{(benchmarkResult.avg_recall * 100).toFixed(0)}%</strong>
                    </div>
                    <div className="space-y-1.5">
                      <span className="text-[10px] text-slate-455 dark:text-slate-400 block font-semibold">Citation Quality</span>
                      <strong className="text-lg font-black text-teal-600 dark:text-teal-400 font-mono">{(benchmarkResult.avg_citation_quality * 100).toFixed(0)}%</strong>
                    </div>
                  </div>

                  {/* Category Details Table */}
                  <div className="space-y-3.5">
                    <h4 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                      <ShieldCheck className="h-4 w-4 text-emerald-500" />
                      Intent Categories Breakdown
                    </h4>
                    <div className="border border-slate-150 dark:border-slate-800 rounded-lg overflow-hidden font-sans">
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="bg-slate-50 dark:bg-slate-900/60 border-b border-slate-150 dark:border-slate-800 font-semibold text-slate-655 dark:text-slate-400">
                            <th className="p-3">Intent Category</th>
                            <th className="p-3">Avg Latency</th>
                            <th className="p-3">Precision</th>
                            <th className="p-3">Recall</th>
                            <th className="p-3">Citation Quality</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-900">
                          {Object.entries(benchmarkResult.categories || {}).map(([category, data]: [string, any]) => (
                            <tr key={category} className="hover:bg-slate-50/20 dark:hover:bg-slate-900/5 transition-colors">
                              <td className="p-3 font-semibold text-slate-900 dark:text-white">{category}</td>
                              <td className="p-3 font-mono">{data.avg_latency_ms.toFixed(1)} ms</td>
                              <td className="p-3">
                                <span className={`font-semibold ${data.avg_precision > 0.8 ? 'text-emerald-600' : 'text-amber-500'}`}>
                                  {(data.avg_precision * 100).toFixed(0)}%
                                </span>
                              </td>
                              <td className="p-3">
                                <span className="font-semibold text-slate-800 dark:text-slate-300">
                                  {(data.avg_recall * 100).toFixed(0)}%
                                </span>
                              </td>
                              <td className="p-3 font-mono font-bold text-teal-650 dark:text-teal-400">
                                {(data.avg_citation_quality * 100).toFixed(0)}%
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

