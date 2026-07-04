'use client'

import { useState, useEffect } from 'react'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import { toast } from 'react-hot-toast'
import {
  Cpu,
  Server,
  Database,
  RefreshCw,
  Clock,
  Sparkles,
  Activity,
  Trash2,
  Archive,
  AlertTriangle,
  Loader2,
  CheckCircle,
  AlertCircle,
} from 'lucide-react'
import {
  useSystemHealth,
  useSystemInfo,
  useBackgroundJobs,
  useMaintenanceAction,
} from '@/hooks/use-system-monitor'
import { ServiceHealthStatus } from '@/types'

export default function AdminSystemDashboard() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <AdminSystemContent />
    </ProtectedRoute>
  )
}

function AdminSystemContent() {
  const { data: healthData, isLoading: healthLoading, refetch: refetchHealth, isRefetching: healthRefetching } = useSystemHealth()
  const { data: infoData, isLoading: infoLoading, refetch: refetchInfo } = useSystemInfo()
  const { data: jobsData, isLoading: jobsLoading, refetch: refetchJobs, isRefetching: jobsRefetching } = useBackgroundJobs()
  const maintenanceMutation = useMaintenanceAction()

  // Maintenance action states
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [selectedAction, setSelectedAction] = useState<
    'clear-sessions' | 'clear-otps' | 'archive-notifications' | 'archive-audit-logs' | null
  >(null)
  const [retentionDays, setRetentionDays] = useState<number>(30)

  const handleRefreshAll = async () => {
    await Promise.all([refetchHealth(), refetchInfo(), refetchJobs()])
    toast.success('System parameters refreshed')
  }

  const triggerConfirm = (
    action: 'clear-sessions' | 'clear-otps' | 'archive-notifications' | 'archive-audit-logs',
    defaultRetention?: number
  ) => {
    setSelectedAction(action)
    if (defaultRetention !== undefined) {
      setRetentionDays(defaultRetention)
    }
    setConfirmOpen(true)
  }

  const runAction = async () => {
    if (!selectedAction) return
    try {
      const payload: {
        actionType: typeof selectedAction
        retentionDays?: number
      } = { actionType: selectedAction }

      if (selectedAction === 'archive-notifications' || selectedAction === 'archive-audit-logs') {
        payload.retentionDays = retentionDays
      }

      const res = await maintenanceMutation.mutateAsync(payload)
      
      const count = res.details?.deleted_count ?? res.details?.archived_count ?? 0
      toast.success(`${res.message || 'Operation executed successfully'} (Affected: ${count})`)
      setConfirmOpen(false)
    } catch (err: any) {
      console.error(err)
      toast.error(err.message || 'Failed to complete maintenance action')
    }
  }

  // Format uptime string
  const formatUptime = (seconds?: number) => {
    if (seconds === undefined) return 'N/A'
    const d = Math.floor(seconds / (3600 * 24))
    const h = Math.floor((seconds % (3600 * 24)) / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    const s = Math.floor(seconds % 60)

    const parts = []
    if (d > 0) parts.push(`${d}d`)
    if (h > 0) parts.push(`${h}h`)
    if (m > 0) parts.push(`${m}m`)
    parts.push(`${s}s`)
    return parts.join(' ')
  }

  const getStatusBadge = (status: ServiceHealthStatus | string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'active':
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400 flex-shrink-0">
            <CheckCircle className="h-3 w-3 flex-shrink-0" />
            Healthy
          </span>
        )
      case 'degraded':
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-1.5 py-0.5 text-[10px] font-semibold text-amber-700 dark:bg-amber-950/30 dark:text-amber-400 flex-shrink-0">
            <AlertTriangle className="h-3 w-3 flex-shrink-0" />
            Degraded
          </span>
        )
      case 'offline':
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-1.5 py-0.5 text-[10px] font-semibold text-rose-700 dark:bg-rose-950/30 dark:text-rose-400 flex-shrink-0">
            <AlertCircle className="h-3 w-3 flex-shrink-0" />
            Offline
          </span>
        )
      default:
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-400 flex-shrink-0">
            <Clock className="h-3 w-3 flex-shrink-0" />
            {status}
          </span>
        )
    }
  }

  const getActionTitle = (action: typeof selectedAction) => {
    switch (action) {
      case 'clear-sessions':
        return 'Purge Expired Sessions'
      case 'clear-otps':
        return 'Purge Expired OTPs'
      case 'archive-notifications':
        return 'Archive Old Notifications'
      case 'archive-audit-logs':
        return 'Archive Old Audit Logs'
      default:
        return 'Maintenance Action'
    }
  }

  const getActionWarning = (action: typeof selectedAction) => {
    switch (action) {
      case 'clear-sessions':
        return 'This will permanently remove all expired user and administrator JWT refresh token sessions. Active sessions will not be disrupted.'
      case 'clear-otps':
        return 'This will permanently delete all expired OTP verification code registers. This does not affect active authentication attempts.'
      case 'archive-notifications':
        return 'This will move all notification logs older than the configured threshold to cold backup storage collections and remove them from active screens.'
      case 'archive-audit-logs':
        return 'This will move all audit log entries older than the configured threshold to cold backup storage collections and remove them from the active dashboard feed.'
      default:
        return 'Are you sure you want to run this maintenance action?'
    }
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            System Health & Maintenance
          </h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            Real-time server performance diagnostics, background scheduler monitoring, and database maintenance cleanups.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={handleRefreshAll}
            variant="outline"
            className="flex items-center gap-2 border-slate-200 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-900"
            disabled={healthRefetching || jobsRefetching}
          >
            <RefreshCw className={`h-4 w-4 ${healthRefetching || jobsRefetching ? 'animate-spin' : ''}`} />
            Refresh Status
          </Button>
        </div>
      </div>

      {/* Grid: Health Checks & System Info */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* System Info Card */}
        <Card className="border border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-950/50 backdrop-blur-sm shadow-sm lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-lg font-bold flex items-center gap-2 text-slate-900 dark:text-white">
              <Cpu className="h-5 w-5 text-teal-500" />
              Platform Diagnostics
            </CardTitle>
            <CardDescription>Server host details and running configuration</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {infoLoading ? (
              <div className="flex items-center justify-center py-6">
                <Loader2 className="h-6 w-6 animate-spin text-teal-500" />
              </div>
            ) : infoData ? (
              <div className="divide-y divide-slate-100 dark:divide-slate-900 text-sm">
                <div className="flex justify-between py-2.5">
                  <span className="text-slate-500 dark:text-slate-400">Uptime</span>
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {formatUptime(infoData.uptime_seconds)}
                  </span>
                </div>
                <div className="flex justify-between py-2.5">
                  <span className="text-slate-500 dark:text-slate-400">Environment</span>
                  <span className="font-semibold capitalize text-slate-900 dark:text-white">
                    {infoData.environment}
                  </span>
                </div>
                <div className="flex justify-between py-2.5">
                  <span className="text-slate-500 dark:text-slate-400">Platform Version</span>
                  <span className="font-mono text-slate-900 dark:text-white">{infoData.version}</span>
                </div>
                <div className="flex justify-between py-2.5">
                  <span className="text-slate-500 dark:text-slate-400">Startup Timestamp</span>
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {new Date(infoData.startup_time).toLocaleDateString()} {new Date(infoData.startup_time).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ) : (
              <div className="text-center text-sm text-slate-500 py-6">Failed to retrieve platform details</div>
            )}
          </CardContent>
        </Card>

        {/* Background Jobs Card */}
        <Card className="border border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-950/50 backdrop-blur-sm shadow-sm lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg font-bold flex items-center gap-2 text-slate-900 dark:text-white">
              <Activity className="h-5 w-5 text-teal-500" />
              Background Tasks Status
            </CardTitle>
            <CardDescription>Aggregation monitoring for scheduler and job queues</CardDescription>
          </CardHeader>
          <CardContent>
            {jobsLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-teal-500" />
              </div>
            ) : jobsData ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-slate-100 dark:border-slate-900 text-slate-500 dark:text-slate-400">
                      <th className="pb-3 font-semibold">Subsystem Queue</th>
                      <th className="pb-3 font-semibold text-center">Active/Queued</th>
                      <th className="pb-3 font-semibold text-center">Completed</th>
                      <th className="pb-3 font-semibold text-center">Failed/Cancelled</th>
                      <th className="pb-3 font-semibold">Uptime Status</th>
                      <th className="pb-3 font-semibold">Next Scheduled Run</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-900 text-slate-900 dark:text-white">
                    {/* Reminder Jobs */}
                    <tr>
                      <td className="py-3 font-medium flex items-center gap-2">
                        <Clock className="h-4 w-4 text-slate-400" />
                        Reminder Schedulers
                      </td>
                      <td className="py-3 text-center font-semibold">{jobsData.reminder_jobs.queued}</td>
                      <td className="py-3 text-center text-emerald-600 dark:text-emerald-400 font-semibold">
                        {jobsData.reminder_jobs.completed}
                      </td>
                      <td className="py-3 text-center text-rose-600 dark:text-rose-400 font-semibold">
                        {jobsData.reminder_jobs.failed}
                      </td>
                      <td className="py-3">{getStatusBadge(jobsData.reminder_jobs.status)}</td>
                      <td className="py-3 text-slate-500">
                        {jobsData.reminder_jobs.next_execution
                          ? new Date(jobsData.reminder_jobs.next_execution).toLocaleTimeString([], {
                              hour: '2-digit',
                              minute: '2-digit',
                            })
                          : 'None'}
                      </td>
                    </tr>
                    {/* Notification Jobs */}
                    <tr>
                      <td className="py-3 font-medium flex items-center gap-2">
                        <Server className="h-4 w-4 text-slate-400" />
                        Notification Dispatches
                      </td>
                      <td className="py-3 text-center text-slate-400 font-semibold">-</td>
                      <td className="py-3 text-center text-slate-400 font-semibold">-</td>
                      <td className="py-3 text-center text-slate-400 font-semibold">-</td>
                      <td className="py-3">{getStatusBadge(jobsData.notification_jobs.status)}</td>
                      <td className="py-3 text-slate-400">N/A</td>
                    </tr>
                    {/* AI Agent Jobs */}
                    <tr>
                      <td className="py-3 font-medium flex items-center gap-2">
                        <Sparkles className="h-4 w-4 text-slate-400" />
                        AI Agent Analytics
                      </td>
                      <td className="py-3 text-center text-slate-400 font-semibold">-</td>
                      <td className="py-3 text-center text-slate-400 font-semibold">-</td>
                      <td className="py-3 text-center text-slate-400 font-semibold">-</td>
                      <td className="py-3">{getStatusBadge(jobsData.ai_jobs.status)}</td>
                      <td className="py-3 text-slate-400">N/A</td>
                    </tr>
                    {/* Failed Job Logs */}
                    <tr>
                      <td className="py-3 font-medium flex items-center gap-2">
                        <AlertTriangle className="h-4 w-4 text-slate-400" />
                        Dead-Letter Failures
                      </td>
                      <td className="py-3 text-center text-slate-400 font-semibold">-</td>
                      <td className="py-3 text-center text-slate-400 font-semibold">-</td>
                      <td className="py-3 text-center text-slate-400 font-semibold">-</td>
                      <td className="py-3">{getStatusBadge(jobsData.failed_jobs.status)}</td>
                      <td className="py-3 text-slate-400">N/A</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center text-sm text-slate-500 py-12">Failed to load background task statistics</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Section: Live Subsystem Health Status */}
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white mb-4">
          Subsystems Health
        </h2>
        {healthLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
            {[1, 2, 3, 4, 5].map((idx) => (
              <Card key={idx} className="border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 animate-pulse h-36" />
            ))}
          </div>
        ) : healthData?.services ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
            {healthData.services.map((svc) => (
              <Card
                key={svc.name}
                className="border border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-950/50 backdrop-blur-sm shadow-sm hover:shadow-md transition-shadow"
              >
                <CardContent className="pt-6 space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-1.5 min-w-0">
                    <span className="font-semibold text-slate-900 dark:text-white text-sm truncate min-w-0 flex-1">{svc.name}</span>
                    <div className="flex-shrink-0">{getStatusBadge(svc.status)}</div>
                  </div>
                  <div className="space-y-1">
                    <div className="text-xs text-slate-500">Latency</div>
                    <div className="text-lg font-mono font-bold text-slate-900 dark:text-white">
                      {svc.latency_ms > 0 ? `${svc.latency_ms} ms` : svc.status === 'offline' ? 'N/A' : '0 ms'}
                    </div>
                  </div>
                  <div className="text-xs text-slate-600 dark:text-slate-400 line-clamp-1" title={svc.message}>
                    {svc.message}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="text-center text-sm text-slate-500 py-12 border border-dashed rounded-lg border-slate-200 dark:border-slate-800">
            Failed to fetch system subsystem connectivity health checks.
          </div>
        )}
      </div>

      {/* Section: Maintenance Utilities */}
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white mb-4">
          Maintenance Operations
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Purge Expired Sessions */}
          <Card className="border border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-950/50 backdrop-blur-sm shadow-sm flex flex-col justify-between">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-bold flex items-center gap-2 text-slate-900 dark:text-white">
                <Trash2 className="h-4 w-4 text-teal-500" />
                Clear Expired Sessions
              </CardTitle>
              <CardDescription className="text-xs">
                Permanently purge all expired refresh tokens from the active database cache list.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-0">
              <Button
                onClick={() => triggerConfirm('clear-sessions')}
                className="w-full mt-2 bg-slate-900 hover:bg-slate-800 text-white dark:bg-slate-800 dark:hover:bg-slate-700 text-xs font-semibold py-2 rounded-md"
              >
                Execute Purge
              </Button>
            </CardContent>
          </Card>

          {/* Purge Expired OTPs */}
          <Card className="border border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-950/50 backdrop-blur-sm shadow-sm flex flex-col justify-between">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-bold flex items-center gap-2 text-slate-900 dark:text-white">
                <Trash2 className="h-4 w-4 text-teal-500" />
                Clear Expired OTPs
              </CardTitle>
              <CardDescription className="text-xs">
                Permanently purge all expired one-time passcode registers from the active listings.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-0">
              <Button
                onClick={() => triggerConfirm('clear-otps')}
                className="w-full mt-2 bg-slate-900 hover:bg-slate-800 text-white dark:bg-slate-800 dark:hover:bg-slate-700 text-xs font-semibold py-2 rounded-md"
              >
                Execute Purge
              </Button>
            </CardContent>
          </Card>

          {/* Archive Old Notifications */}
          <Card className="border border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-950/50 backdrop-blur-sm shadow-sm flex flex-col justify-between">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-bold flex items-center gap-2 text-slate-900 dark:text-white">
                <Archive className="h-4 w-4 text-teal-500" />
                Archive Notifications
              </CardTitle>
              <CardDescription className="text-xs">
                Move user notifications older than retention days into backups to preserve database speed.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-0">
              <Button
                onClick={() => triggerConfirm('archive-notifications', 30)}
                className="w-full mt-2 bg-slate-900 hover:bg-slate-800 text-white dark:bg-slate-800 dark:hover:bg-slate-700 text-xs font-semibold py-2 rounded-md"
              >
                Execute Archival
              </Button>
            </CardContent>
          </Card>

          {/* Archive Old Audit Logs */}
          <Card className="border border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-950/50 backdrop-blur-sm shadow-sm flex flex-col justify-between">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-bold flex items-center gap-2 text-slate-900 dark:text-white">
                <Archive className="h-4 w-4 text-teal-500" />
                Archive Audit Trails
              </CardTitle>
              <CardDescription className="text-xs">
                Move administrative audit log records older than retention days into backups to optimize search queries.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-0">
              <Button
                onClick={() => triggerConfirm('archive-audit-logs', 90)}
                className="w-full mt-2 bg-slate-900 hover:bg-slate-800 text-white dark:bg-slate-800 dark:hover:bg-slate-700 text-xs font-semibold py-2 rounded-md"
              >
                Execute Archival
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Double confirmation modal dialog */}
      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-slate-900 dark:text-white">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              Confirm {getActionTitle(selectedAction)}?
            </DialogTitle>
            <DialogDescription className="text-sm pt-2 text-slate-600 dark:text-slate-400">
              {getActionWarning(selectedAction)}
            </DialogDescription>
          </DialogHeader>

          {/* Retention threshold inputs for archival commands */}
          {(selectedAction === 'archive-notifications' || selectedAction === 'archive-audit-logs') && (
            <div className="py-4 space-y-2">
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                Retention Threshold (Days)
              </label>
              <input
                type="number"
                min="1"
                max="365"
                value={retentionDays}
                onChange={(e) => setRetentionDays(parseInt(e.target.value) || 1)}
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-800 dark:bg-slate-950 dark:text-white focus:outline-none focus:ring-1 focus:ring-teal-500"
              />
            </div>
          )}

          <DialogFooter className="mt-4 gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={() => setConfirmOpen(false)}
              className="border-slate-200 text-slate-700 hover:bg-slate-50 dark:border-slate-800 dark:text-slate-300 dark:hover:bg-slate-900"
            >
              Cancel
            </Button>
            <Button
              onClick={runAction}
              disabled={maintenanceMutation.isPending}
              className="bg-slate-900 hover:bg-slate-800 text-white dark:bg-slate-800 dark:hover:bg-slate-700 font-semibold"
            >
              {maintenanceMutation.isPending ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Running...
                </span>
              ) : (
                'Confirm Execution'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
