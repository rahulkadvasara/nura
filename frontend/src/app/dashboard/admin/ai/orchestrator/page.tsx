'use client'

import { useState } from 'react'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import {
  useOrchestratorExecute,
  useOrchestratorDebug,
  useOrchestratorStatistics,
  useOrchestratorHealth
} from '@/hooks/use-ai'
import {
  Sparkles,
  RefreshCw,
  Terminal,
  Activity,
  Cpu,
  Clock,
  Zap,
  CheckCircle2,
  AlertTriangle,
  Play,
  ArrowRight,
  Database
} from 'lucide-react'

function OrchestratorHealthStatus() {
  const { data: health, isLoading, isError, refetch } = useOrchestratorHealth()

  return (
    <Card className="shadow-sm border-slate-200 bg-white px-4 py-2 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="flex flex-col">
          <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">Subsystems Health</span>
          {isLoading ? (
            <span className="text-xs font-medium text-slate-500 flex items-center gap-1">
              <RefreshCw className="h-3 w-3 animate-spin" /> Check...
            </span>
          ) : isError ? (
            <span className="text-xs font-medium text-red-500 flex items-center gap-1">
              <AlertTriangle className="h-3.5 w-3.5" /> Offline
            </span>
          ) : (
            <div className="flex items-center gap-2 mt-0.5">
              <span className={`h-2 w-2 rounded-full ${health?.groq?.reachable ? 'bg-emerald-500' : 'bg-red-500'}`} title="Groq" />
              <span className={`h-2 w-2 rounded-full ${health?.vector?.connected ? 'bg-emerald-500' : 'bg-red-500'}`} title="Qdrant" />
              <span className="text-[11px] text-slate-500 font-medium">Groq & Qdrant Connected</span>
            </div>
          )}
        </div>
      </div>
      <Button variant="ghost" size="sm" onClick={() => refetch()} className="p-1 h-auto text-slate-400 hover:text-slate-700">
        <RefreshCw className="h-3.5 w-3.5" />
      </Button>
    </Card>
  )
}

