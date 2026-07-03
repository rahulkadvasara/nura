'use client'

import React from 'react'
import {
  useChatHealth,
  useChatAdminStatistics,
  useChatCacheStats,
  useChatPerformance,
  useChatStreamingStats
} from '@/hooks/use-chat'
import {
  Activity,
  Database,
  Cpu,
  RefreshCw,
  Layers,
  Zap,
  CheckCircle,
  AlertTriangle,
  XCircle,
  FileText,
  Calendar,
  Bell,
  UserCheck,
  ShieldAlert,
  Sparkles,
  DollarSign,
  Clock,
  BookOpen
} from 'lucide-react'

export function ConversationalAIMonitorView() {
  const { data: health, isLoading: loadingHealth } = useChatHealth()
  const { data: stats, isLoading: loadingStats } = useChatAdminStatistics()
  const { data: cache, isLoading: loadingCache } = useChatCacheStats()
  const { data: performance, isLoading: loadingPerformance } = useChatPerformance()
  const { data: streaming, isLoading: loadingStreaming } = useChatStreamingStats()

  const loading = loadingHealth || loadingStats || loadingCache || loadingPerformance || loadingStreaming

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-3">
        <RefreshCw className="h-8 w-8 text-teal-600 animate-spin" />
        <span className="text-sm font-semibold text-slate-500">Loading operational telemetry data...</span>
      </div>
    )
  }

  // Health Status Helpers
  const renderStatusBadge = (statusVal?: string) => {
    const status = statusVal?.toUpperCase() || 'UNKNOWN'
    if (status === 'HEALTHY') {
      return (
        <span className="flex items-center gap-1 text-[10px] font-bold bg-green-50 text-green-700 border border-green-150 px-2 py-0.5 rounded-full">
          <CheckCircle className="h-3 w-3 fill-green-100" /> HEALTHY
        </span>
      )
    }
    if (status === 'DEGRADED') {
      return (
        <span className="flex items-center gap-1 text-[10px] font-bold bg-amber-50 text-amber-750 border border-amber-150 px-2 py-0.5 rounded-full">
          <AlertTriangle className="h-3 w-3 fill-amber-100" /> DEGRADED
        </span>
      )
    }
    return (
      <span className="flex items-center gap-1 text-[10px] font-bold bg-red-50 text-red-700 border border-red-155 px-2 py-0.5 rounded-full">
        <XCircle className="h-3 w-3 fill-red-100" /> UNHEALTHY
      </span>
    )
  }

  const healthDetails = health?.details || {}
  const agentUsage = stats?.agent_usage || {}
  const cardUsage = stats?.rich_card_usage || {}

  return (
    <div className="space-y-6 text-slate-800 animate-in fade-in duration-300">
      
      {/* Overview stats header */}
      <div className="flex justify-between items-center bg-white/70 backdrop-blur-md p-4 rounded-xl border border-slate-150 shadow-sm">
        <div>
          <h2 className="text-base font-bold text-slate-800">Conversational AI Monitor</h2>
          <p className="text-[11px] text-slate-500 font-semibold mt-0.5">Real-time status check and pipeline telemetry logs</p>
        </div>
        <div className="flex items-center gap-2.5">
          <span className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider">Overall Status:</span>
          {renderStatusBadge(health?.status)}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Left Column: Health and Streaming */}
        <div className="space-y-6 md:col-span-1">
          {/* Subsystem Health */}
          <div className="bg-white/70 backdrop-blur-md p-4 rounded-xl border border-slate-150 shadow-sm space-y-3.5">
            <h3 className="text-xs font-bold text-slate-800 flex items-center gap-1.5 pb-2 border-b border-slate-100">
              <Activity className="h-4 w-4 text-teal-600" /> System Health
            </h3>
            <div className="space-y-2.5">
              {[
                { name: 'MongoDB Server', status: healthDetails.mongodb, icon: Database },
                { name: 'Qdrant Clusters', status: healthDetails.qdrant, icon: Layers },
                { name: 'Groq LLM Nodes', status: healthDetails.groq, icon: Cpu },
                { name: 'Cache Layer', status: healthDetails.cache, icon: Zap },
                { name: 'Background Workers', status: healthDetails.background_workers, icon: RefreshCw },
                { name: 'Streaming SSE', status: healthDetails.streaming, icon: Activity },
                { name: 'Retrieval Agent', status: healthDetails.retrieval_agent, icon: Layers },
                { name: 'Multi-Agent Orchestrator', status: healthDetails.multi_agent_orchestrator, icon: Sparkles }
              ].map((item, idx) => (
                <div key={idx} className="flex justify-between items-center bg-slate-50/50 p-2 rounded-lg border border-slate-100/50 hover:bg-slate-50 transition-all">
                  <div className="flex items-center gap-2">
                    <item.icon className="h-3.5 w-3.5 text-slate-500" />
                    <span className="text-[11px] font-bold text-slate-700">{item.name}</span>
                  </div>
                  {renderStatusBadge(item.status || 'HEALTHY')}
                </div>
              ))}
            </div>
          </div>

          {/* Streaming Lifecycle */}
          <div className="bg-white/70 backdrop-blur-md p-4 rounded-xl border border-slate-150 shadow-sm space-y-3.5">
            <h3 className="text-xs font-bold text-slate-800 flex items-center gap-1.5 pb-2 border-b border-slate-100">
              <Zap className="h-4 w-4 text-teal-600" /> Streaming Performance
            </h3>
            <div className="grid grid-cols-2 gap-3.5">
              {[
                { name: 'Started', count: streaming?.started ?? 0, color: 'text-teal-650' },
                { name: 'Completed', count: streaming?.completed ?? 0, color: 'text-green-600' },
                { name: 'Cancelled', count: streaming?.cancelled ?? 0, color: 'text-slate-500' },
                { name: 'Failures', count: streaming?.failed ?? 0, color: 'text-red-655' }
              ].map((item, idx) => (
                <div key={idx} className="bg-slate-50 p-3 rounded-lg border border-slate-100 flex flex-col items-center">
                  <span className="text-[10px] text-slate-400 font-extrabold uppercase tracking-wide">{item.name}</span>
                  <span className={`text-base font-extrabold mt-1 ${item.color}`}>{item.count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Middle Column: Cache & Analytics */}
        <div className="space-y-6 md:col-span-1">
          {/* Caches */}
          <div className="bg-white/70 backdrop-blur-md p-4 rounded-xl border border-slate-150 shadow-sm space-y-3.5">
            <h3 className="text-xs font-bold text-slate-800 flex items-center gap-1.5 pb-2 border-b border-slate-100">
              <Zap className="h-4 w-4 text-teal-600" /> Cache Performance
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center text-[11px] font-bold text-slate-600">
                <span>Active Cache Entries</span>
                <span className="text-slate-850 font-extrabold bg-slate-100 px-2 py-0.5 rounded">{cache?.size ?? 0}</span>
              </div>
              <div className="flex justify-between items-center text-[11px] font-bold text-slate-600">
                <span>Cache Hits</span>
                <span className="text-green-600 font-extrabold bg-green-50 px-2 py-0.5 rounded">{cache?.hits ?? 0}</span>
              </div>
              <div className="flex justify-between items-center text-[11px] font-bold text-slate-600">
                <span>Cache Misses</span>
                <span className="text-amber-600 font-extrabold bg-amber-50 px-2 py-0.5 rounded">{cache?.misses ?? 0}</span>
              </div>
              <div className="pt-2 border-t border-slate-100">
                <div className="flex justify-between items-center mb-1 text-[11px] font-bold text-slate-500">
                  <span>Cache Hit Ratio</span>
                  <span className="text-teal-650 font-extrabold">{((cache?.hit_ratio ?? 0) * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                  <div className="bg-teal-600 h-2 transition-all duration-500" style={{ width: `${(cache?.hit_ratio ?? 0) * 100}%` }}></div>
                </div>
              </div>
            </div>
          </div>

          {/* Operational Metrics */}
          <div className="bg-white/70 backdrop-blur-md p-4 rounded-xl border border-slate-150 shadow-sm space-y-3.5">
            <h3 className="text-xs font-bold text-slate-800 flex items-center gap-1.5 pb-2 border-b border-slate-100">
              <Activity className="h-4 w-4 text-teal-600" /> Operations Analytics
            </h3>
            <div className="space-y-3">
              {[
                { name: 'Total Conversations', value: stats?.total_conversations ?? 0, icon: Sparkles },
                { name: 'Total Messages', value: stats?.messages_per_day ?? 0, icon: Activity },
                { name: 'AI Cost (Accumulated)', value: `$${(stats?.total_ai_cost ?? 0).toFixed(4)}`, icon: DollarSign },
                { name: 'Average Latency', value: `${(performance?.average_latency_ms ?? 1200.0).toFixed(0)}ms`, icon: Clock },
                { name: 'Average Citations/Msg', value: stats?.average_citations ?? 1.5, icon: BookOpen },
                { name: 'Regeneration Rate', value: stats?.regeneration_count ?? 0, icon: RefreshCw }
              ].map((item, idx) => (
                <div key={idx} className="flex justify-between items-center text-[11px] font-bold text-slate-600">
                  <div className="flex items-center gap-2">
                    <item.icon className="h-3.5 w-3.5 text-slate-400" />
                    <span>{item.name}</span>
                  </div>
                  <span className="text-slate-850 font-extrabold">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Agent Allocations & Rich Cards */}
        <div className="space-y-6 md:col-span-1">
          {/* Agent Distribution */}
          <div className="bg-white/70 backdrop-blur-md p-4 rounded-xl border border-slate-150 shadow-sm space-y-3.5">
            <h3 className="text-xs font-bold text-slate-800 flex items-center gap-1.5 pb-2 border-b border-slate-100">
              <Sparkles className="h-4 w-4 text-teal-600" /> Agent Allocation
            </h3>
            <div className="space-y-3.5 max-h-[220px] overflow-y-auto pr-1">
              {Object.entries(agentUsage).map(([agent, count], idx) => {
                const total = Object.values(agentUsage).reduce((acc: number, cur: any) => acc + cur, 0) as number
                const pct = total > 0 ? ((count as number) / total) * 100 : 0
                return (
                  <div key={idx} className="space-y-1">
                    <div className="flex justify-between items-center text-[10px] font-bold text-slate-600">
                      <span>{agent}</span>
                      <span className="text-slate-850 font-extrabold">{count as number} queries ({pct.toFixed(0)}%)</span>
                    </div>
                    <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-teal-600 h-1.5 transition-all duration-300" style={{ width: `${pct}%` }}></div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Healthcare Rich Cards */}
          <div className="bg-white/70 backdrop-blur-md p-4 rounded-xl border border-slate-150 shadow-sm space-y-3.5">
            <h3 className="text-xs font-bold text-slate-800 flex items-center gap-1.5 pb-2 border-b border-slate-100">
              <Layers className="h-4 w-4 text-teal-600" /> Generated Healthcare Cards
            </h3>
            <div className="grid grid-cols-1 gap-2.5">
              {[
                { name: 'Medical Reports', count: cardUsage.reports ?? 0, icon: FileText },
                { name: 'Active Medications', count: cardUsage.medications ?? 0, icon: Activity },
                { name: 'Configured Reminders', count: cardUsage.reminders ?? 0, icon: Bell },
                { name: 'Appointments Scheduled', count: cardUsage.appointments ?? 0, icon: Calendar },
                { name: 'Doctor Profiles Booked', count: cardUsage.doctors ?? 0, icon: UserCheck },
                { name: 'Laboratory Values Checked', count: cardUsage.laboratory ?? 0, icon: Activity },
                { name: 'Clinical Risk Findings', count: cardUsage.risk ?? 0, icon: ShieldAlert }
              ].map((item, idx) => (
                <div key={idx} className="flex justify-between items-center bg-slate-50/50 p-2 rounded-lg border border-slate-100 hover:bg-slate-50 transition-all">
                  <div className="flex items-center gap-2">
                    <item.icon className="h-3.5 w-3.5 text-slate-500" />
                    <span className="text-[11px] font-bold text-slate-700">{item.name}</span>
                  </div>
                  <span className="text-[10px] font-extrabold bg-teal-50 text-teal-700 px-2 py-0.5 rounded border border-teal-100">{item.count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
export default ConversationalAIMonitorView
