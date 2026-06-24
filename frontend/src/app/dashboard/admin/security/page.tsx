'use client'

import { useState, useEffect } from 'react'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { useAuthStore } from '@/stores/auth'
import { adminManagementService } from '@/services/admin-management.service'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import { toast } from 'react-hot-toast'
import {
  Shield,
  Lock,
  Clock,
  Globe,
  Activity,
  Power,
  Loader2,
  AlertTriangle,
  Server,
  UserCheck,
} from 'lucide-react'
import { AdminSession, AuditLog } from '@/types'

export default function AdminSecurityPage() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <AdminSecurityContent />
    </ProtectedRoute>
  )
}

function AdminSecurityContent() {
  const { user } = useAuthStore()
  const [sessions, setSessions] = useState<AdminSession[]>([])
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)

  // Session Revocation Confirm Modal
  const [confirmModalOpen, setConfirmModalOpen] = useState(false)
  const [sessionToRevoke, setSessionToRevoke] = useState<AdminSession | null>(null)
  const [revoking, setRevoking] = useState(false)

  const fetchData = async () => {
    if (!user) return
    try {
      setLoading(true)
      // Fetch sessions
      const sessionsRes = await adminManagementService.listSessions()
      if (sessionsRes.success && sessionsRes.data) {
        setSessions(sessionsRes.data)
      } else {
        toast.error(sessionsRes.message || 'Failed to load security sessions')
      }

      // Fetch audit logs (via admin details API)
      const detailRes = await adminManagementService.getAdminDetail(user.id)
      if (detailRes.success && detailRes.data) {
        setAuditLogs(detailRes.data.audit_summary || [])
      }
    } catch (err) {
      console.error(err)
      toast.error('An error occurred while loading security data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [user])

  const openRevokeConfirm = (session: AdminSession) => {
    setSessionToRevoke(session)
    setConfirmModalOpen(true)
  }

  const handleRevokeSession = async () => {
    if (!sessionToRevoke) return
    try {
      setRevoking(true)
      const res = await adminManagementService.revokeSession(sessionToRevoke.id)
      if (res.success) {
        toast.success('Session revoked successfully')
        setConfirmModalOpen(false)
        fetchData()
      } else {
        toast.error(res.message || 'Failed to revoke session')
      }
    } catch (err: any) {
      console.error(err)
      const msg = err.response?.data?.message || 'Failed to revoke session'
      toast.error(msg)
    } finally {
      setRevoking(false)
    }
  }

  // Calculate active sessions
  const activeSessionsCount = sessions.filter((s) => {
    const expired = new Date(s.expires_at) < new Date()
    return !s.revoked && !expired
  }).length

  return (
    <div className="space-y-6 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="border-b border-slate-200 pb-5">
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 flex items-center gap-2">
          <Lock className="h-8 w-8 text-teal-600" />
          Security & Session Management
        </h1>
        <p className="text-slate-500 mt-1">
          Monitor your active sessions, verify login metadata, and view recent security audits.
        </p>
      </div>

      {/* Grid of Security Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="border-slate-200 shadow bg-white">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
              <Server className="h-4 w-4 text-slate-400" />
              Active Sessions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-extrabold text-slate-950 mt-1">
              {loading ? <Loader2 className="h-7 w-7 text-teal-600 animate-spin" /> : activeSessionsCount}
            </div>
            <p className="text-xs text-slate-400 mt-1">Authorized devices/browsers connected</p>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow bg-white">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
              <Clock className="h-4 w-4 text-slate-400" />
              Last Session Activity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg font-bold text-slate-800 mt-1">
              {loading ? (
                <Loader2 className="h-7 w-7 text-teal-600 animate-spin" />
              ) : sessions.length > 0 ? (
                new Date(sessions[0].last_activity).toLocaleString(undefined, {
                  dateStyle: 'medium',
                  timeStyle: 'short',
                })
              ) : (
                'No activity'
              )}
            </div>
            <p className="text-xs text-slate-400 mt-1">Timestamp of last token refresh activity</p>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow bg-white">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
              <UserCheck className="h-4 w-4 text-slate-400" />
              Account Integrity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2 mt-1">
              {user?.is_active ? (
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  Active
                </span>
              ) : (
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-red-50 text-red-700 border border-red-200">
                  Disabled
                </span>
              )}
              {user?.email_verified ? (
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200">
                  Verified
                </span>
              ) : (
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-yellow-50 text-yellow-700 border border-yellow-200">
                  Unverified
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-2">Current administrator privilege status</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Session Management Table (Left 2 cols) */}
        <Card className="border-slate-200 shadow bg-white lg:col-span-2 overflow-hidden rounded-xl">
          <CardHeader className="border-b border-slate-100 bg-slate-50/50">
            <CardTitle className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Globe className="h-5 w-5 text-teal-600" />
              Connected Sessions
            </CardTitle>
            <CardDescription>
              Revoke active credentials to log out immediately on those devices.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">
                      Session ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">
                      Last Activity
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-bold text-slate-500 uppercase tracking-wider">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-slate-100">
                  {loading ? (
                    Array.from({ length: 2 }).map((_, i) => (
                      <tr key={i} className="animate-pulse">
                        <td className="px-6 py-4">
                          <div className="h-4 bg-slate-200 rounded w-32" />
                        </td>
                        <td className="px-6 py-4">
                          <div className="h-4 bg-slate-200 rounded w-24" />
                        </td>
                        <td className="px-6 py-4">
                          <div className="h-5 bg-slate-200 rounded w-16" />
                        </td>
                        <td className="px-6 py-4 text-right">
                          <div className="h-8 bg-slate-200 rounded w-16 ml-auto" />
                        </td>
                      </tr>
                    ))
                  ) : sessions.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="px-6 py-12 text-center text-slate-400">
                        No connected sessions found.
                      </td>
                    </tr>
                  ) : (
                    sessions.map((session) => {
                      const isExpired = new Date(session.expires_at) < new Date()
                      return (
                        <tr key={session.id} className="hover:bg-slate-50/50 transition-colors">
                          <td className="px-6 py-4 whitespace-nowrap text-xs font-mono text-slate-500">
                            {session.id}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-xs text-slate-600 font-semibold">
                            {new Date(session.last_activity).toLocaleString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            {session.revoked ? (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-red-50 text-red-700 border border-red-200">
                                Revoked
                              </span>
                            ) : isExpired ? (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-slate-100 text-slate-600 border border-slate-200">
                                Expired
                              </span>
                            ) : (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                                Active
                              </span>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right text-xs">
                            {!session.revoked && !isExpired && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => openRevokeConfirm(session)}
                                className="text-red-600 hover:text-red-700 border-red-200 hover:bg-red-50/50 text-xs py-1 px-2.5 h-8 font-semibold"
                              >
                                Revoke
                              </Button>
                            )}
                          </td>
                        </tr>
                      )
                    })
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Security Activity (Right 1 col) */}
        <Card className="border-slate-200 shadow bg-white rounded-xl overflow-hidden flex flex-col h-[500px]">
          <CardHeader className="border-b border-slate-100 bg-slate-50/50 py-4">
            <CardTitle className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Activity className="h-5 w-5 text-teal-600" />
              Security Activity
            </CardTitle>
            <CardDescription>
              Recent security events involving your account.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex-1 overflow-y-auto p-4 divide-y divide-slate-100 bg-slate-50/30">
            {loading ? (
              <div className="py-20 flex justify-center items-center">
                <Loader2 className="h-8 w-8 text-teal-600 animate-spin" />
              </div>
            ) : auditLogs.length === 0 ? (
              <div className="py-20 text-center text-slate-400 text-sm">
                No recent security activity logged.
              </div>
            ) : (
              auditLogs
                .filter((log) =>
                  [
                    'ADMIN_LOGIN',
                    'ADMIN_LOGOUT',
                    'ADMIN_PASSWORD_RESET_REQUEST',
                    'ADMIN_PASSWORD_RESET_SUCCESS',
                    'ADMIN_PASSWORD_CHANGED',
                    'ADMIN_SESSION_REVOKED',
                    'ADMIN_TOKEN_REFRESH',
                  ].includes(log.action)
                )
                .map((log) => (
                  <div key={log.id} className="py-3 text-xs space-y-1 bg-white hover:bg-slate-50 p-2 border border-slate-100 rounded-lg shadow-sm mb-2">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-teal-700 bg-teal-50 border border-teal-100 rounded px-1.5 py-0.5">
                        {log.action.replace('ADMIN_', '')}
                      </span>
                      <span className="text-slate-400 text-[10px]">
                        {new Date(log.created_at).toLocaleDateString(undefined, {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                    </div>
                    {log.ip_address && (
                      <p className="text-[10px] text-slate-500 font-semibold">
                        IP: {log.ip_address}
                      </p>
                    )}
                  </div>
                ))
            )}
          </CardContent>
        </Card>
      </div>

      {/* Revocation Confirmation Dialog */}
      <Dialog open={confirmModalOpen} onOpenChange={setConfirmModalOpen}>
        <DialogContent className="max-w-md rounded-xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 font-bold text-xl text-red-600">
              <AlertTriangle className="h-6 w-6" />
              Revoke Session Authorization?
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to revoke the session {sessionToRevoke?.id}?
            </DialogDescription>
          </DialogHeader>

          <div className="py-3 space-y-2 text-sm text-slate-600">
            <p>
              Once revoked, any browser or mobile app currently connected via this session token will lose API access immediately and be forced to re-login.
            </p>
          </div>

          <DialogFooter className="pt-4 border-t gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setConfirmModalOpen(false)}
              className="border-slate-200 text-slate-700 font-semibold h-10 w-full sm:w-auto"
            >
              Cancel
            </Button>
            <Button
              type="button"
              disabled={revoking}
              onClick={handleRevokeSession}
              className="bg-red-600 hover:bg-red-700 text-white font-semibold h-10 w-full sm:w-auto flex items-center justify-center gap-1.5"
            >
              {revoking && <Loader2 className="h-4 w-4 animate-spin" />}
              Revoke Session
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
