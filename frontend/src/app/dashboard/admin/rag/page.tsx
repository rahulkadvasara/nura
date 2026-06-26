'use client'

import { useState, useEffect } from 'react'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { toast } from 'react-hot-toast'
import { useQuery } from '@tanstack/react-query'
import { adminUserService } from '@/services/admin-user.service'
import { useAuditLogs } from '@/hooks/use-admin-logs'
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
} from 'lucide-react'
import { User } from '@/types'

export default function AdminRagSyncPage() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <AdminRagSyncContent />
    </ProtectedRoute>
  )
}

function AdminRagSyncContent() {
  const [search, setSearch] = useState('')
  const [patients, setPatients] = useState<User[]>([])
  const [searchingPatients, setSearchingPatients] = useState(false)

  // API Queries & Mutations
  const { data: status, isLoading: loadingStatus, refetch: refetchStatus, isRefetching: refetchingStatus } = useSyncStatus()
  const { data: stats, isLoading: loadingStats, refetch: refetchStats, isRefetching: refetchingStats } = useSyncStatistics()
  
  // RAG sync logs fetched from the Audit Log system
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
    await Promise.all([refetchStatus(), refetchStats(), refetchLogs()])
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

  const isSyncInProgress = rebuildSyncMutation.isPending || (status && status.queue_size > 0)
  const isRefreshing = refetchingStatus || refetchingStats || refetchingLogs

  // Compute calculated metrics
  const totalCount = stats?.sync_count ?? 0
  const skippedCount = stats?.vectors_skipped ?? 0
  const regeneratedCount = stats?.vectors_regenerated ?? 0
  const efficiencyPercentage = totalCount > 0 ? ((skippedCount / totalCount) * 100).toFixed(0) : '0'

  return (
    <div className="space-y-6 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            <Database className="h-8 w-8 text-teal-600 dark:text-teal-400" />
            <span>RAG Memory Sync Pipeline</span>
          </h1>
          <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
            Real-time event synchronization dashboard mapping longitudinal MongoDB clinical profiles to semantic Qdrant indexes.
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

      {/* Pipeline Telemetry Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Metric 1: Total Syncs */}
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

        {/* Metric 2: Skip/Efficiency Ratio */}
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

        {/* Metric 3: Latency */}
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

        {/* Metric 4: Fault Tolerance (Failures/DLQ) */}
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

      {/* Main Grid Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Side (2 Columns): Control Center & Patient Lookup */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Component 1: Control Center */}
          <Card className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm overflow-hidden">
            <CardHeader className="border-b border-slate-100 dark:border-slate-900 bg-slate-50/50 dark:bg-slate-900/20">
              <CardTitle className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Sliders className="h-5 w-5 text-teal-600" />
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
                  className="bg-slate-900 hover:bg-slate-800 text-white dark:bg-slate-800 dark:hover:bg-slate-700 font-semibold text-xs whitespace-nowrap px-4 py-2 border-0"
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

          {/* Component 2: Manual Sync & Patient Lookup */}
          <Card className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm overflow-hidden">
            <CardHeader className="border-b border-slate-100 dark:border-slate-900 bg-slate-50/50 dark:bg-slate-900/20">
              <CardTitle className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Users className="h-5 w-5 text-teal-600" />
                Manual Patient Memory Sync
              </CardTitle>
              <CardDescription>Query active patients to inspect and sync records.</CardDescription>
            </CardHeader>
            <CardContent className="p-6 space-y-4">
              <div className="relative">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Filter patients by name or email..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-9 bg-slate-50 border-slate-200 dark:border-slate-800 dark:bg-slate-900 focus:bg-white transition-colors"
                />
              </div>

              <div className="border border-slate-150 dark:border-slate-850 rounded-lg divide-y divide-slate-100 dark:divide-slate-900 overflow-hidden max-h-[300px] overflow-y-auto">
                {searchingPatients ? (
                  <div className="flex justify-center items-center py-10 text-sm text-slate-500">
                    <Loader2 className="h-4 w-4 animate-spin mr-2 text-teal-600" />
                    Searching profiles...
                  </div>
                ) : patients.length === 0 ? (
                  <div className="py-10 text-center text-sm text-slate-400">
                    No active patients matching criteria.
                  </div>
                ) : (
                  patients.map((pat) => {
                    const isSyncing = syncPatientMutation.isPending && syncPatientMutation.variables === pat.id
                    return (
                      <div key={pat.id} className="flex items-center justify-between p-3.5 hover:bg-slate-50/40 dark:hover:bg-slate-900/20 transition-colors">
                        <div className="flex items-center min-w-0 mr-4">
                          <div className="h-9 w-9 flex-shrink-0 rounded-full bg-teal-50 dark:bg-teal-950/30 flex items-center justify-center border border-teal-100 dark:border-teal-900/50 text-teal-700 dark:text-teal-400 font-bold text-sm">
                            {pat.full_name ? pat.full_name.charAt(0).toUpperCase() : 'P'}
                          </div>
                          <div className="ml-3 min-w-0">
                            <p className="text-sm font-semibold text-slate-900 dark:text-white truncate">{pat.full_name}</p>
                            <p className="text-xs text-slate-400 truncate">{pat.email}</p>
                          </div>
                        </div>
                        <Button
                          size="sm"
                          onClick={() => handleSyncPatient(pat.id, pat.full_name)}
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
                    )
                  })
                )}
              </div>
            </CardContent>
          </Card>

        </div>

        {/* Right Side (1 Column): Queue Monitor & History */}
        <div className="space-y-6">
          
          {/* Component 3: Live Queue Monitor */}
          <Card className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm overflow-hidden">
            <CardHeader className="border-b border-slate-100 dark:border-slate-900 bg-slate-50/50 dark:bg-slate-900/20">
              <CardTitle className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Activity className="h-5 w-5 text-teal-600" />
                Pipeline Queue Monitor
              </CardTitle>
              <CardDescription>Current status of async event worker.</CardDescription>
            </CardHeader>
            <CardContent className="p-6">
              {loadingStatus ? (
                <div className="flex justify-center py-6">
                  <Loader2 className="h-6 w-6 animate-spin text-teal-600" />
                </div>
              ) : status ? (
                <div className="space-y-4">
                  <div className="flex justify-between items-center py-2 border-b border-slate-100 dark:border-slate-900 text-sm">
                    <span className="text-slate-500 dark:text-slate-400">Worker Status</span>
                    <span className="font-semibold">
                      {status.running ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-400">
                          <CheckCircle className="h-3 w-3" />
                          Active / Listening
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2 py-0.5 text-xs font-semibold text-rose-700 dark:bg-rose-950/20 dark:text-rose-400">
                          <XCircle className="h-3 w-3" />
                          Offline
                        </span>
                      )}
                    </span>
                  </div>
                  
                  <div className="flex justify-between items-center py-2 border-b border-slate-100 dark:border-slate-900 text-sm">
                    <span className="text-slate-500 dark:text-slate-400">Buffered Queue Length</span>
                    <span className="font-mono font-bold text-slate-900 dark:text-white">
                      {status.queue_size} tasks
                    </span>
                  </div>

                  <div className="flex justify-between items-center py-2 text-sm">
                    <span className="text-slate-500 dark:text-slate-400">Dead Letter Jobs</span>
                    <span className={`font-mono font-bold ${status.dlq_count > 0 ? 'text-rose-600' : 'text-slate-900 dark:text-white'}`}>
                      {status.dlq_count} failed jobs
                    </span>
                  </div>
                </div>
              ) : (
                <div className="text-center text-sm text-slate-400">Unable to load worker status</div>
              )}
            </CardContent>
          </Card>

          {/* Component 4: Sync History */}
          <Card className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm overflow-hidden">
            <CardHeader className="border-b border-slate-100 dark:border-slate-900 bg-slate-50/50 dark:bg-slate-900/20">
              <CardTitle className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <History className="h-5 w-5 text-teal-600" />
                Sync Audit History
              </CardTitle>
              <CardDescription>Most recent pipeline operations.</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              {loadingLogs ? (
                <div className="flex justify-center py-10">
                  <Loader2 className="h-6 w-6 animate-spin text-teal-600" />
                </div>
              ) : !logsData || logsData.logs?.length === 0 ? (
                <div className="py-10 text-center text-sm text-slate-400">
                  No synchronization logs recorded yet.
                </div>
              ) : (
                <div className="divide-y divide-slate-100 dark:divide-slate-900 max-h-[400px] overflow-y-auto">
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
  )
}