function OrchestratorDashboardContent() {
  const [query, setQuery] = useState('My patient has chest pain and needs a cardiologist recommendations.')
  const [patientId, setPatientId] = useState('65f7c32b5e28a425fca68341')
  const [session_id, setSessionId] = useState('')
  const [conversation_id, setConversationId] = useState('')
  const [debugMode, setDebugMode] = useState(true)

  const executeMutation = useOrchestratorExecute()
  const debugMutation = useOrchestratorDebug()
  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useOrchestratorStatistics()

  const handleRun = () => {
    const payload = {
      query,
      patient_id: patientId || undefined,
      session_id: session_id || undefined,
      conversation_id: conversation_id || undefined,
      debug_mode: debugMode,
      metadata: {}
    }

    if (debugMode) {
      debugMutation.mutate(payload)
    } else {
      executeMutation.mutate(payload)
    }
  }

  const activeMutation = debugMode ? debugMutation : executeMutation
  const result = activeMutation.data

  return (
    <div className="space-y-6">
      {/* Header section */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Sparkles className="h-8 w-8 text-teal-600 animate-pulse" />
            Multi-Agent Orchestrator
          </h1>
          <p className="text-slate-500 mt-1">
            Production LangGraph dynamic pipeline orchestrating all 9 AI healthcare agents.
          </p>
        </div>
        <div className="flex items-center gap-4">
          <OrchestratorHealthStatus />
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetchStats()}
            className="flex items-center gap-1.5"
            disabled={statsLoading}
          >
            <RefreshCw className={`h-3.5 w-3.5 ${statsLoading ? 'animate-spin' : ''}`} />
            Refresh Statistics
          </Button>
        </div>
      </div>

      {/* Telemetry Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[
          { name: 'Total Executions', val: stats?.total_executions ?? 0, desc: `Failures: ${stats?.failures ?? 0}`, icon: Activity },
          { name: 'Average Latency', val: `${(stats?.average_latency_ms ?? 0.0).toFixed(1)} ms`, desc: `Retries: ${stats?.retries ?? 0}`, icon: Clock },
          { name: 'Total Token Usage', val: (stats?.total_token_usage?.total_tokens ?? 0).toLocaleString(), desc: `Prompt: ${stats?.total_token_usage?.prompt_tokens ?? 0}`, icon: Cpu },
          { name: 'USD Total Costs', val: `$${(stats?.total_costs ?? 0.0).toFixed(4)}`, desc: `Cache Hit: ${((stats?.cache_hit_rate ?? 0.0) * 100.0).toFixed(1)}%`, icon: Zap }
        ].map((item, idx) => (
          <Card key={idx} className="border border-slate-200 shadow-sm bg-white overflow-hidden">
            <CardContent className="pt-4 flex items-center justify-between">
              <div>
                <span className="text-xs text-slate-400 block uppercase font-semibold">{item.name}</span>
                <span className="text-xl font-bold text-slate-900 mt-0.5 block">{item.val}</span>
                <span className="text-[10px] text-slate-500 block mt-0.5">{item.desc}</span>
              </div>
              <item.icon className="h-8 w-8 text-teal-600/30" />
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Column: Playground Inputs */}
        <div className="space-y-6">
          <Card className="border border-slate-200 shadow-sm bg-white">
            <CardHeader className="pb-3 border-b border-slate-100 bg-slate-50/50">
              <CardTitle className="text-sm font-bold text-slate-800 uppercase tracking-wider">Execution Variables</CardTitle>
            </CardHeader>
            <CardContent className="pt-6 space-y-6">
              <div>
                <label className="text-xs font-semibold text-slate-500 block uppercase mb-2">Patient MongoDB ID</label>
                <Input
                  value={patientId}
                  onChange={(e) => setPatientId(e.target.value)}
                  placeholder="Patient MongoDB ID"
                  className="font-mono text-sm bg-slate-50"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-500 block uppercase mb-2">Session ID (Optional)</label>
                  <Input
                    value={session_id}
                    onChange={(e) => setSessionId(e.target.value)}
                    placeholder="Auto-generated if blank"
                    className="font-mono text-sm bg-slate-50"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-500 block uppercase mb-2">Conversation ID (Optional)</label>
                  <Input
                    value={conversation_id}
                    onChange={(e) => setConversationId(e.target.value)}
                    placeholder="Auto-generated if blank"
                    className="font-mono text-sm bg-slate-50"
                  />
                </div>
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-500 block uppercase mb-2">Prompt / User Request Inquiry</label>
                <Textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  rows={4}
                  placeholder="E.g., I need a reminder to take Aspirin daily at 8 AM..."
                  className="font-sans text-sm resize-none"
                />
              </div>
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="orchestratorDebugCheck"
                  checked={debugMode}
                  onChange={(e) => setDebugMode(e.target.checked)}
                  className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                />
                <label htmlFor="orchestratorDebugCheck" className="text-sm text-slate-600 font-medium select-none cursor-pointer">
                  Enable verbose execution tracing (debug endpoint)
                </label>
              </div>
              <Button
                onClick={handleRun}
                className="w-full bg-teal-600 hover:bg-teal-700 text-white font-semibold flex items-center justify-center gap-2 shadow-sm"
                disabled={activeMutation.isPending}
              >
                {activeMutation.isPending ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Executing Graph Workflow...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 fill-current" />
                    Execute Multi-Agent Graph
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Intentionally show intent distributions & agent usages dynamically */}
          {stats && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card className="border border-slate-200 shadow-sm bg-white">
                <CardHeader className="pb-2 border-b border-slate-100 bg-slate-50/50">
                  <CardTitle className="text-xs font-bold text-slate-600 uppercase">Intent Traversal Distribution</CardTitle>
                </CardHeader>
                <CardContent className="pt-4">
                  <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
                    {Object.entries(stats.intent_distribution).length === 0 ? (
                      <span className="text-xs text-slate-400">No intents logged yet.</span>
                    ) : (
                      Object.entries(stats.intent_distribution).map(([intent, count]) => (
                        <div key={intent} className="flex justify-between items-center text-xs border-b border-slate-50 pb-1">
                          <span className="font-mono bg-slate-100 px-1.5 py-0.5 rounded text-slate-700 font-bold">{intent}</span>
                          <span className="font-bold text-slate-900">{count} runs</span>
                        </div>
                      ))
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card className="border border-slate-200 shadow-sm bg-white">
                <CardHeader className="pb-2 border-b border-slate-100 bg-slate-50/50">
                  <CardTitle className="text-xs font-bold text-slate-600 uppercase">Agents Executions Count</CardTitle>
                </CardHeader>
                <CardContent className="pt-4">
                  <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
                    {Object.entries(stats.agent_usage).length === 0 ? (
                      <span className="text-xs text-slate-400">No agent run metrics yet.</span>
                    ) : (
                      Object.entries(stats.agent_usage).map(([agent, count]) => (
                        <div key={agent} className="flex justify-between items-center text-xs border-b border-slate-50 pb-1">
                          <span className="font-sans text-slate-700 font-semibold">{agent}</span>
                          <span className="font-bold text-slate-900">{count} runs</span>
                        </div>
                      ))
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>

        {/* Right Column: Execution Output Console */}
        <div className="border border-slate-200 rounded-lg p-6 bg-slate-50/50 space-y-6 shadow-sm">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200/50 pb-2">
            Execution Console Outputs
          </h3>

          {activeMutation.isIdle && (
            <div className="flex flex-col items-center justify-center py-32 text-slate-400">
              <Terminal className="h-10 w-10 mb-2 stroke-1 text-slate-400" />
              <p className="text-sm">Submit a query to inspect dynamic routing workflows and traversal execution trace paths.</p>
            </div>
          )}

          {activeMutation.isPending && (
            <div className="flex flex-col items-center justify-center py-32 text-slate-500">
              <RefreshCw className="h-10 w-10 mb-2 animate-spin text-teal-600" />
              <p className="text-sm font-semibold">Running dynamic LangGraph state traversal...</p>
            </div>
          )}

          {activeMutation.isSuccess && result && (
            <div className="space-y-6">
              {/* Dynamic Status Banner */}
              <div className={`p-4 rounded-lg flex items-start gap-3 border ${
                result.success
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                  : 'bg-red-50 border-red-200 text-red-800'
              }`}>
                {result.success ? (
                  <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                ) : (
                  <AlertTriangle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                )}
                <div>
                  <div className="font-bold text-sm">
                    Execution: {result.success ? 'Success' : 'Failed'}
                  </div>
                  <div className="text-xs opacity-90 mt-1 flex flex-wrap gap-2">
                    <span>Intended: <strong className="font-mono bg-white/50 px-1 rounded">{result.intent}</strong></span>
                    <span>•</span>
                    <span>Dispatched: <strong className="font-mono bg-white/50 px-1 rounded">{result.agent}</strong></span>
                  </div>
                  <div className="text-sm mt-3 font-medium font-sans leading-relaxed">
                    {result.response}
                  </div>
                </div>
              </div>

              {/* Warnings check */}
              {result.warnings && result.warnings.length > 0 && (
                <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                  <h4 className="text-xs font-bold text-amber-800 uppercase flex items-center gap-1.5 mb-2">
                    <AlertTriangle className="h-4 w-4 text-amber-600" />
                    Clinical Safety Warnings
                  </h4>
                  <ul className="list-disc pl-4 space-y-1 text-xs text-amber-800 font-semibold">
                    {result.warnings.map((w, idx) => (
                      <li key={idx}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Execution Trace Timeline */}
              {result.execution_trace && result.execution_trace.length > 0 && (
                <div className="space-y-3 bg-white p-4 rounded-lg border border-slate-200">
                  <span className="text-xs font-semibold text-slate-500 block uppercase">Traversed Graph Trace Path</span>
                  <div className="flex flex-wrap items-center gap-2 pt-1">
                    {result.execution_trace.map((node, index) => (
                      <div key={index} className="flex items-center gap-2">
                        <span className={`text-[10px] font-mono font-bold px-2 py-1 rounded shadow-sm ${
                          node.includes('Agent') && node !== 'router_agent' && node !== 'retrieval_agent'
                            ? 'bg-indigo-100 text-indigo-800 border border-indigo-200'
                            : 'bg-slate-100 text-slate-600 border border-slate-200'
                        }`}>
                          {node}
                        </span>
                        {index < result.execution_trace.length - 1 && (
                          <ArrowRight className="h-3.5 w-3.5 text-slate-300 flex-shrink-0" />
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Citations references */}
              {result.citations && result.citations.length > 0 && (
                <div className="space-y-2 bg-white p-4 rounded-lg border border-slate-200">
                  <span className="text-xs font-semibold text-slate-500 block uppercase">Retrieved Citations & References</span>
                  <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
                    {result.citations.map((c, idx) => (
                      <div key={idx} className="p-2 border border-slate-100 rounded text-[11px] space-y-1 bg-slate-50/50">
                        <div className="font-bold text-slate-700">Source: {c.source} (score: {(c.score ?? 0).toFixed(2)})</div>
                        <div className="text-slate-500 italic">"{c.text}"</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Memory Sync results status if present */}
              {result.metadata?.memory_sync_result && (
                <div className="p-4 bg-teal-50/30 border border-teal-200 rounded-lg flex items-start gap-2.5">
                  <Database className="h-5 w-5 text-teal-600 flex-shrink-0 mt-0.5" />
                  <div className="text-xs text-teal-800">
                    <span className="font-bold block">Phase 9 Patient Memory Synced</span>
                    <div className="mt-1 space-y-0.5 opacity-90">
                      <div>Version: {result.metadata.memory_sync_result.summary_version}</div>
                      <div>Rebuilt MongoDB: {result.metadata.memory_sync_result.rebuilt_mongodb ? 'Yes' : 'No'}</div>
                      <div>Regenerated Qdrant: {result.metadata.memory_sync_result.regenerated_qdrant ? 'Yes' : 'No'}</div>
                      <div>Latency: {result.metadata.memory_sync_result.sync_latency_ms.toFixed(1)} ms</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Usage & JSON debug blocks */}
              <div className="space-y-2">
                <span className="text-xs font-semibold text-slate-500 block uppercase">Raw Debug Trace Contract</span>
                <pre className="bg-slate-900 text-teal-400 p-4 rounded-lg text-xs font-mono overflow-auto max-h-56">
                  {JSON.stringify(result, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function MultiAgentOrchestratorPage() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <OrchestratorDashboardContent />
    </ProtectedRoute>
  )
}
