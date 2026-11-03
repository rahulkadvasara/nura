'use client'

import { useState } from 'react'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import {
  Activity,
  Search,
  Calendar,
  Filter,
  User as UserIcon,
  Clock,
  Cpu,
  Shield,
  Copy,
  ChevronLeft,
  ChevronRight,
  Download,
  AlertCircle,
  FileCode,
  CheckCircle2,
  XCircle,
  AlertTriangle,
} from 'lucide-react'
import {
  useAuditLogs,
  useAgentLogs,
  useAuthenticationLogs,
} from '@/hooks/use-admin-logs'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { toast } from 'react-hot-toast'
import { AuditLog, AgentLog } from '@/types'

type ActiveTab = 'audit' | 'agent' | 'auth'

export default function AdminLogsPage() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <AdminLogsContent />
    </ProtectedRoute>
  )
}

function AdminLogsContent() {
  const [activeTab, setActiveTab] = useState<ActiveTab>('audit')

  // Search & Global filters
  const [search, setSearch] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  // Audit Tab specific filters
  const [auditUser, setAuditUser] = useState('')
  const [auditRole, setAuditRole] = useState('')
  const [auditAction, setAuditAction] = useState('')
  const [auditResource, setAuditResource] = useState('')

  // Agent Tab specific filters
  const [agentName, setAgentName] = useState('')
  const [agentStatus, setAgentStatus] = useState('')
  const [agentSession, setAgentSession] = useState('')

  // Pagination states
  const [limit] = useState(15)
  const [auditSkip, setAuditSkip] = useState(0)
  const [agentSkip, setAgentSkip] = useState(0)
  const [authSkip, setAuthSkip] = useState(0)

  // Drawer detail views
  const [selectedAuditLog, setSelectedAuditLog] = useState<AuditLog | null>(null)
  const [selectedAgentLog, setSelectedAgentLog] = useState<AgentLog | null>(null)

  // Query parameters mapping
  const auditParams = {
    limit,
    skip: auditSkip,
    search: search || undefined,
    user_id: auditUser || undefined,
    role: auditRole || undefined,
    action: auditAction || undefined,
    resource_type: auditResource || undefined,
    start_date: startDate || undefined,
    end_date: endDate || undefined,
  }

  const agentParams = {
    limit,
    skip: agentSkip,
    agent: agentName || undefined,
    status: agentStatus || undefined,
    session: agentSession || undefined,
    start_date: startDate || undefined,
    end_date: endDate || undefined,
  }

  const authParams = {
    limit,
    skip: authSkip,
    search: search || undefined,
    start_date: startDate || undefined,
    end_date: endDate || undefined,
  }

  // React Query Hooks
  const {
    data: auditData,
    isLoading: isAuditLoading,
    isError: isAuditError,
    error: auditError,
    refetch: refetchAudit,
  } = useAuditLogs(auditParams)

  const {
    data: agentData,
    isLoading: isAgentLoading,
    isError: isAgentError,
    error: agentError,
    refetch: refetchAgent,
  } = useAgentLogs(agentParams)

  const {
    data: authData,
    isLoading: isAuthLoading,
    isError: isAuthError,
    error: authError,
    refetch: refetchAuth,
  } = useAuthenticationLogs(authParams)

  // Format Helper: ISO date strings
  const formatDate = (isoStr: string) => {
    if (!isoStr) return ''
    return new Date(isoStr).toLocaleString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  // Clipboard Copier
  const handleCopyJson = (obj: any) => {
    const jsonStr = JSON.stringify(obj, null, 2)
    navigator.clipboard.writeText(jsonStr)
    toast.success('JSON copied to clipboard')
  }

  // Reset page skips when filters change
  const handleTabChange = (tab: ActiveTab) => {
    setActiveTab(tab)
    setSearch('')
    setStartDate('')
    setEndDate('')
  }

  // Render badge helper for agent runs
  const getAgentStatusBadge = (statusStr: string) => {
    switch (statusStr.toLowerCase()) {
      case 'completed':
        return (
          <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200 font-semibold gap-1 hover:bg-emerald-50">
            <CheckCircle2 className="h-3 w-3" />
            completed
          </Badge>
        )
      case 'failed':
        return (
          <Badge className="bg-rose-50 text-rose-700 border-rose-200 font-semibold gap-1 hover:bg-rose-50">
            <XCircle className="h-3 w-3" />
            failed
          </Badge>
        )
      default:
        return (
          <Badge className="bg-amber-50 text-amber-700 border-amber-200 font-semibold gap-1 hover:bg-amber-50 animate-pulse">
            <Clock className="h-3 w-3" />
            started
          </Badge>
        )
    }
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 relative">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 flex items-center gap-2.5">
            <Activity className="h-8 w-8 text-teal-600 animate-pulse" />
            System Logs & Audit Center
          </h1>
          <p className="text-slate-500 mt-1">
            Centralized platform visibility, security audit trails, and AI agent execution logs.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={() => {
              if (activeTab === 'audit') refetchAudit()
              else if (activeTab === 'agent') refetchAgent()
              else refetchAuth()
            }}
            variant="outline"
            className="border-slate-200 shadow-sm font-semibold hover:bg-slate-50"
          >
            Refresh Feed
          </Button>
          <Button
            onClick={() => toast.success('Log export query is queued for backup archives')}
            variant="default"
            className="bg-teal-600 hover:bg-teal-700 text-white font-semibold flex items-center gap-1.5 shadow"
          >
            <Download className="h-4 w-4" />
            Export Logs
          </Button>
        </div>
      </div>

      {/* Tabs Controller */}
      <div className="flex border-b border-slate-200">
        <button
          onClick={() => handleTabChange('audit')}
          className={`flex-1 sm:flex-none px-6 py-3.5 text-sm font-bold border-b-2 transition-all flex items-center justify-center gap-2 ${
            activeTab === 'audit'
              ? 'border-teal-600 text-teal-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Shield className="h-4 w-4" />
          Audit Logs
        </button>
        <button
          onClick={() => handleTabChange('agent')}
          className={`flex-1 sm:flex-none px-6 py-3.5 text-sm font-bold border-b-2 transition-all flex items-center justify-center gap-2 ${
            activeTab === 'agent'
              ? 'border-teal-600 text-teal-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Cpu className="h-4 w-4" />
          Agent Logs
        </button>
        <button
          onClick={() => handleTabChange('auth')}
          className={`flex-1 sm:flex-none px-6 py-3.5 text-sm font-bold border-b-2 transition-all flex items-center justify-center gap-2 ${
            activeTab === 'auth'
              ? 'border-teal-600 text-teal-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Clock className="h-4 w-4" />
          Authentication Logs
        </button>
      </div>

      {/* Tab Specific Filters Panels */}
      <Card className="border border-slate-200 shadow-sm bg-white">
        <CardContent className="p-4 space-y-4">
          <div className="flex flex-col md:flex-row gap-4 items-stretch md:items-center justify-between">
            {/* Search Box */}
            {activeTab !== 'agent' && (
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  placeholder={
                    activeTab === 'audit'
                      ? 'Search audit by action, resource ID, or actor...'
                      : 'Search security actions...'
                  }
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value)
                    setAuditSkip(0)
                    setAuthSkip(0)
                  }}
                  className="pl-10 h-9 border-slate-200 focus:border-teal-500 focus:ring-teal-500 text-sm bg-white"
                />
              </div>
            )}

            {/* Date Filters Range */}
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-semibold text-slate-500 flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5 text-teal-600" />
                Date Range:
              </span>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => {
                  setStartDate(e.target.value)
                  setAuditSkip(0)
                  setAgentSkip(0)
                  setAuthSkip(0)
                }}
                className="h-8 py-1 px-2 border-slate-200 text-xs rounded bg-white w-[130px] focus:border-teal-500"
              />
              <span className="text-xs text-slate-400">to</span>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => {
                  setEndDate(e.target.value)
                  setAuditSkip(0)
                  setAgentSkip(0)
                  setAuthSkip(0)
                }}
                className="h-8 py-1 px-2 border-slate-200 text-xs rounded bg-white w-[130px] focus:border-teal-500"
              />
            </div>
          </div>

          {/* Audit Tab dropdowns */}
          {activeTab === 'audit' && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-3 border-t border-slate-100">
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
                  Filter by Action
                </label>
                <select
                  value={auditAction}
                  onChange={(e) => {
                    setAuditAction(e.target.value)
                    setAuditSkip(0)
                  }}
                  className="w-full h-8 text-xs bg-white border border-slate-200 rounded px-2 text-slate-700 outline-none focus:border-teal-500 cursor-pointer"
                >
                  <option value="">All Actions</option>
                  <option value="ADMIN_CREATED">Admin Created</option>
                  <option value="ADMIN_ENABLED">Admin Enabled</option>
                  <option value="ADMIN_DISABLED">Admin Disabled</option>
                  <option value="DOCTOR_APPROVED">Doctor Approved</option>
                  <option value="DOCTOR_REJECTED">Doctor Rejected</option>
                  <option value="DOCTOR_SUSPENDED">Doctor Suspended</option>
                  <option value="DOCTOR_REACTIVATED">Doctor Reactivated</option>
                  <option value="USER_ACTIVATED">User Activated</option>
                  <option value="USER_SUSPENDED">User Suspended</option>
                  <option value="PRESCRIPTION_CREATED">Prescription Created</option>
                  <option value="APPOINTMENT_CREATED">Appointment Created</option>
                </select>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
                  Target Resource
                </label>
                <select
                  value={auditResource}
                  onChange={(e) => {
                    setAuditResource(e.target.value)
                    setAuditSkip(0)
                  }}
                  className="w-full h-8 text-xs bg-white border border-slate-200 rounded px-2 text-slate-700 outline-none focus:border-teal-500 cursor-pointer"
                >
                  <option value="">All Resources</option>
                  <option value="user">user</option>
                  <option value="doctor_profile">doctor_profile</option>
                  <option value="appointment">appointment</option>
                  <option value="consultation">consultation</option>
                  <option value="prescription">prescription</option>
                  <option value="report">report</option>
                  <option value="reminder">reminder</option>
                  <option value="admin">admin</option>
                </select>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
                  Filter by Role
                </label>
                <select
                  value={auditRole}
                  onChange={(e) => {
                    setAuditRole(e.target.value)
                    setAuditSkip(0)
                  }}
                  className="w-full h-8 text-xs bg-white border border-slate-200 rounded px-2 text-slate-700 outline-none focus:border-teal-500 cursor-pointer"
                >
                  <option value="">All Roles</option>
                  <option value="admin">admin</option>
                  <option value="doctor">doctor</option>
                  <option value="patient">patient</option>
                </select>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
                  Specific User ID
                </label>
                <Input
                  placeholder="Actor user ID..."
                  value={auditUser}
                  onChange={(e) => {
                    setAuditUser(e.target.value)
                    setAuditSkip(0)
                  }}
                  className="h-8 border-slate-200 text-xs px-2 focus:border-teal-500"
                />
              </div>
            </div>
          )}

          {/* Agent Tab specific controls */}
          {activeTab === 'agent' && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 border-t border-slate-100">
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
                  Filter by Agent
                </label>
                <select
                  value={agentName}
                  onChange={(e) => {
                    setAgentName(e.target.value)
                    setAgentSkip(0)
                  }}
                  className="w-full h-8 text-xs bg-white border border-slate-200 rounded px-2 text-slate-700 outline-none focus:border-teal-500 cursor-pointer"
                >
                  <option value="">All Agents</option>
                  <option value="router_agent">router_agent</option>
                  <option value="rag_agent">rag_agent</option>
                  <option value="evaluator_agent">evaluator_agent</option>
                  <option value="triage_agent">triage_agent</option>
                </select>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
                  Status
                </label>
                <select
                  value={agentStatus}
                  onChange={(e) => {
                    setAgentStatus(e.target.value)
                    setAgentSkip(0)
                  }}
                  className="w-full h-8 text-xs bg-white border border-slate-200 rounded px-2 text-slate-700 outline-none focus:border-teal-500 cursor-pointer"
                >
                  <option value="">All Statuses</option>
                  <option value="started">started</option>
                  <option value="completed">completed</option>
                  <option value="failed">failed</option>
                </select>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
                  Chat Session ID
                </label>
                <Input
                  placeholder="Session uuid..."
                  value={agentSession}
                  onChange={(e) => {
                    setAgentSession(e.target.value)
                    setAgentSkip(0)
                  }}
                  className="h-8 border-slate-200 text-xs px-2 focus:border-teal-500"
                />
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Main Logs Table Data Content */}
      <Card className="border border-slate-200 shadow-sm bg-white overflow-hidden">
        <CardContent className="p-0">
          {/* Tab 1: Audit Logs */}
          {activeTab === 'audit' && (
            <>
              {isAuditLoading ? (
                <div className="p-8 space-y-3">
                  <div className="h-5 bg-slate-100 rounded animate-pulse w-full" />
                  <div className="h-10 bg-slate-50 rounded animate-pulse w-full" />
                  <div className="h-10 bg-slate-50 rounded animate-pulse w-full" />
                </div>
              ) : isAuditError ? (
                <div className="py-12 text-center text-slate-500">
                  <AlertCircle className="h-8 w-8 text-rose-500 mx-auto mb-2" />
                  <h4 className="font-bold text-slate-800 text-sm">Failed to retrieve audit log feed</h4>
                  <p className="text-xs mt-1">{(auditError as Error)?.message || 'Audit feed is currently locked.'}</p>
                </div>
              ) : !auditData || auditData.logs.length === 0 ? (
                <div className="py-16 text-center text-slate-500">
                  <Search className="h-8 w-8 text-slate-400 mx-auto mb-2" />
                  <h4 className="font-bold text-slate-800 text-sm">No audit logs match criteria</h4>
                  <p className="text-xs mt-1">Adjust search parameters or calendar spans.</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm border-collapse">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-100 text-slate-500 font-semibold text-xs uppercase tracking-wider">
                        <th className="py-3 px-6">Timestamp</th>
                        <th className="py-3 px-6">Action</th>
                        <th className="py-3 px-6">Resource Type</th>
                        <th className="py-3 px-6">Resource ID</th>
                        <th className="py-3 px-6">Actor ID</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 cursor-pointer">
                      {auditData.logs.map((log) => (
                        <tr
                          key={log.id}
                          onClick={() => setSelectedAuditLog(log)}
                          className="hover:bg-slate-50/70 transition-colors"
                        >
                          <td className="py-3.5 px-6 text-xs text-slate-500">
                            {formatDate(log.created_at)}
                          </td>
                          <td className="py-3.5 px-6 font-semibold text-slate-800 text-xs">
                            <span className="bg-teal-50 text-teal-800 font-semibold border border-teal-100 px-2 py-0.5 rounded text-[10px]">
                              {log.action}
                            </span>
                          </td>
                          <td className="py-3.5 px-6 text-slate-600 text-xs capitalize">
                            {log.resource_type}
                          </td>
                          <td className="py-3.5 px-6 text-xs text-slate-400 font-mono truncate max-w-[140px]">
                            {log.resource_id || 'System'}
                          </td>
                          <td className="py-3.5 px-6 text-xs text-slate-400 font-mono truncate max-w-[140px]">
                            {log.user_id || 'Anon'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>

                  {/* Audit Pagination */}
                  {auditData.total > limit && (
                    <div className="flex items-center justify-between border-t border-slate-100 py-3.5 px-6 text-xs text-slate-600 bg-slate-50/30">
                      <span>
                        Showing <span className="font-semibold">{auditSkip + 1}</span> to{' '}
                        <span className="font-semibold">
                          {Math.min(auditSkip + limit, auditData.total)}
                        </span>{' '}
                        of <span className="font-semibold">{auditData.total}</span> records
                      </span>
                      <div className="flex gap-2">
                        <Button
                          onClick={() => setAuditSkip(Math.max(0, auditSkip - limit))}
                          disabled={auditSkip === 0}
                          variant="outline"
                          size="sm"
                          className="h-7 text-[10px]"
                        >
                          <ChevronLeft className="h-3 w-3 mr-1" />
                          Prev
                        </Button>
                        <Button
                          onClick={() => setAuditSkip(auditSkip + limit)}
                          disabled={auditSkip + limit >= auditData.total}
                          variant="outline"
                          size="sm"
                          className="h-7 text-[10px]"
                        >
                          Next
                          <ChevronRight className="h-3 w-3 ml-1" />
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}

          {/* Tab 2: Agent Logs */}
          {activeTab === 'agent' && (
            <>
              {isAgentLoading ? (
                <div className="p-8 space-y-3">
                  <div className="h-5 bg-slate-100 rounded animate-pulse w-full" />
                  <div className="h-10 bg-slate-50 rounded animate-pulse w-full" />
                  <div className="h-10 bg-slate-50 rounded animate-pulse w-full" />
                </div>
              ) : isAgentError ? (
                <div className="py-12 text-center text-slate-500">
                  <AlertCircle className="h-8 w-8 text-rose-500 mx-auto mb-2" />
                  <h4 className="font-bold text-slate-800 text-sm">Failed to retrieve agent execution steps</h4>
                  <p className="text-xs mt-1">{(agentError as Error)?.message || 'Database connection error.'}</p>
                </div>
              ) : !agentData || agentData.logs.length === 0 ? (
                <div className="py-16 text-center text-slate-500">
                  <Search className="h-8 w-8 text-slate-400 mx-auto mb-2" />
                  <h4 className="font-bold text-slate-800 text-sm">No agent traces match criteria</h4>
                  <p className="text-xs mt-1">Adjust session ID or dates.</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm border-collapse">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-100 text-slate-500 font-semibold text-xs uppercase tracking-wider">
                        <th className="py-3 px-6">Timestamp</th>
                        <th className="py-3 px-6">Agent Name</th>
                        <th className="py-3 px-6">Session ID</th>
                        <th className="py-3 px-6 text-right">Latency (ms)</th>
                        <th className="py-3 px-6">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 cursor-pointer">
                      {agentData.logs.map((log) => (
                        <tr
                          key={log.id}
                          onClick={() => setSelectedAgentLog(log)}
                          className="hover:bg-slate-50/70 transition-colors"
                        >
                          <td className="py-3.5 px-6 text-xs text-slate-500">
                            {formatDate(log.created_at)}
                          </td>
                          <td className="py-3.5 px-6 font-semibold text-slate-800 text-xs">
                            {log.agent_name}
                          </td>
                          <td className="py-3.5 px-6 text-xs text-slate-400 font-mono truncate max-w-[140px]">
                            {log.session_id || 'System run'}
                          </td>
                          <td className="py-3.5 px-6 text-right font-medium text-slate-700 text-xs">
                            {log.latency_ms.toFixed(0)} ms
                          </td>
                          <td className="py-3.5 px-6">
                            {getAgentStatusBadge(log.status)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>

                  {/* Agent Pagination */}
                  {agentData.total > limit && (
                    <div className="flex items-center justify-between border-t border-slate-100 py-3.5 px-6 text-xs text-slate-600 bg-slate-50/30">
                      <span>
                        Showing <span className="font-semibold">{agentSkip + 1}</span> to{' '}
                        <span className="font-semibold">
                          {Math.min(agentSkip + limit, agentData.total)}
                        </span>{' '}
                        of <span className="font-semibold">{agentData.total}</span> records
                      </span>
                      <div className="flex gap-2">
                        <Button
                          onClick={() => setAgentSkip(Math.max(0, agentSkip - limit))}
                          disabled={agentSkip === 0}
                          variant="outline"
                          size="sm"
                          className="h-7 text-[10px]"
                        >
                          <ChevronLeft className="h-3 w-3 mr-1" />
                          Prev
                        </Button>
                        <Button
                          onClick={() => setAgentSkip(agentSkip + limit)}
                          disabled={agentSkip + limit >= agentData.total}
                          variant="outline"
                          size="sm"
                          className="h-7 text-[10px]"
                        >
                          Next
                          <ChevronRight className="h-3 w-3 ml-1" />
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}

          {/* Tab 3: Authentication Logs */}
          {activeTab === 'auth' && (
            <>
              {isAuthLoading ? (
                <div className="p-8 space-y-3">
                  <div className="h-5 bg-slate-100 rounded animate-pulse w-full" />
                  <div className="h-10 bg-slate-50 rounded animate-pulse w-full" />
                  <div className="h-10 bg-slate-50 rounded animate-pulse w-full" />
                </div>
              ) : isAuthError ? (
                <div className="py-12 text-center text-slate-500">
                  <AlertCircle className="h-8 w-8 text-rose-500 mx-auto mb-2" />
                  <h4 className="font-bold text-slate-800 text-sm">Failed to retrieve authentication security logs</h4>
                  <p className="text-xs mt-1">{(authError as Error)?.message || 'Endpoint connection failed.'}</p>
                </div>
              ) : !authData || authData.logs.length === 0 ? (
                <div className="py-16 text-center text-slate-500">
                  <Search className="h-8 w-8 text-slate-400 mx-auto mb-2" />
                  <h4 className="font-bold text-slate-800 text-sm">No authentication actions match criteria</h4>
                  <p className="text-xs mt-1">Adjust search parameters or calendar spans.</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm border-collapse">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-100 text-slate-500 font-semibold text-xs uppercase tracking-wider">
                        <th className="py-3 px-6">Timestamp</th>
                        <th className="py-3 px-6">Action / Event</th>
                        <th className="py-3 px-6">IP Address</th>
                        <th className="py-3 px-6">User Agent</th>
                        <th className="py-3 px-6">Target User ID</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 cursor-pointer">
                      {authData.logs.map((log) => (
                        <tr
                          key={log.id}
                          onClick={() => setSelectedAuditLog(log)}
                          className="hover:bg-slate-50/70 transition-colors"
                        >
                          <td className="py-3.5 px-6 text-xs text-slate-500">
                            {formatDate(log.created_at)}
                          </td>
                          <td className="py-3.5 px-6 font-semibold text-slate-800 text-xs">
                            <span className="bg-teal-50 text-teal-800 font-semibold border border-teal-100 px-2 py-0.5 rounded text-[10px]">
                              {log.action}
                            </span>
                          </td>
                          <td className="py-3.5 px-6 text-slate-600 text-xs">
                            {log.ip_address || 'unknown'}
                          </td>
                          <td className="py-3.5 px-6 text-xs text-slate-400 max-w-[200px] truncate">
                            {log.user_agent || 'unknown'}
                          </td>
                          <td className="py-3.5 px-6 text-xs text-slate-400 font-mono truncate max-w-[140px]">
                            {log.user_id || 'system'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>

                  {/* Auth Pagination */}
                  {authData.total > limit && (
                    <div className="flex items-center justify-between border-t border-slate-100 py-3.5 px-6 text-xs text-slate-600 bg-slate-50/30">
                      <span>
                        Showing <span className="font-semibold">{authSkip + 1}</span> to{' '}
                        <span className="font-semibold">
                          {Math.min(authSkip + limit, authData.total)}
                        </span>{' '}
                        of <span className="font-semibold">{authData.total}</span> records
                      </span>
                      <div className="flex gap-2">
                        <Button
                          onClick={() => setAuthSkip(Math.max(0, authSkip - limit))}
                          disabled={authSkip === 0}
                          variant="outline"
                          size="sm"
                          className="h-7 text-[10px]"
                        >
                          <ChevronLeft className="h-3 w-3 mr-1" />
                          Prev
                        </Button>
                        <Button
                          onClick={() => setAuthSkip(authSkip + limit)}
                          disabled={authSkip + limit >= authData.total}
                          variant="outline"
                          size="sm"
                          className="h-7 text-[10px]"
                        >
                          Next
                          <ChevronRight className="h-3 w-3 ml-1" />
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* DETAIL SLIDE-OVER DRAWER (AUDIT & AUTHENTICATION DETAILED VIEW) */}
      {selectedAuditLog && (
        <div className="fixed inset-0 z-50 overflow-hidden" aria-labelledby="slide-over-title" role="dialog" aria-modal="true">
          <div className="absolute inset-0 overflow-hidden">
            {/* Background Overlay */}
            <div
              onClick={() => setSelectedAuditLog(null)}
              className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity duration-300"
            />

            <div className="pointer-events-none fixed inset-y-0 right-0 flex max-w-full pl-10">
              <div className="pointer-events-auto w-screen max-w-xl transform transition-all duration-300 ease-in-out bg-white shadow-2xl flex flex-col h-full border-l border-slate-100">
                {/* Header */}
                <div className="px-6 py-5 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <Shield className="h-5 w-5 text-teal-600" />
                    <h2 className="text-base font-bold text-slate-800" id="slide-over-title">
                      Detailed Audit Statement
                    </h2>
                  </div>
                  <button
                    onClick={() => setSelectedAuditLog(null)}
                    className="rounded-md text-slate-400 hover:text-slate-500 focus:outline-none hover:bg-slate-100 p-1"
                  >
                    <XCircle className="h-5 w-5" />
                  </button>
                </div>

                {/* Body */}
                <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
                  {/* Event Summary block */}
                  <div className="p-4 border border-slate-200 rounded-xl bg-slate-50 flex justify-between items-center">
                    <div>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                        Audited Action
                      </p>
                      <h4 className="text-base font-extrabold text-slate-800 mt-0.5">
                        {selectedAuditLog.action}
                      </h4>
                    </div>
                    <Badge className="bg-teal-50 text-teal-700 border border-teal-200 font-semibold uppercase text-[10px]">
                      Verified
                    </Badge>
                  </div>

                  {/* Metadata Table */}
                  <div className="space-y-4">
                    <h4 className="font-bold text-slate-800 text-xs tracking-wide uppercase flex items-center gap-1.5">
                      <Clock className="h-4 w-4 text-teal-600" />
                      Audited Properties
                    </h4>
                    <div className="border border-slate-200 rounded-xl overflow-hidden text-xs divide-y divide-slate-100 bg-white">
                      <div className="flex py-3 px-4 justify-between items-center">
                        <span className="text-slate-400 font-semibold">Record Log ID</span>
                        <span className="font-mono text-slate-700">{selectedAuditLog.id}</span>
                      </div>
                      <div className="flex py-3 px-4 justify-between items-center">
                        <span className="text-slate-400 font-semibold">Audited Resource</span>
                        <span className="capitalize text-slate-700">
                          {selectedAuditLog.resource_type} ({selectedAuditLog.resource_id || 'System'})
                        </span>
                      </div>
                      <div className="flex py-3 px-4 justify-between items-center">
                        <span className="text-slate-400 font-semibold">Event Timestamp</span>
                        <span className="text-slate-700">{formatDate(selectedAuditLog.created_at)}</span>
                      </div>
                      <div className="flex py-3 px-4 justify-between items-center">
                        <span className="text-slate-400 font-semibold">Actor User ID</span>
                        <span className="font-mono text-slate-700">{selectedAuditLog.user_id || 'system'}</span>
                      </div>
                      {selectedAuditLog.ip_address && (
                        <div className="flex py-3 px-4 justify-between items-center">
                          <span className="text-slate-400 font-semibold">Client IP</span>
                          <span className="text-slate-700">{selectedAuditLog.ip_address}</span>
                        </div>
                      )}
                      {selectedAuditLog.user_agent && (
                        <div className="py-3 px-4 space-y-1">
                          <p className="text-slate-400 font-semibold">Client User Agent</p>
                          <p className="text-slate-600 font-medium leading-relaxed leading-3 text-[11px] truncate max-w-full">
                            {selectedAuditLog.user_agent}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Pre/Post JSON States */}
                  <div className="space-y-3">
                    <h4 className="font-bold text-slate-800 text-xs tracking-wide uppercase flex items-center gap-1.5">
                      <FileCode className="h-4 w-4 text-teal-600" />
                      State Modification (Old vs New Values)
                    </h4>
                    <div className="relative">
                      <pre className="bg-slate-950 text-emerald-400 p-4 rounded-xl overflow-x-auto font-mono text-[11px] max-h-[300px] leading-relaxed shadow-inner">
                        <code>
                          {JSON.stringify(
                            {
                              old_value: selectedAuditLog.old_value,
                              new_value: selectedAuditLog.new_value,
                            },
                            null,
                            2
                          )}
                        </code>
                      </pre>
                      <button
                        onClick={() => handleCopyJson(selectedAuditLog)}
                        className="absolute right-3.5 top-3.5 bg-slate-900/60 hover:bg-slate-900 border border-slate-800 rounded p-1.5 text-slate-400 hover:text-slate-100 transition-colors"
                        title="Copy entire audit log entry JSON"
                      >
                        <Copy className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Footer action */}
                <div className="px-6 py-4 border-t border-slate-200 bg-slate-50 flex gap-3">
                  <Button
                    onClick={() => handleCopyJson(selectedAuditLog)}
                    className="flex-1 bg-teal-600 hover:bg-teal-700 text-white font-semibold flex justify-center items-center gap-1.5"
                  >
                    Copy Audit JSON
                  </Button>
                  <Button
                    onClick={() => setSelectedAuditLog(null)}
                    variant="outline"
                    className="border-slate-200 text-slate-700"
                  >
                    Dismiss
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* DETAIL SLIDE-OVER DRAWER (AGENT LOG DETAILED VIEW) */}
      {selectedAgentLog && (
        <div className="fixed inset-0 z-50 overflow-hidden" aria-labelledby="slide-over-title" role="dialog" aria-modal="true">
          <div className="absolute inset-0 overflow-hidden">
            {/* Background Overlay */}
            <div
              onClick={() => setSelectedAgentLog(null)}
              className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity duration-300"
            />

            <div className="pointer-events-none fixed inset-y-0 right-0 flex max-w-full pl-10">
              <div className="pointer-events-auto w-screen max-w-2xl transform transition-all duration-300 ease-in-out bg-white shadow-2xl flex flex-col h-full border-l border-slate-100">
                {/* Header */}
                <div className="px-6 py-5 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <Cpu className="h-5 w-5 text-teal-600" />
                    <h2 className="text-base font-bold text-slate-800" id="slide-over-title">
                      AI Agent Execution Log Trace
                    </h2>
                  </div>
                  <button
                    onClick={() => setSelectedAgentLog(null)}
                    className="rounded-md text-slate-400 hover:text-slate-500 focus:outline-none hover:bg-slate-100 p-1"
                  >
                    <XCircle className="h-5 w-5" />
                  </button>
                </div>

                {/* Body */}
                <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
                  {/* Event summary block */}
                  <div className="p-4 border border-slate-200 rounded-xl bg-slate-50 flex justify-between items-center">
                    <div>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                        Executing Agent
                      </p>
                      <h4 className="text-base font-extrabold text-slate-800 mt-0.5">
                        {selectedAgentLog.agent_name}
                      </h4>
                    </div>
                    {getAgentStatusBadge(selectedAgentLog.status)}
                  </div>

                  {/* Metadata Table */}
                  <div className="space-y-4">
                    <h4 className="font-bold text-slate-800 text-xs tracking-wide uppercase flex items-center gap-1.5">
                      <Clock className="h-4 w-4 text-teal-600" />
                      Execution Metadata
                    </h4>
                    <div className="border border-slate-200 rounded-xl overflow-hidden text-xs divide-y divide-slate-100 bg-white">
                      <div className="flex py-3 px-4 justify-between items-center">
                        <span className="text-slate-400 font-semibold">Workflow ID</span>
                        <span className="font-mono text-slate-700">{selectedAgentLog.workflow_id}</span>
                      </div>
                      <div className="flex py-3 px-4 justify-between items-center">
                        <span className="text-slate-400 font-semibold">Chat Session ID</span>
                        <span className="font-mono text-slate-700">
                          {selectedAgentLog.session_id || 'None (General Run)'}
                        </span>
                      </div>
                      <div className="flex py-3 px-4 justify-between items-center">
                        <span className="text-slate-400 font-semibold">Latency (ms)</span>
                        <span className="font-semibold text-slate-700">
                          {selectedAgentLog.latency_ms.toFixed(1)} ms
                        </span>
                      </div>
                      <div className="flex py-3 px-4 justify-between items-center">
                        <span className="text-slate-400 font-semibold">LLM Token Usage</span>
                        <span className="text-slate-700">
                          Prompt: {selectedAgentLog.token_usage?.prompt ?? 0} | Completion:{' '}
                          {selectedAgentLog.token_usage?.completion ?? 0} | Total:{' '}
                          {selectedAgentLog.token_usage?.total ?? 0}
                        </span>
                      </div>
                      <div className="flex py-3 px-4 justify-between items-center">
                        <span className="text-slate-400 font-semibold">Execution Timestamp</span>
                        <span className="text-slate-700">{formatDate(selectedAgentLog.created_at)}</span>
                      </div>
                    </div>
                  </div>

                  {/* Error Trace if Failed */}
                  {selectedAgentLog.status === 'failed' && selectedAgentLog.error_message && (
                    <div className="p-4 border border-rose-200 bg-rose-50 rounded-xl space-y-1.5">
                      <p className="text-xs font-bold text-rose-800 flex items-center gap-1.5">
                        <AlertTriangle className="h-4 w-4" />
                        Run Exception Error Message
                      </p>
                      <p className="font-mono text-xs text-rose-700 bg-white/50 p-2.5 rounded border border-rose-100 overflow-x-auto leading-relaxed">
                        {selectedAgentLog.error_message}
                      </p>
                    </div>
                  )}

                  {/* Input / Output Payloads JSON */}
                  <div className="space-y-3">
                    <h4 className="font-bold text-slate-800 text-xs tracking-wide uppercase flex items-center gap-1.5">
                      <FileCode className="h-4 w-4 text-teal-600" />
                      Payload Traces (Prompt Inputs & LLM Responses)
                    </h4>
                    <div className="relative">
                      <pre className="bg-slate-950 text-teal-400 p-4 rounded-xl overflow-x-auto font-mono text-[11px] max-h-[300px] leading-relaxed shadow-inner">
                        <code>
                          {JSON.stringify(
                            {
                              input_payload: selectedAgentLog.input_payload,
                              output_payload: selectedAgentLog.output_payload,
                            },
                            null,
                            2
                          )}
                        </code>
                      </pre>
                      <button
                        onClick={() => handleCopyJson(selectedAgentLog)}
                        className="absolute right-3.5 top-3.5 bg-slate-900/60 hover:bg-slate-900 border border-slate-800 rounded p-1.5 text-slate-400 hover:text-slate-100 transition-colors"
                        title="Copy entire agent trace log JSON"
                      >
                        <Copy className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Footer action */}
                <div className="px-6 py-4 border-t border-slate-200 bg-slate-50 flex gap-3">
                  <Button
                    onClick={() => handleCopyJson(selectedAgentLog)}
                    className="flex-1 bg-teal-600 hover:bg-teal-700 text-white font-semibold flex justify-center items-center gap-1.5"
                  >
                    Copy Trace JSON
                  </Button>
                  <Button
                    onClick={() => setSelectedAgentLog(null)}
                    variant="outline"
                    className="border-slate-200 text-slate-700"
                  >
                    Dismiss
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
