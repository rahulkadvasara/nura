'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { adminUserService } from '@/services/admin-user.service'
import { 
  useAIHealth, 
  useAIPlaygroundTest, 
  useEmbeddingHealth, 
  useEmbeddingTest,
  useVectorHealth,
  useVectorTest,
  usePatientContext,
  useAIPlaygroundHealth,
  useAIPlaygroundChat,
  useIndexStatistics,
  useIndexDocument,
  useBatchIndexDocuments,
  useReindexDocument,
  useDeleteDocument,
  useDeletePatientDocuments,
  useRetrievalSingle,
  useRetrievalMulti,
  useRetrievalStatistics,
  useRetrievalStatisticsRaw,
  useRetrievalAgent,
  useRetrievalAgentDebug,
  useBuildContext,
  useContextAssemblyStatistics,
  useGraphHealth,
  useGraphNodes,
  useGraphStatistics,
  useGraphTestRun,
  useRouterIntents,
  useRouterClassify,
  useRouterTest,
  useRouterStatistics,
  useMedicalAgentTest,
  useSymptomAgentTest,
  useMemoryAgentTest,
  useCoreAgentsStatistics,
  useReportAgentTest,
  useDrugAgentTest,
  useDoctorAgentTest,
  useHealthcareAgentsStatistics,
  useDrugLookup,
  useDrugNormalize,
  useDrugStatistics,
  useCheckDrugInteractions,
  useDrugInteractionsStatistics,
  useValidateMedications,
  useMedicationValidationStatistics,
  useExplainDrugSafety,
  useDrugAISafetyStatistics
} from '@/hooks/use-ai'
import { HealthcareAgentsView } from './healthcare_agents_view'
import { OperationsAgentsView } from './operations_agents_view'
import { 
  Sparkles, 
  Cpu, 
  Clock, 
  Activity, 
  Terminal, 
  AlertTriangle, 
  CheckCircle2, 
  RefreshCw, 
  Zap, 
  Database,
  Copy,
  Check,
  FileText,
  Code,
  Users,
  Search,
  Sliders,
  Settings,
  Trash2,
  Layers,
  Brain
} from 'lucide-react'


function LLMHealthBadge() {
  const { 
    data: health, 
    isLoading: isHealthLoading, 
    isError: isHealthError, 
    refetch: refetchHealth 
  } = useAIHealth()

  return (
    <Card className="shadow-sm border-slate-200 bg-white px-4 py-2 flex items-center gap-3">
      <div className="flex flex-col">
        <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Groq Client Status</span>
        {isHealthLoading ? (
          <span className="text-sm font-medium text-slate-500 flex items-center gap-1.5 mt-0.5">
            <RefreshCw className="h-3 w-3 animate-spin" />
            Checking...
          </span>
        ) : isHealthError ? (
          <span className="text-sm font-medium text-red-500 flex items-center gap-1.5 mt-0.5">
            <AlertTriangle className="h-4 w-4" />
            Connection Error
          </span>
        ) : health?.reachable ? (
          <span className="text-sm font-medium text-teal-600 flex items-center gap-1.5 mt-0.5">
            <CheckCircle2 className="h-4 w-4 text-teal-500" />
            Healthy & Reachable
          </span>
        ) : (
          <span className="text-sm font-medium text-amber-500 flex items-center gap-1.5 mt-0.5">
            <AlertTriangle className="h-4 w-4" />
            Unreachable
          </span>
        )}
      </div>
      <Button 
        variant="ghost" 
        size="icon" 
        onClick={() => refetchHealth()} 
        disabled={isHealthLoading}
        className="h-8 w-8 text-slate-400 hover:text-slate-600"
      >
        <RefreshCw className={`h-4 w-4 ${isHealthLoading ? 'animate-spin' : ''}`} />
      </Button>
    </Card>
  )
}

function EmbeddingHealthBadge() {
  const { 
    data: health, 
    isLoading: isHealthLoading, 
    isError: isHealthError, 
    refetch: refetchHealth 
  } = useEmbeddingHealth()

  return (
    <Card className="shadow-sm border-slate-200 bg-white px-4 py-2 flex items-center gap-3">
      <div className="flex flex-col">
        <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Embedding Status</span>
        {isHealthLoading ? (
          <span className="text-sm font-medium text-slate-500 flex items-center gap-1.5 mt-0.5">
            <RefreshCw className="h-3 w-3 animate-spin" />
            Checking...
          </span>
        ) : isHealthError ? (
          <span className="text-sm font-medium text-red-500 flex items-center gap-1.5 mt-0.5">
            <AlertTriangle className="h-4 w-4" />
            Connection Error
          </span>
        ) : health?.status === 'healthy' ? (
          <span className="text-sm font-medium text-teal-600 flex items-center gap-1.5 mt-0.5">
            <CheckCircle2 className="h-4 w-4 text-teal-500" />
            Healthy
          </span>
        ) : (
          <span className="text-sm font-medium text-amber-500 flex items-center gap-1.5 mt-0.5">
            <AlertTriangle className="h-4 w-4" />
            Unhealthy
          </span>
        )}
      </div>
      <Button 
        variant="ghost" 
        size="icon" 
        onClick={() => refetchHealth()} 
        disabled={isHealthLoading}
        className="h-8 w-8 text-slate-400 hover:text-slate-600"
      >
        <RefreshCw className={`h-4 w-4 ${isHealthLoading ? 'animate-spin' : ''}`} />
      </Button>
    </Card>
  )
}

function AIConnectionInfoCard() {
  const { data: health } = useAIHealth()
  return (
    <Card className="border-slate-200 shadow-sm bg-white">
      <CardHeader className="pb-3 border-b border-slate-100">
        <CardTitle className="text-sm font-semibold text-slate-700">Infrastructure Metadata</CardTitle>
      </CardHeader>
      <CardContent className="pt-4 space-y-3 text-xs">
        <div className="flex justify-between items-center text-slate-600">
          <span>Configured Model:</span>
          <span className="font-medium text-slate-800">{health?.model || 'llama-3.3-70b-versatile'}</span>
        </div>
        <div className="flex justify-between items-center text-slate-600">
          <span>Connection Target:</span>
          <span className="font-medium text-slate-800">api.groq.com</span>
        </div>
        <div className="flex justify-between items-center text-slate-600">
          <span>Health Latency:</span>
          <span className="font-medium text-slate-800">
            {health?.latency_ms ? `${health.latency_ms.toFixed(1)} ms` : 'N/A'}
          </span>
        </div>
        {health?.timestamp && (
          <div className="flex flex-col gap-1 pt-2 border-t border-slate-100 text-slate-400">
            <span>Last Checked:</span>
            <span>{new Date(health.timestamp).toLocaleString()}</span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function EmbeddingConnectionInfoCard() {
  const { data: health } = useEmbeddingHealth()
  return (
    <Card className="border-slate-200 shadow-sm bg-white">
      <CardHeader className="pb-3 border-b border-slate-100">
        <CardTitle className="text-sm font-semibold text-slate-700">Embedding Engine Settings</CardTitle>
      </CardHeader>
      <CardContent className="pt-4 space-y-3 text-xs">
        <div className="flex justify-between items-center text-slate-600">
          <span>Provider:</span>
          <span className="font-medium text-slate-800 uppercase">{health?.provider || 'local'}</span>
        </div>
        <div className="flex justify-between items-center text-slate-600">
          <span>Embedding Model:</span>
          <span className="font-medium text-slate-800 text-right truncate max-w-[150px]" title={health?.model}>{health?.model || 'all-MiniLM-L6-v2'}</span>
        </div>
        <div className="flex justify-between items-center text-slate-600">
          <span>Target Dimension:</span>
          <span className="font-medium text-slate-800">{health?.dimensions || 384}</span>
        </div>
        <div className="flex justify-between items-center text-slate-600">
          <span>Engine Latency:</span>
          <span className="font-medium text-slate-800">
            {health?.latency ? `${health.latency.toFixed(1)} ms` : 'N/A'}
          </span>
        </div>
      </CardContent>
    </Card>
  )
}

function LLMPlaygroundView() {
  const [prompt, setPrompt] = useState('')
  const [testResult, setTestResult] = useState<any>(null)
  const testMutation = useAIPlaygroundTest()

  const handleRunTest = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!prompt.trim()) return

    try {
      const result = await testMutation.mutateAsync(prompt)
      setTestResult(result)
    } catch (err) {
      setTestResult(null)
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in duration-300">
      {/* Playground Input Column (col-span-2) */}
      <div className="lg:col-span-2 space-y-6">
        <Card className="border-slate-200 shadow-md bg-white">
          <CardHeader className="border-b border-slate-100 bg-slate-50/50">
            <CardTitle className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <Terminal className="h-5 w-5 text-slate-500" />
              Prompt Execution Console
            </CardTitle>
            <CardDescription>
              Submit direct requests to confirm model response pipelines without database contextual overlays.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <form onSubmit={handleRunTest} className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="prompt" className="text-sm font-medium text-slate-700">
                  System Prompt Input
                </label>
                <Textarea
                  id="prompt"
                  placeholder="Enter a verification prompt (e.g. Write a 3-word sentence explaining medicine)..."
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  rows={5}
                  disabled={testMutation.isPending}
                  className="border-slate-200 focus:border-teal-500 focus:ring-teal-500 resize-none font-sans"
                />
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-xs text-slate-400">
                  * Playground runs direct LLM inference with no conversation memory.
                </span>
                <Button
                  type="submit"
                  disabled={!prompt.trim() || testMutation.isPending}
                  className="bg-teal-600 hover:bg-teal-700 text-white font-semibold transition-all px-6"
                >
                  {testMutation.isPending ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Executing Inference...
                    </>
                  ) : (
                    <>
                      <Zap className="h-4 w-4 mr-2" />
                      Run Test
                    </>
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Response Panel */}
        {(testResult || testMutation.isPending || testMutation.isError) && (
          <Card className="border-slate-200 shadow-md bg-white overflow-hidden">
            <CardHeader className="border-b border-slate-100 bg-slate-50/50">
              <CardTitle className="text-lg font-semibold text-slate-800">
                Model Output Stream Response
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              {testMutation.isPending ? (
                <div className="flex flex-col items-center justify-center py-12 text-slate-400 gap-3">
                  <RefreshCw className="h-8 w-8 animate-spin text-teal-500" />
                  <p className="text-sm font-medium animate-pulse text-slate-500">Waiting for Groq host responses...</p>
                </div>
              ) : testMutation.isError ? (
                <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 flex items-start gap-3">
                  <AlertTriangle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold">Inference Execution Failed</h4>
                    <p className="text-sm mt-1 text-red-600">
                      {testMutation.error?.message || 'An unexpected error occurred during client generation.'}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-5 font-mono text-sm text-slate-800 whitespace-pre-wrap leading-relaxed shadow-inner">
                  {testResult?.response}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Telemetry and System Info Column */}
      <div className="space-y-6">
        {/* Active Model Telemetry Cards */}
        {testResult && (
          <>
            {/* Latency card */}
            <Card className="border-slate-200 shadow bg-gradient-to-br from-teal-50 to-white hover:shadow-md transition-all">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Response Latency</p>
                    <h3 className="text-3xl font-extrabold text-teal-900 mt-1">
                      {testResult.latency.toFixed(0)} <span className="text-lg font-semibold text-teal-600">ms</span>
                    </h3>
                  </div>
                  <div className="p-3 rounded-full bg-teal-100 text-teal-700">
                    <Clock className="h-6 w-6" />
                  </div>
                </div>
                <div className="mt-3 text-xs text-slate-400 flex items-center gap-1">
                  <Activity className="h-3 w-3 text-teal-500" />
                  Measured roundtrip response generation latency
                </div>
              </CardContent>
            </Card>

            {/* Token Usage card */}
            <Card className="border-slate-200 shadow bg-gradient-to-br from-blue-50 to-white hover:shadow-md transition-all">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Token Allocation</p>
                    <h3 className="text-3xl font-extrabold text-blue-900 mt-1">
                      {testResult.token_usage.total_tokens} <span className="text-lg font-semibold text-blue-600">tkn</span>
                    </h3>
                  </div>
                  <div className="p-3 rounded-full bg-blue-100 text-blue-700">
                    <Database className="h-6 w-6" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-blue-100/50 text-xs text-slate-500">
                  <div>
                    <span className="block text-slate-400 font-medium">Prompt</span>
                    <span className="font-semibold text-blue-900">{testResult.token_usage.prompt_tokens}</span>
                  </div>
                  <div>
                    <span className="block text-slate-400 font-medium">Completion</span>
                    <span className="font-semibold text-blue-900">{testResult.token_usage.completion_tokens}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Model Card */}
            <Card className="border-slate-200 shadow bg-gradient-to-br from-indigo-50 to-white hover:shadow-md transition-all">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active LLM Provider</p>
                    <h3 className="text-lg font-bold text-indigo-900 mt-1 truncate max-w-[200px]" title={testResult.model}>
                      {testResult.model}
                    </h3>
                  </div>
                  <div className="p-3 rounded-full bg-indigo-100 text-indigo-700">
                    <Cpu className="h-6 w-6" />
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t border-indigo-100/50 text-xs text-slate-500 flex justify-between">
                  <span>Finish Reason:</span>
                  <span className="font-mono bg-indigo-50 px-1.5 py-0.5 rounded text-indigo-700 font-semibold">
                    {testResult.finish_reason}
                  </span>
                </div>
              </CardContent>
            </Card>
          </>
        )}

        {/* AI Connection Info */}
        <AIConnectionInfoCard />
      </div>
    </div>
  )
}

function EmbeddingsPlaygroundView() {
  const [text, setText] = useState('')
  const [testResult, setTestResult] = useState<any>(null)
  const [copiedVector, setCopiedVector] = useState(false)
  const [copiedMetadata, setCopiedMetadata] = useState(false)
  const testMutation = useEmbeddingTest()

  const handleRunTest = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!text.trim()) return

    try {
      const result = await testMutation.mutateAsync(text)
      setTestResult(result)
    } catch (err) {
      setTestResult(null)
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in duration-300">
      {/* Playground Input Column (col-span-2) */}
      <div className="lg:col-span-2 space-y-6">
        <Card className="border-slate-200 shadow-md bg-white">
          <CardHeader className="border-b border-slate-100 bg-slate-50/50">
            <CardTitle className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <Code className="h-5 w-5 text-slate-500" />
              Embedding Input Console
            </CardTitle>
            <CardDescription>
              Submit custom text payloads to generate mathematical vector representation profiles.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <form onSubmit={handleRunTest} className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="embedding-text" className="text-sm font-medium text-slate-700">
                  Verification Block Input
                </label>
                <Textarea
                  id="embedding-text"
                  placeholder="Enter content to convert into vector embedding (e.g. Patient presents with mild hypertension and elevated systolic pressure)..."
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  rows={5}
                  disabled={testMutation.isPending}
                  className="border-slate-200 focus:border-teal-500 focus:ring-teal-500 resize-none font-sans"
                />
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-xs text-slate-400">
                  * Converts input string directly to vector coordinates utilizing the active platform embedder.
                </span>
                <Button
                  type="submit"
                  disabled={!text.trim() || testMutation.isPending}
                  className="bg-teal-600 hover:bg-teal-700 text-white font-semibold transition-all px-6"
                >
                  {testMutation.isPending ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Vectorizing Input...
                    </>
                  ) : (
                    <>
                      <Zap className="h-4 w-4 mr-2" />
                      Generate Embedding
                    </>
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Loading and Error states inside response area */}
        {testMutation.isPending && (
          <Card className="border-slate-200 shadow-md bg-white">
            <CardContent className="pt-6">
              <div className="flex flex-col items-center justify-center py-12 text-slate-400 gap-3">
                <RefreshCw className="h-8 w-8 animate-spin text-teal-500" />
                <p className="text-sm font-medium animate-pulse text-slate-500">Generating L2 normalized vector coordinates...</p>
              </div>
            </CardContent>
          </Card>
        )}

        {testMutation.isError && (
          <Card className="border-slate-200 shadow-md bg-white">
            <CardContent className="pt-6">
              <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="font-semibold">Embedding Generation Failed</h4>
                  <p className="text-sm mt-1 text-red-600">
                    {testMutation.error?.message || 'An unexpected error occurred during client generation.'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Response Panel */}
        {testResult && !testMutation.isPending && (
          <div className="space-y-6">
            {/* Vector Array Preview */}
            <Card className="border-slate-200 shadow-md bg-white overflow-hidden">
              <CardHeader className="border-b border-slate-100 bg-slate-50/50 flex flex-row items-center justify-between py-4">
                <div>
                  <CardTitle className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                    <Database className="h-5 w-5 text-teal-600" />
                    Vector Signature Preview
                  </CardTitle>
                  <CardDescription>
                    Abridged list showing the first 5 elements of the high-dimensional embedding vector.
                  </CardDescription>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    navigator.clipboard.writeText(JSON.stringify(testResult.vector_preview))
                    setCopiedVector(true)
                    setTimeout(() => setCopiedVector(false), 2000)
                  }}
                  className="h-8 gap-1.5"
                >
                  {copiedVector ? (
                    <>
                      <Check className="h-3.5 w-3.5 text-teal-600" />
                      Copied
                    </>
                  ) : (
                    <>
                      <Copy className="h-3.5 w-3.5" />
                      Copy
                    </>
                  )}
                </Button>
              </CardHeader>
              <CardContent className="pt-6">
                <div className="rounded-lg border border-slate-200 bg-slate-900 p-5 font-mono text-sm text-slate-100 shadow-inner overflow-x-auto">
                  <div className="text-teal-400">Preview of first {testResult.vector_preview.length} dimensions:</div>
                  <div className="mt-2">
                    [
                    <div className="pl-6 space-y-1">
                      {testResult.vector_preview.map((val: number, idx: number) => (
                        <div key={idx}>
                          <span className="text-slate-500">{idx}:</span>{' '}
                          <span className="text-amber-300">{val.toFixed(8)}</span>
                          {idx < testResult.vector_preview.length - 1 ? ',' : ''}
                        </div>
                      ))}
                      <div className="text-slate-500">... (truncated {testResult.dimensions - testResult.vector_preview.length} elements)</div>
                    </div>
                    ]
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Metadata Audit Payload */}
            <Card className="border-slate-200 shadow-md bg-white overflow-hidden">
              <CardHeader className="border-b border-slate-100 bg-slate-50/50 flex flex-row items-center justify-between py-4">
                <div>
                  <CardTitle className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                    <FileText className="h-5 w-5 text-slate-500" />
                    Metadata Audit Payload
                  </CardTitle>
                  <CardDescription>
                    Index headers and SHA-256 fingerprint validation generated along with the text embedding.
                  </CardDescription>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    navigator.clipboard.writeText(JSON.stringify(testResult.metadata, null, 2))
                    setCopiedMetadata(true)
                    setTimeout(() => setCopiedMetadata(false), 2000)
                  }}
                  className="h-8 gap-1.5"
                >
                  {copiedMetadata ? (
                    <>
                      <Check className="h-3.5 w-3.5 text-teal-600" />
                      Copied
                    </>
                  ) : (
                    <>
                      <Copy className="h-3.5 w-3.5" />
                      Copy
                    </>
                  )}
                </Button>
              </CardHeader>
              <CardContent className="pt-6">
                <pre className="rounded-lg border border-slate-200 bg-slate-50 p-5 font-mono text-xs text-slate-800 shadow-inner overflow-x-auto">
                  {JSON.stringify(testResult.metadata, null, 2)}
                </pre>
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      {/* Telemetry and System Info Column */}
      <div className="space-y-6">
        {/* Active Model Telemetry Cards */}
        {testResult && (
          <>
            {/* Latency card */}
            <Card className="border-slate-200 shadow bg-gradient-to-br from-teal-50 to-white hover:shadow-md transition-all">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Vector Generation Latency</p>
                    <h3 className="text-3xl font-extrabold text-teal-900 mt-1">
                      {testResult.latency.toFixed(1)} <span className="text-lg font-semibold text-teal-600">ms</span>
                    </h3>
                  </div>
                  <div className="p-3 rounded-full bg-teal-100 text-teal-700">
                    <Clock className="h-6 w-6" />
                  </div>
                </div>
                <div className="mt-3 text-xs text-slate-400 flex items-center gap-1">
                  <Activity className="h-3 w-3 text-teal-500" />
                  Measured roundtrip embedding inference latency
                </div>
              </CardContent>
            </Card>

            {/* Vector Resolution card */}
            <Card className="border-slate-200 shadow bg-gradient-to-br from-blue-50 to-white hover:shadow-md transition-all">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Vector Resolution</p>
                    <h3 className="text-3xl font-extrabold text-blue-900 mt-1">
                      {testResult.dimensions} <span className="text-lg font-semibold text-blue-600">dim</span>
                    </h3>
                  </div>
                  <div className="p-3 rounded-full bg-blue-100 text-blue-700">
                    <Database className="h-6 w-6" />
                  </div>
                </div>
                <div className="mt-3 text-xs text-slate-400 flex items-center gap-1">
                  <Activity className="h-3 w-3 text-blue-500" />
                  Embedding model vector dimensional configuration
                </div>
              </CardContent>
            </Card>

            {/* Vector Math Validation Card */}
            <Card className="border-slate-200 shadow-sm bg-white">
              <CardHeader className="pb-3 border-b border-slate-100">
                <CardTitle className="text-sm font-semibold text-slate-700">Vector Math Validation</CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-3 text-xs">
                <div className="flex justify-between items-center text-slate-600">
                  <span>Normalization Scheme:</span>
                  <span className="font-mono bg-teal-50 px-1.5 py-0.5 rounded text-teal-700 font-semibold">L2 Normalized</span>
                </div>
                <div className="flex justify-between items-center text-slate-600">
                  <span>Vector Unit Norm:</span>
                  <span className="font-semibold text-teal-600">1.00000000</span>
                </div>
                <div className="flex justify-between items-center text-slate-600">
                  <span>Fingerprint Type:</span>
                  <span className="font-medium text-slate-800">SHA-256</span>
                </div>
              </CardContent>
            </Card>
          </>
        )}

        {/* Embedding Connection Info */}
        <EmbeddingConnectionInfoCard />
      </div>
    </div>
  )
}

function VectorHealthBadge() {
  const { 
    data: health, 
    isLoading: isHealthLoading, 
    isError: isHealthError, 
    refetch: refetchHealth 
  } = useVectorHealth()

  return (
    <Card className="shadow-sm border-slate-200 bg-white px-4 py-2 flex items-center gap-3">
      <div className="flex flex-col">
        <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Vector DB Status</span>
        {isHealthLoading ? (
          <span className="text-sm font-medium text-slate-500 flex items-center gap-1.5 mt-0.5">
            <RefreshCw className="h-3 w-3 animate-spin" />
            Checking...
          </span>
        ) : isHealthError ? (
          <span className="text-sm font-medium text-red-500 flex items-center gap-1.5 mt-0.5">
            <AlertTriangle className="h-4 w-4" />
            Connection Error
          </span>
        ) : health?.connected ? (
          <span className="text-sm font-medium text-teal-600 flex items-center gap-1.5 mt-0.5">
            <CheckCircle2 className="h-4 w-4 text-teal-500" />
            Connected
          </span>
        ) : (
          <span className="text-sm font-medium text-amber-500 flex items-center gap-1.5 mt-0.5">
            <AlertTriangle className="h-4 w-4" />
            Disconnected
          </span>
        )}
      </div>
      <Button 
        variant="ghost" 
        size="icon" 
        onClick={() => refetchHealth()} 
        disabled={isHealthLoading}
        className="h-8 w-8 text-slate-400 hover:text-slate-600"
      >
        <RefreshCw className={`h-4 w-4 ${isHealthLoading ? 'animate-spin' : ''}`} />
      </Button>
    </Card>
  )
}

function VectorPlaygroundView() {
  const [text, setText] = useState('')
  const [collection, setCollection] = useState('patient_reports')
  const [testResult, setTestResult] = useState<any>(null)
  
  const { data: health, isLoading: isHealthLoading, refetch: refetchHealth } = useVectorHealth()
  const testMutation = useVectorTest()

  const handleRunTest = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!text.trim() || !collection) return

    try {
      const result = await testMutation.mutateAsync({ collection, text })
      setTestResult(result)
    } catch (err) {
      setTestResult(null)
    }
  }

  const collectionsList = health?.collections || [
    { name: 'patient_reports', status: 'unknown', vector_count: 0, dimensions: 384, distance: 'COSINE' },
    { name: 'chat_memory', status: 'unknown', vector_count: 0, dimensions: 384, distance: 'COSINE' },
    { name: 'medical_knowledge', status: 'unknown', vector_count: 0, dimensions: 384, distance: 'COSINE' },
    { name: 'drug_knowledge', status: 'unknown', vector_count: 0, dimensions: 384, distance: 'COSINE' },
    { name: 'doctor_knowledge', status: 'unknown', vector_count: 0, dimensions: 384, distance: 'COSINE' },
  ]

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in duration-300">
      {/* Test Execution Console and Results (col-span-2) */}
      <div className="lg:col-span-2 space-y-6">
        <Card className="border-slate-200 shadow-md bg-white">
          <CardHeader className="border-b border-slate-100 bg-slate-50/50">
            <CardTitle className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <Terminal className="h-5 w-5 text-slate-500" />
              Semantic Search Verification Console
            </CardTitle>
            <CardDescription>
              Submit test text queries to generate a temporary embedding, run near-neighbor lookup, and measure semantic search latency.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <form onSubmit={handleRunTest} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label htmlFor="collection-select" className="text-sm font-medium text-slate-700">
                    Target Collection
                  </label>
                  <select
                    id="collection-select"
                    value={collection}
                    onChange={(e) => setCollection(e.target.value)}
                    disabled={testMutation.isPending}
                    className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-sm focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
                  >
                    <option value="patient_reports">Patient Reports (patient_reports)</option>
                    <option value="chat_memory">Chat Memory (chat_memory)</option>
                    <option value="medical_knowledge">Medical Knowledge (medical_knowledge)</option>
                    <option value="drug_knowledge">Drug Knowledge (drug_knowledge)</option>
                    <option value="doctor_knowledge">Doctor Knowledge (doctor_knowledge)</option>
                  </select>
                </div>
              </div>

              <div className="space-y-2">
                <label htmlFor="vector-text" className="text-sm font-medium text-slate-700">
                  Search Query Text
                </label>
                <Textarea
                  id="vector-text"
                  placeholder="Enter validation text to query the vector database (e.g. chronic hypertension symptoms)..."
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  rows={4}
                  disabled={testMutation.isPending}
                  className="border-slate-200 focus:border-teal-500 focus:ring-teal-500 resize-none font-sans"
                />
              </div>

              <div className="flex justify-between items-center">
                <span className="text-xs text-slate-400">
                  * Triggers temporary upsert, nearest-neighbor query, and clean-up.
                </span>
                <Button
                  type="submit"
                  disabled={!text.trim() || testMutation.isPending}
                  className="bg-teal-600 hover:bg-teal-700 text-white font-semibold transition-all px-6"
                >
                  {testMutation.isPending ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Executing Pipeline...
                    </>
                  ) : (
                    <>
                      <Zap className="h-4 w-4 mr-2" />
                      Verify Pipeline
                    </>
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Loading and Error states */}
        {testMutation.isPending && (
          <Card className="border-slate-200 shadow-md bg-white">
            <CardContent className="pt-6">
              <div className="flex flex-col items-center justify-center py-12 text-slate-400 gap-3">
                <RefreshCw className="h-8 w-8 animate-spin text-teal-500" />
                <p className="text-sm font-medium animate-pulse text-slate-500">Executing semantic search roundtrip...</p>
              </div>
            </CardContent>
          </Card>
        )}

        {testMutation.isError && (
          <Card className="border-slate-200 shadow-md bg-white">
            <CardContent className="pt-6">
              <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="font-semibold">Verification Pipeline Failed</h4>
                  <p className="text-sm mt-1 text-red-600">
                    {testMutation.error?.message || 'An unexpected error occurred during the verification pipeline.'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Response Results Panel */}
        {testResult && !testMutation.isPending && (
          <div className="space-y-6">
            <Card className="border-slate-200 shadow-md bg-white overflow-hidden">
              <CardHeader className="border-b border-slate-100 bg-slate-50/50 py-4">
                <CardTitle className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                  <Database className="h-5 w-5 text-teal-600" />
                  Semantic Match Results ({testResult.search_results.length})
                </CardTitle>
                <CardDescription>
                  List of nearest neighbor points matching the generated query vector.
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-6 space-y-4">
                {testResult.search_results.length === 0 ? (
                  <p className="text-sm text-slate-500 py-6 text-center">No points found in collection (excluding clean-up temporary test point).</p>
                ) : (
                  testResult.search_results.map((hit: any, index: number) => (
                    <div key={hit.id || index} className="rounded-lg border border-slate-100 bg-slate-50/50 p-4 space-y-3 hover:border-slate-200 transition-colors">
                      <div className="flex justify-between items-start gap-2">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-slate-200 text-slate-700">Point {index + 1}</span>
                          <span className="text-xs font-mono text-slate-400 truncate max-w-[150px] md:max-w-xs" title={hit.id}>{hit.id}</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <span className="text-xs text-slate-400 font-medium">Similarity Score:</span>
                          <span className="text-xs font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded-full border border-teal-100">
                            {hit.score.toFixed(4)}
                          </span>
                        </div>
                      </div>
                      <pre className="rounded border border-slate-100 bg-white p-3 font-mono text-xs text-slate-800 overflow-x-auto font-sans">
                        {JSON.stringify(hit.payload, null, 2)}
                      </pre>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      {/* Collection Stats Cards Column (col-span-1) */}
      <div className="space-y-6">
        {/* Latency card */}
        {testResult && (
          <Card className="border-slate-200 shadow bg-gradient-to-br from-teal-50 to-white hover:shadow-md transition-all">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Verification Latency</p>
                  <h3 className="text-3xl font-extrabold text-teal-900 mt-1">
                    {testResult.latency.toFixed(1)} <span className="text-lg font-semibold text-teal-600">ms</span>
                  </h3>
                </div>
                <div className="p-3 rounded-full bg-teal-100 text-teal-700">
                  <Clock className="h-6 w-6" />
                </div>
              </div>
              <div className="mt-3 text-xs text-slate-400 flex items-center gap-1">
                <Activity className="h-3 w-3 text-teal-500" />
                Measured roundtrip embedding-to-qdrant search latency
              </div>
            </CardContent>
          </Card>
        )}

        <Card className="border-slate-200 shadow bg-gradient-to-br from-blue-50 to-white hover:shadow-md transition-all">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Vector DB Latency</p>
                <h3 className="text-3xl font-extrabold text-blue-900 mt-1">
                  {health?.latency ? `${health.latency.toFixed(1)}` : 'N/A'} <span className="text-lg font-semibold text-blue-600">ms</span>
                </h3>
              </div>
              <div className="p-3 rounded-full bg-blue-100 text-blue-700">
                <Clock className="h-6 w-6" />
              </div>
            </div>
            <div className="mt-3 text-xs text-slate-400 flex items-center gap-1">
              <Activity className="h-3 w-3 text-blue-500" />
              Ping latency to Qdrant server
            </div>
          </CardContent>
        </Card>

        {/* Collections Overview */}
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wider">Registered Collections</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => refetchHealth()}
              disabled={isHealthLoading}
              className="text-slate-500 hover:text-slate-700 text-xs gap-1"
            >
              <RefreshCw className={`h-3 w-3 ${isHealthLoading ? 'animate-spin' : ''}`} />
              Refresh Stats
            </Button>
          </div>

          {collectionsList.map((col: any) => (
            <Card key={col.name} className="border-slate-200 shadow-sm bg-white overflow-hidden">
              <div className="border-b border-slate-100 bg-slate-50/50 px-4 py-2 flex justify-between items-center">
                <span className="text-xs font-bold text-slate-700 font-mono">{col.name}</span>
                <span className={`text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded-full ${
                  col.status === 'green' || col.status === 'healthy'
                    ? 'bg-teal-50 text-teal-700 border border-teal-100'
                    : col.status === 'yellow'
                    ? 'bg-amber-50 text-amber-700 border border-amber-100'
                    : 'bg-red-50 text-red-700 border border-red-100'
                }`}>
                  {col.status}
                </span>
              </div>
              <CardContent className="p-4 space-y-2 text-xs">
                <div className="flex justify-between items-center text-slate-600">
                  <span>Points Count:</span>
                  <span className="font-semibold text-slate-800">{col.vector_count}</span>
                </div>
                <div className="flex justify-between items-center text-slate-600">
                  <span>Dimensions:</span>
                  <span className="font-medium text-slate-800">{col.dimensions}</span>
                </div>
                <div className="flex justify-between items-center text-slate-600">
                  <span>Distance Metric:</span>
                  <span className="font-mono text-slate-800">{col.distance}</span>
                </div>
                {col.storage_bytes !== undefined && col.storage_bytes > 0 && (
                  <div className="flex justify-between items-center text-slate-600">
                    <span>Storage Size:</span>
                    <span className="font-medium text-slate-800">{(col.storage_bytes / 1024).toFixed(1)} KB</span>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}

function PatientContextHealthBadge() {
  return (
    <Card className="shadow-sm border-slate-200 bg-white px-4 py-2 flex items-center gap-3">
      <div className="flex flex-col">
        <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Context Builder</span>
        <span className="text-sm font-medium text-teal-600 flex items-center gap-1.5 mt-0.5">
          <CheckCircle2 className="h-4 w-4 text-teal-500" />
          Deterministic Engine Ready
        </span>
      </div>
    </Card>
  )
}

function PatientContextPlaygroundView() {
  const [search, setSearch] = useState('')
  const [selectedPatientId, setSelectedPatientId] = useState('')
  const [selectedPatientName, setSelectedPatientName] = useState('')
  const [testResult, setTestResult] = useState<any>(null)
  const [latency, setLatency] = useState<number | null>(null)
  const [copied, setCopied] = useState(false)
  const [activeSubTab, setActiveSubTab] = useState<'raw' | 'parsed'>('parsed')

  // Fetch patients list
  const { data: patientsResponse, isLoading: isLoadingPatients, isError: isPatientsError } = useQuery({
    queryKey: ['admin', 'patients-list'],
    queryFn: () => adminUserService.listUsers(undefined, 'patient')
  })
  const patients = patientsResponse?.data || []

  // Filter patients list based on search term
  const filteredPatients = patients.filter((p: any) =>
    p.full_name?.toLowerCase().includes(search.toLowerCase()) ||
    p.email?.toLowerCase().includes(search.toLowerCase())
  )

  const buildMutation = usePatientContext()

  const handleBuild = async () => {
    if (!selectedPatientId) return
    const startTime = performance.now()
    try {
      const result = await buildMutation.mutateAsync(selectedPatientId)
      const endTime = performance.now()
      setLatency(endTime - startTime)
      setTestResult(result)
    } catch (err) {
      setTestResult(null)
      setLatency(null)
    }
  }

  const handleCopy = () => {
    if (!testResult) return
    navigator.clipboard.writeText(JSON.stringify(testResult, null, 2))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in duration-300">
      {/* Left Column - Patient Selection (col-span-1) */}
      <div className="space-y-6">
        <Card className="border-slate-200 shadow-md bg-white">
          <CardHeader className="border-b border-slate-100 bg-slate-50/50">
            <CardTitle className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <Users className="h-5 w-5 text-slate-500" />
              Patient Selector
            </CardTitle>
            <CardDescription>
              Search and select an active patient to compile their unified medical history profile.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-6 space-y-4">
            <div className="relative">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search patient name/email..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full rounded-md border border-slate-200 pl-9 pr-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
              />
            </div>

            {isLoadingPatients ? (
              <div className="flex items-center justify-center py-12 text-slate-400 gap-2">
                <RefreshCw className="h-4 w-4 animate-spin text-teal-500" />
                <span className="text-sm">Loading patients list...</span>
              </div>
            ) : isPatientsError ? (
              <div className="text-center py-6 text-red-500 text-sm">
                Failed to fetch patients list.
              </div>
            ) : filteredPatients.length === 0 ? (
              <div className="text-center py-6 text-slate-500 text-sm">
                No patients match the search filter.
              </div>
            ) : (
              <div className="max-h-60 overflow-y-auto border border-slate-100 rounded-md divide-y divide-slate-100">
                {filteredPatients.map((patient: any) => (
                  <button
                    key={patient.id}
                    onClick={() => {
                      setSelectedPatientId(patient.id)
                      setSelectedPatientName(patient.full_name)
                    }}
                    className={`w-full text-left px-3 py-2.5 transition-colors flex items-center gap-3 ${
                      selectedPatientId === patient.id
                        ? 'bg-teal-50 hover:bg-teal-100'
                        : 'hover:bg-slate-50'
                    }`}
                  >
                    <div className={`h-8 w-8 rounded-full flex items-center justify-center font-bold text-xs uppercase ${
                      selectedPatientId === patient.id
                        ? 'bg-teal-600 text-white'
                        : 'bg-slate-100 text-slate-700'
                    }`}>
                      {patient.full_name?.charAt(0) || 'P'}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-semibold text-slate-800 truncate">
                        {patient.full_name}
                      </div>
                      <div className="text-xs text-slate-400 truncate">
                        {patient.email}
                      </div>
                    </div>
                    {selectedPatientId === patient.id && (
                      <CheckCircle2 className="h-4 w-4 text-teal-600 flex-shrink-0" />
                    )}
                  </button>
                ))}
              </div>
            )}

            <Button
              onClick={handleBuild}
              disabled={!selectedPatientId || buildMutation.isPending}
              className="w-full bg-teal-600 hover:bg-teal-700 text-white font-semibold transition-all"
            >
              {buildMutation.isPending ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Compiling Context...
                </>
              ) : (
                <>
                  <Zap className="h-4 w-4 mr-2" />
                  Assemble Context
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Telemetry metadata panels */}
        {testResult && (
          <Card className="border-slate-200 shadow-sm bg-white">
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-sm font-semibold text-slate-700">Sources & Provenance</CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-3 text-xs">
              <div className="flex flex-col gap-1.5">
                <span className="text-slate-400 font-medium">MongoDB Collections Queried:</span>
                <div className="flex flex-wrap gap-1.5">
                  {testResult.metadata.sources_used.map((src: string) => (
                    <span key={src} className="font-mono bg-slate-100 border border-slate-200 px-2 py-0.5 rounded text-slate-700">
                      {src}
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex justify-between items-center text-slate-600 pt-2 border-t border-slate-100">
                <span>Context Version:</span>
                <span className="font-semibold text-slate-800">{testResult.metadata.context_version}</span>
              </div>
              <div className="flex justify-between items-center text-slate-600">
                <span>Compiled At:</span>
                <span className="text-slate-500">{new Date(testResult.metadata.generated_at).toLocaleString()}</span>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Right Column - Results Console (col-span-2) */}
      <div className="lg:col-span-2 space-y-6">
        {/* Loading State */}
        {buildMutation.isPending && (
          <Card className="border-slate-200 shadow-md bg-white">
            <CardContent className="py-12 flex flex-col items-center justify-center text-slate-400 gap-3">
              <RefreshCw className="h-8 w-8 animate-spin text-teal-500" />
              <p className="text-sm font-medium animate-pulse text-slate-500">Querying database collections...</p>
              <p className="text-xs text-slate-400 max-w-sm text-center">
                Fetching patient records and compiling structured output. Running token-budget compression if necessary.
              </p>
            </CardContent>
          </Card>
        )}

        {/* Error State */}
        {buildMutation.isError && (
          <Card className="border-slate-200 shadow-md bg-white">
            <CardContent className="pt-6">
              <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="font-semibold">Context Assembly Failed</h4>
                  <p className="text-sm mt-1 text-red-600">
                    {buildMutation.error?.message || 'An unexpected error occurred during database compilation.'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Ready / Unselected State */}
        {!testResult && !buildMutation.isPending && !buildMutation.isError && (
          <Card className="border-slate-200 border-dashed border-2 bg-slate-50/50 p-12 text-center">
            <div className="mx-auto h-12 w-12 text-slate-400 flex items-center justify-center bg-white rounded-full border border-slate-200 shadow-sm mb-4">
              <Users className="h-6 w-6" />
            </div>
            <h3 className="text-sm font-bold text-slate-700">No Patient Selected</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto mt-2">
              Select a patient from the list on the left and click &apos;Assemble Context&apos; to fetch, build, and audit their deterministic structured AI context profile.
            </p>
          </Card>
        )}

        {/* Success State */}
        {testResult && !buildMutation.isPending && (
          <div className="space-y-6 animate-in fade-in duration-300">
            {/* Telemetry Stats Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* Token Count */}
              <Card className="border-slate-200 shadow bg-gradient-to-br from-teal-50 to-white">
                <CardContent className="p-4 flex items-center justify-between">
                  <div>
                    <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Estimated Context Size</p>
                    <h3 className="text-2xl font-extrabold text-teal-900 mt-1">
                      {testResult.metadata.estimated_tokens} <span className="text-xs font-semibold text-teal-600">tokens</span>
                    </h3>
                  </div>
                  <div className="p-2 rounded-full bg-teal-100 text-teal-700">
                    <Database className="h-4 w-4" />
                  </div>
                </CardContent>
              </Card>

              {/* Sections Count */}
              <Card className="border-slate-200 shadow bg-gradient-to-br from-blue-50 to-white">
                <CardContent className="p-4 flex items-center justify-between">
                  <div>
                    <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Active Sections</p>
                    <h3 className="text-2xl font-extrabold text-blue-900 mt-1">
                      {testResult.metadata.sections_returned.length} <span className="text-xs font-semibold text-blue-600">sections</span>
                    </h3>
                  </div>
                  <div className="p-2 rounded-full bg-blue-100 text-blue-700">
                    <FileText className="h-4 w-4" />
                  </div>
                </CardContent>
              </Card>

              {/* Execution Latency */}
              <Card className="border-slate-200 shadow bg-gradient-to-br from-indigo-50 to-white">
                <CardContent className="p-4 flex items-center justify-between">
                  <div>
                    <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Assembly Duration</p>
                    <h3 className="text-2xl font-extrabold text-indigo-900 mt-1">
                      {latency ? `${latency.toFixed(1)}` : 'N/A'} <span className="text-xs font-semibold text-indigo-600">ms</span>
                    </h3>
                  </div>
                  <div className="p-2 rounded-full bg-indigo-100 text-indigo-700">
                    <Clock className="h-4 w-4" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Main Payload Display */}
            <Card className="border-slate-200 shadow-md bg-white overflow-hidden">
              <CardHeader className="border-b border-slate-100 bg-slate-50/50 flex flex-row items-center justify-between py-4">
                <div>
                  <CardTitle className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                    <Code className="h-5 w-5 text-teal-600" />
                    Structured Context Profile
                  </CardTitle>
                  <CardDescription>
                    Assembled patient context data generated for {selectedPatientName}.
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  <div className="bg-slate-100 border border-slate-200 p-0.5 rounded flex text-xs">
                    <button
                      onClick={() => setActiveSubTab('parsed')}
                      className={`px-2.5 py-1 rounded font-medium transition-all ${
                        activeSubTab === 'parsed'
                          ? 'bg-white shadow-sm text-slate-800'
                          : 'text-slate-500 hover:text-slate-700'
                      }`}
                    >
                      Summary Accordion
                    </button>
                    <button
                      onClick={() => setActiveSubTab('raw')}
                      className={`px-2.5 py-1 rounded font-medium transition-all ${
                        activeSubTab === 'raw'
                          ? 'bg-white shadow-sm text-slate-800'
                          : 'text-slate-500 hover:text-slate-700'
                      }`}
                    >
                      Raw JSON
                    </button>
                  </div>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCopy}
                    className="h-8 gap-1.5"
                  >
                    {copied ? (
                      <>
                        <Check className="h-3.5 w-3.5 text-teal-600" />
                        Copied
                      </>
                    ) : (
                      <>
                        <Copy className="h-3.5 w-3.5" />
                        Copy JSON
                      </>
                    )}
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                {activeSubTab === 'raw' ? (
                  <pre className="p-5 font-mono text-xs text-slate-100 bg-slate-900 shadow-inner overflow-x-auto max-h-[500px] overflow-y-auto">
                    {JSON.stringify(testResult, null, 2)}
                  </pre>
                ) : (
                  <div className="p-6 space-y-4 max-h-[500px] overflow-y-auto">
                    {/* Patient Profile */}
                    {testResult.patient_profile && (
                      <div className="border-b border-slate-100 pb-4">
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wide mb-2">Patient Profile</h4>
                        <div className="grid grid-cols-2 gap-2 text-sm text-slate-600">
                          <div><span className="font-semibold text-slate-500">Name:</span> {testResult.patient_profile.full_name}</div>
                          <div><span className="font-semibold text-slate-500">Email:</span> {testResult.patient_profile.email}</div>
                          <div><span className="font-semibold text-slate-500">Phone:</span> {testResult.patient_profile.phone || 'N/A'}</div>
                          <div><span className="font-semibold text-slate-500">Registered:</span> {new Date(testResult.patient_profile.created_at).toLocaleDateString()}</div>
                        </div>
                      </div>
                    )}

                    {/* Medical Summary */}
                    {testResult.medical_summary && (
                      <div className="border-b border-slate-100 pb-4">
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wide mb-2">Medical Summary</h4>
                        <p className="text-sm text-slate-700 bg-slate-50 border border-slate-100 p-3 rounded-md italic">
                          {testResult.medical_summary}
                        </p>
                      </div>
                    )}

                    {/* Chronic / Active Conditions */}
                    {testResult.current_conditions?.length > 0 && (
                      <div className="border-b border-slate-100 pb-4">
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wide mb-2">Current Conditions</h4>
                        <div className="flex flex-wrap gap-2">
                          {testResult.current_conditions.map((cond: string, i: number) => (
                            <span key={i} className="text-xs bg-red-50 border border-red-100 text-red-700 font-semibold px-2 py-0.5 rounded-full">
                              {cond}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Medications */}
                    {testResult.current_medications?.length > 0 && (
                      <div className="border-b border-slate-100 pb-4">
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wide mb-2">Current Medications</h4>
                        <div className="flex flex-wrap gap-2">
                          {testResult.current_medications.map((med: string, i: number) => (
                            <span key={i} className="text-xs bg-blue-50 border border-blue-100 text-blue-700 font-semibold px-2 py-0.5 rounded-full">
                              {med}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Allergies */}
                    {(testResult.medication_allergies?.length > 0 || testResult.drug_allergies?.length > 0) && (
                      <div className="border-b border-slate-100 pb-4">
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wide mb-2">Allergies</h4>
                        <div className="flex flex-wrap gap-2">
                          {Array.from(new Set([...(testResult.medication_allergies || []), ...(testResult.drug_allergies || [])])).map((all: string, i: number) => (
                            <span key={i} className="text-xs bg-amber-50 border border-amber-100 text-amber-700 font-semibold px-2 py-0.5 rounded-full">
                              {all}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Lifestyle Notes */}
                    {testResult.lifestyle_notes && (
                      <div className="border-b border-slate-100 pb-4">
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wide mb-2">Lifestyle Notes</h4>
                        <p className="text-sm text-slate-600 bg-slate-50 border border-slate-100 p-3 rounded-md">
                          {testResult.lifestyle_notes}
                        </p>
                      </div>
                    )}

                    {/* Emergency Information */}
                    {testResult.emergency_information && (
                      <div className="border-b border-slate-100 pb-4 bg-rose-50 border border-rose-100 p-3 rounded-md">
                        <h4 className="text-xs font-bold text-rose-800 uppercase tracking-wide mb-1 flex items-center gap-1.5">
                          <AlertTriangle className="h-3.5 w-3.5 text-rose-600" />
                          Emergency / Critical Risk Information
                        </h4>
                        <p className="text-sm text-rose-700 font-medium">
                          {testResult.emergency_information}
                        </p>
                      </div>
                    )}

                    {/* List summary lengths */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2">
                      <div className="bg-slate-50 border border-slate-100 p-3 rounded-md text-center">
                        <div className="text-lg font-bold text-slate-800">{testResult.lab_reports_summary?.length || 0}</div>
                        <div className="text-[10px] text-slate-400 uppercase font-semibold">Reports</div>
                      </div>
                      <div className="bg-slate-50 border border-slate-100 p-3 rounded-md text-center">
                        <div className="text-lg font-bold text-slate-800">{testResult.appointments_summary?.length || 0}</div>
                        <div className="text-[10px] text-slate-400 uppercase font-semibold">Appointments</div>
                      </div>
                      <div className="bg-slate-50 border border-slate-100 p-3 rounded-md text-center">
                        <div className="text-lg font-bold text-slate-800">{testResult.consultations_summary?.length || 0}</div>
                        <div className="text-[10px] text-slate-400 uppercase font-semibold">Consultations</div>
                      </div>
                      <div className="bg-slate-50 border border-slate-100 p-3 rounded-md text-center">
                        <div className="text-lg font-bold text-slate-800">{testResult.prescriptions_summary?.length || 0}</div>
                        <div className="text-[10px] text-slate-400 uppercase font-semibold">Prescriptions</div>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}

function IntegrationHealthSummaryBadge() {
  const { data: health, isLoading, isError, refetch } = useAIPlaygroundHealth()

  // Calculate overall connectivity count
  const isHealthy = health && 
    health.groq?.reachable && 
    health.embedding?.status === 'healthy' && 
    health.vector?.connected && 
    health.prompt_registry?.status === 'healthy' && 
    health.context_builder?.status === 'healthy'

  return (
    <Card className="shadow-sm border-slate-200 bg-white px-4 py-2 flex items-center gap-3">
      <div className="flex flex-col">
        <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Orchestrator Status</span>
        {isLoading ? (
          <span className="text-sm font-medium text-slate-500 flex items-center gap-1.5 mt-0.5">
            <RefreshCw className="h-3 w-3 animate-spin" />
            Checking...
          </span>
        ) : isError ? (
          <span className="text-sm font-medium text-red-500 flex items-center gap-1.5 mt-0.5">
            <AlertTriangle className="h-4 w-4" />
            System Errors
          </span>
        ) : isHealthy ? (
          <span className="text-sm font-medium text-teal-600 flex items-center gap-1.5 mt-0.5">
            <CheckCircle2 className="h-4 w-4 text-teal-500" />
            Integrated System Healthy
          </span>
        ) : (
          <span className="text-sm font-medium text-amber-500 flex items-center gap-1.5 mt-0.5">
            <AlertTriangle className="h-4 w-4" />
            Degraded State
          </span>
        )}
      </div>
      <Button 
        variant="ghost" 
        size="icon" 
        onClick={() => refetch()} 
        disabled={isLoading}
        className="h-8 w-8 text-slate-400 hover:text-slate-600"
      >
        <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
      </Button>
    </Card>
  )
}

function IntegrationPlaygroundView() {
  const [prompt, setPrompt] = useState('')
  const [selectedPatientId, setSelectedPatientId] = useState('')
  const [selectedPatientName, setSelectedPatientName] = useState('')
  const [selectedModel, setSelectedModel] = useState('')
  const [temperature, setTemperature] = useState<number>(0.7)
  const [maxTokens, setMaxTokens] = useState<number>(1024)
  const [search, setSearch] = useState('')
  const [testResult, setTestResult] = useState<any>(null)
  const [latency, setLatency] = useState<number | null>(null)
  const [copiedPrompt, setCopiedPrompt] = useState(false)
  const [copiedResponse, setCopiedResponse] = useState(false)
  const [activeSubTab, setActiveSubTab] = useState<'response' | 'prompt' | 'metadata'>('response')

  const { data: health, isLoading: isHealthLoading, isError: isHealthError, refetch: refetchHealth } = useAIPlaygroundHealth()
  const chatMutation = useAIPlaygroundChat()

  // Fetch patients list
  const { data: patientsResponse, isLoading: isLoadingPatients, isError: isPatientsError } = useQuery({
    queryKey: ['admin', 'patients-list'],
    queryFn: () => adminUserService.listUsers(undefined, 'patient')
  })
  const patients = patientsResponse?.data || []

  // Filter patients list based on search term
  const filteredPatients = patients.filter((p: any) =>
    p.full_name?.toLowerCase().includes(search.toLowerCase()) ||
    p.email?.toLowerCase().includes(search.toLowerCase())
  )

  const handleRunChat = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!prompt.trim()) return

    const startTime = performance.now()
    try {
      const result = await chatMutation.mutateAsync({
        prompt: prompt,
        patient_id: selectedPatientId || undefined,
        model: selectedModel || undefined,
        temperature: temperature,
        max_tokens: maxTokens
      })
      const endTime = performance.now()
      setLatency(endTime - startTime)
      setTestResult(result)
    } catch (err) {
      setTestResult(null)
      setLatency(null)
    }
  }

  const handleCopyPrompt = () => {
    if (!testResult?.prompt_template) return
    navigator.clipboard.writeText(testResult.prompt_template)
    setCopiedPrompt(true)
    setTimeout(() => setCopiedPrompt(false), 2000)
  }

  const handleCopyResponse = () => {
    if (!testResult?.response) return
    navigator.clipboard.writeText(testResult.response)
    setCopiedResponse(true)
    setTimeout(() => setCopiedResponse(false), 2000)
  }

  // Health check badges helper status
  const getStatusBadge = (status: string | undefined) => {
    if (!status) return <span className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold bg-slate-100 text-slate-700">Unknown</span>
    const isHealthy = status.toLowerCase() === 'healthy' || status.toLowerCase() === 'connected' || status === 'true'
    return isHealthy ? (
      <span className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold bg-teal-50 text-teal-700 border-teal-200">Healthy</span>
    ) : (
      <span className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold bg-rose-50 text-rose-700 border-rose-200">Unhealthy</span>
    )
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* 1. Health Metrics Overview Panel */}
      <Card className="border-slate-200 shadow-sm bg-white">
        <CardHeader className="pb-3 border-b border-slate-100 bg-slate-50/50 flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-base font-semibold text-slate-800 flex items-center gap-2">
              <Settings className="h-4 w-4 text-slate-500" />
              Integrated Infrastructure Health Overview
            </CardTitle>
            <CardDescription>
              Consolidated connectivity health status across all active system-wide AI endpoints.
            </CardDescription>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => refetchHealth()}
            disabled={isHealthLoading}
            className="text-slate-500 hover:text-slate-700 text-xs gap-1"
          >
            <RefreshCw className={`h-3 w-3 ${isHealthLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </CardHeader>
        <CardContent className="pt-6">
          {isHealthLoading && !health ? (
            <div className="flex justify-center items-center py-6 text-slate-400 gap-2">
              <RefreshCw className="h-4 w-4 animate-spin text-teal-500" />
              <span>Querying integrated health checks...</span>
            </div>
          ) : isHealthError ? (
            <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-rose-500" />
              Failed to fetch consolidated platform health check status.
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
              {/* Groq Card */}
              <div className="p-4 rounded-lg border border-slate-100 bg-slate-50/50 flex flex-col justify-between space-y-2">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Groq LLM</span>
                <div className="flex justify-between items-center">
                  <span className="text-sm font-bold text-slate-700">
                    {health?.groq?.reachable ? 'Reachable' : 'Unreachable'}
                  </span>
                  {health?.groq?.reachable ? (
                    <span className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold bg-teal-50 text-teal-700 border-teal-200">Healthy</span>
                  ) : (
                    <span className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold bg-rose-50 text-rose-700 border-rose-200">Unhealthy</span>
                  )}
                </div>
                <div className="text-[10px] text-slate-400 mt-1">
                  Model: {health?.groq?.model || 'N/A'} <br />
                  Latency: {health?.groq?.latency_ms ? `${health.groq.latency_ms.toFixed(0)} ms` : 'N/A'}
                </div>
              </div>

              {/* Embedding Card */}
              <div className="p-4 rounded-lg border border-slate-100 bg-slate-50/50 flex flex-col justify-between space-y-2">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Embeddings</span>
                <div className="flex justify-between items-center">
                  <span className="text-sm font-bold text-slate-700 capitalize">
                    {health?.embedding?.status || 'Unknown'}
                  </span>
                  {getStatusBadge(health?.embedding?.status)}
                </div>
                <div className="text-[10px] text-slate-400 mt-1">
                  Provider: {health?.embedding?.provider || 'N/A'} <br />
                  Dimensions: {health?.embedding?.dimensions || 'N/A'}
                </div>
              </div>

              {/* Vector DB Card */}
              <div className="p-4 rounded-lg border border-slate-100 bg-slate-50/50 flex flex-col justify-between space-y-2">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Vector DB</span>
                <div className="flex justify-between items-center">
                  <span className="text-sm font-bold text-slate-700">
                    {health?.vector?.connected ? 'Connected' : 'Disconnected'}
                  </span>
                  {health?.vector?.connected ? (
                    <span className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold bg-teal-50 text-teal-700 border-teal-200">Healthy</span>
                  ) : (
                    <span className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold bg-rose-50 text-rose-700 border-rose-200">Unhealthy</span>
                  )}
                </div>
                <div className="text-[10px] text-slate-400 mt-1">
                  Status: {health?.vector?.status || 'N/A'} <br />
                  Collections: {health?.vector?.collections?.length || 0}
                </div>
              </div>

              {/* Prompt Registry Card */}
              <div className="p-4 rounded-lg border border-slate-100 bg-slate-50/50 flex flex-col justify-between space-y-2">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Prompt Registry</span>
                <div className="flex justify-between items-center">
                  <span className="text-sm font-bold text-slate-700 capitalize">
                    {health?.prompt_registry?.status || 'Unknown'}
                  </span>
                  {getStatusBadge(health?.prompt_registry?.status)}
                </div>
                <div className="text-[10px] text-slate-400 mt-1">
                  Version: {health?.prompt_registry?.version || 'N/A'} <br />
                  Templates: {health?.prompt_registry?.templates_count || 'N/A'}
                </div>
              </div>

              {/* Context Builder Card */}
              <div className="p-4 rounded-lg border border-slate-100 bg-slate-50/50 flex flex-col justify-between space-y-2">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Context Builder</span>
                <div className="flex justify-between items-center">
                  <span className="text-sm font-bold text-slate-700 capitalize">
                    {health?.context_builder?.status || 'Unknown'}
                  </span>
                  {getStatusBadge(health?.context_builder?.status)}
                </div>
                <div className="text-[10px] text-slate-400 mt-1">
                  Error: {health?.context_builder?.error ? 'Failed check' : 'None'}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 2. Double Column Layout: Selector + Playground */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Form Configuration */}
        <div className="lg:col-span-1 space-y-6">
          <Card className="border-slate-200 shadow-md bg-white">
            <CardHeader className="border-b border-slate-100 bg-slate-50/50">
              <CardTitle className="text-base font-semibold text-slate-800 flex items-center gap-2">
                <Sliders className="h-4 w-4 text-slate-500" />
                Playground Config
              </CardTitle>
              <CardDescription>
                Configure parameters for context assembly and LLM response generation.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6 space-y-5">
              
              {/* Patient Selector */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Patient Context Override
                </label>
                <div className="relative">
                  <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search patient name/email..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full rounded-md border border-slate-200 pl-8 pr-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
                  />
                </div>

                {isLoadingPatients ? (
                  <div className="flex items-center justify-center py-4 text-slate-400 gap-1.5 text-xs">
                    <RefreshCw className="h-3 w-3 animate-spin text-teal-500" />
                    <span>Loading patients...</span>
                  </div>
                ) : isPatientsError ? (
                  <div className="text-center py-2 text-rose-500 text-xs">
                    Failed to fetch patients list.
                  </div>
                ) : filteredPatients.length === 0 ? (
                  <div className="text-center py-2 text-slate-500 text-xs">
                    No patients match.
                  </div>
                ) : (
                  <div className="max-h-40 overflow-y-auto border border-slate-100 rounded-md divide-y divide-slate-100 text-xs bg-slate-50/30">
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedPatientId('')
                        setSelectedPatientName('')
                      }}
                      className={`w-full text-left px-2.5 py-2 transition-colors flex items-center justify-between ${
                        selectedPatientId === ''
                          ? 'bg-teal-50 font-semibold text-teal-700 font-bold'
                          : 'hover:bg-slate-50 text-slate-600'
                      }`}
                    >
                      <span>No Patient (Null Context)</span>
                      {selectedPatientId === '' && (
                        <CheckCircle2 className="h-3.5 w-3.5 text-teal-600" />
                      )}
                    </button>
                    {filteredPatients.map((patient: any) => (
                      <button
                        key={patient.id}
                        type="button"
                        onClick={() => {
                          setSelectedPatientId(patient.id)
                          setSelectedPatientName(patient.full_name)
                        }}
                        className={`w-full text-left px-2.5 py-2 transition-colors flex items-center justify-between ${
                          selectedPatientId === patient.id
                            ? 'bg-teal-50 font-semibold text-teal-700 font-bold'
                            : 'hover:bg-slate-50 text-slate-600'
                        }`}
                      >
                        <div className="truncate pr-2">
                          <span className="font-semibold text-slate-800">{patient.full_name}</span>
                          <span className="text-[10px] text-slate-400 block truncate">{patient.email}</span>
                        </div>
                        {selectedPatientId === patient.id && (
                          <CheckCircle2 className="h-3.5 w-3.5 text-teal-600 flex-shrink-0" />
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Model Selector */}
              <div className="space-y-2">
                <label htmlFor="model-select" className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  LLM Model Selector
                </label>
                <select
                  id="model-select"
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs text-slate-800 shadow-sm focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
                >
                  <option value="">System Default ({health?.groq?.model || 'llama-3.3-70b-versatile'})</option>
                  <option value="llama-3.3-70b-versatile">llama-3.3-70b-versatile</option>
                  <option value="llama-3.1-8b-instant">llama-3.1-8b-instant</option>
                  <option value="mixtral-8x7b-32768">mixtral-8x7b-32768</option>
                </select>
              </div>

              {/* Temperature Slider */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-xs">
                  <label className="font-bold text-slate-700 uppercase tracking-wider">
                    Temperature
                  </label>
                  <span className="font-mono font-semibold text-teal-600 bg-teal-50 border border-teal-100 rounded px-1.5 py-0.5">
                    {temperature.toFixed(1)}
                  </span>
                </div>
                <input
                  type="range"
                  min="0.0"
                  max="2.0"
                  step="0.1"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-teal-600"
                />
                <div className="flex justify-between text-[10px] text-slate-400 font-medium">
                  <span>Deterministic (0.0)</span>
                  <span>Creative (2.0)</span>
                </div>
              </div>

              {/* Max Tokens Slider */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-xs">
                  <label className="font-bold text-slate-700 uppercase tracking-wider">
                    Max Tokens
                  </label>
                  <span className="font-mono font-semibold text-teal-600 bg-teal-50 border border-teal-100 rounded px-1.5 py-0.5">
                    {maxTokens}
                  </span>
                </div>
                <input
                  type="range"
                  min="256"
                  max="4096"
                  step="128"
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                  className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-teal-600"
                />
                <div className="flex justify-between text-[10px] text-slate-400 font-medium">
                  <span>Short (256)</span>
                  <span>Long (4096)</span>
                </div>
              </div>

            </CardContent>
          </Card>
        </div>

        {/* Right Column: Execution Form Console + Responses */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="border-slate-200 shadow-md bg-white">
            <CardHeader className="border-b border-slate-100 bg-slate-50/50">
              <CardTitle className="text-base font-semibold text-slate-800 flex items-center gap-2">
                <Terminal className="h-4 w-4 text-slate-500" />
                Integration Playground Console
              </CardTitle>
              <CardDescription>
                Test prompt templates mapped with real patient database profiles. Coordinates context rendering and LLM calls.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <form onSubmit={handleRunChat} className="space-y-4">
                <div className="space-y-2">
                  <label htmlFor="integration-prompt" className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                    User Query / Prompt
                  </label>
                  <Textarea
                    id="integration-prompt"
                    placeholder="Enter medical question or symptom search query..."
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    rows={4}
                    disabled={chatMutation.isPending}
                    className="border-slate-200 focus:border-teal-500 focus:ring-teal-500 resize-none font-sans text-sm"
                  />
                </div>

                <div className="flex justify-between items-center pt-2">
                  <div className="text-xs text-slate-400 font-medium">
                    {selectedPatientId ? (
                      <span className="flex items-center gap-1 text-teal-600 font-semibold bg-teal-50 border border-teal-100 rounded px-2 py-0.5">
                        <Users className="h-3 w-3" /> Context: {selectedPatientName}
                      </span>
                    ) : (
                      <span className="text-slate-400 italic">No patient context selected</span>
                    )}
                  </div>
                  <Button
                    type="submit"
                    disabled={!prompt.trim() || chatMutation.isPending}
                    className="bg-teal-600 hover:bg-teal-700 text-white font-semibold transition-all px-5"
                  >
                    {chatMutation.isPending ? (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                        Generating Response...
                      </>
                    ) : (
                      <>
                        <Zap className="h-4 w-4 mr-2" />
                        Execute Orchestrator
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          {/* Response & Telemetry Output */}
          {chatMutation.isPending && (
            <Card className="border-slate-200 shadow-md bg-white">
              <CardContent className="py-12 flex flex-col items-center justify-center text-slate-400 gap-3">
                <RefreshCw className="h-8 w-8 animate-spin text-teal-500" />
                <p className="text-sm font-medium animate-pulse text-slate-500">Executing integration orchestrator lifecycle...</p>
                <p className="text-xs text-slate-400 text-center max-w-sm">
                  Assembling MongoDB context, loading & checking templates, formatting variables, and calling Groq LLM endpoint.
                </p>
              </CardContent>
            </Card>
          )}

          {chatMutation.isError && (
            <Card className="border-slate-200 shadow-md bg-white">
              <CardContent className="pt-6">
                <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 flex items-start gap-3">
                  <AlertTriangle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold">Orchestration Call Failed</h4>
                    <p className="text-sm mt-1 text-red-600">
                      {chatMutation.error?.message || 'An unexpected error occurred during execution.'}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {testResult && !chatMutation.isPending && (
            <div className="space-y-6">
              
              {/* Telemetry Metrics Row */}
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                
                {/* Total Latency */}
                <Card className="border-slate-200 shadow bg-gradient-to-br from-teal-50 to-white">
                  <CardContent className="p-4 flex items-center justify-between">
                    <div>
                      <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Total Duration</p>
                      <h3 className="text-xl font-extrabold text-teal-900 mt-1">
                        {testResult.execution_session?.duration?.toFixed(0) || latency?.toFixed(0) || 'N/A'} <span className="text-xs font-semibold text-teal-600">ms</span>
                      </h3>
                    </div>
                    <div className="p-2 rounded-full bg-teal-100 text-teal-700">
                      <Clock className="h-4 w-4" />
                    </div>
                  </CardContent>
                </Card>

                {/* Token Count */}
                <Card className="border-slate-200 shadow bg-gradient-to-br from-blue-50 to-white">
                  <CardContent className="p-4 flex items-center justify-between">
                    <div>
                      <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Token Usage</p>
                      <h3 className="text-xl font-extrabold text-blue-900 mt-1">
                        {testResult.execution_session?.tokens || 0} <span className="text-xs font-semibold text-blue-600">tkn</span>
                      </h3>
                    </div>
                    <div className="p-2 rounded-full bg-blue-100 text-blue-700">
                      <Database className="h-4 w-4" />
                    </div>
                  </CardContent>
                </Card>

                {/* Estimated Cost */}
                <Card className="border-slate-200 shadow bg-gradient-to-br from-indigo-50 to-white">
                  <CardContent className="p-4 flex items-center justify-between">
                    <div>
                      <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Estimated Cost</p>
                      <h3 className="text-xl font-extrabold text-indigo-900 mt-1">
                        ${testResult.execution_session?.cost?.toFixed(5) || '0.00000'}
                      </h3>
                    </div>
                    <div className="p-2 rounded-full bg-indigo-100 text-indigo-700">
                      <Zap className="h-4 w-4" />
                    </div>
                  </CardContent>
                </Card>

                {/* Model Used */}
                <Card className="border-slate-200 shadow bg-gradient-to-br from-slate-50 to-white">
                  <CardContent className="p-4 flex items-center justify-between">
                    <div>
                      <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Model Executed</p>
                      <h3 className="text-xs font-bold text-slate-800 mt-1 truncate max-w-[100px]" title={testResult.execution_session?.model}>
                        {testResult.execution_session?.model || 'Unknown'}
                      </h3>
                    </div>
                    <div className="p-2 rounded-full bg-slate-100 text-slate-700">
                      <Cpu className="h-4 w-4" />
                    </div>
                  </CardContent>
                </Card>

              </div>

              {/* Main Response & Debug Console Tabs */}
              <Card className="border-slate-200 shadow-md bg-white overflow-hidden">
                <CardHeader className="border-b border-slate-100 bg-slate-50/50 flex flex-row items-center justify-between py-4">
                  <div>
                    <CardTitle className="text-base font-semibold text-slate-800">
                      Orchestration Response Details
                    </CardTitle>
                    <CardDescription>
                      Review the model completions, assembled inputs, templates, and execution contexts.
                    </CardDescription>
                  </div>
                  
                  <div className="flex gap-2">
                    <div className="bg-slate-100 border border-slate-200 p-0.5 rounded flex text-[10px] font-medium">
                      <button
                        type="button"
                        onClick={() => setActiveSubTab('response')}
                        className={`px-2 py-1 rounded transition-all ${
                          activeSubTab === 'response'
                            ? 'bg-white shadow-sm text-slate-800 font-bold'
                            : 'text-slate-500 hover:text-slate-700 font-semibold'
                        }`}
                      >
                        Model Output
                      </button>
                      <button
                        type="button"
                        onClick={() => setActiveSubTab('prompt')}
                        className={`px-2 py-1 rounded transition-all ${
                          activeSubTab === 'prompt'
                            ? 'bg-white shadow-sm text-slate-800 font-bold'
                            : 'text-slate-500 hover:text-slate-700 font-semibold'
                        }`}
                      >
                        Assembled Prompt
                      </button>
                      <button
                        type="button"
                        onClick={() => setActiveSubTab('metadata')}
                        className={`px-2 py-1 rounded transition-all ${
                          activeSubTab === 'metadata'
                            ? 'bg-white shadow-sm text-slate-800 font-bold'
                            : 'text-slate-500 hover:text-slate-700 font-semibold'
                        }`}
                      >
                        Metadata Traces
                      </button>
                    </div>
                  </div>
                </CardHeader>
                
                <CardContent className="p-0">
                  {/* Model Response Tab */}
                  {activeSubTab === 'response' && (
                    <div className="p-5 space-y-4">
                      <div className="flex justify-between items-center text-xs text-slate-400 font-semibold uppercase tracking-wide">
                        <span>Response Content</span>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={handleCopyResponse}
                          className="h-7 text-[10px] gap-1 px-2.5"
                        >
                          {copiedResponse ? (
                            <>
                              <Check className="h-3 w-3 text-teal-600" />
                              Copied
                            </>
                          ) : (
                            <>
                              <Copy className="h-3 w-3" />
                              Copy Completion
                            </>
                          )}
                        </Button>
                      </div>
                      <div className="rounded-lg border border-slate-200 bg-slate-50 p-5 font-sans text-sm text-slate-800 whitespace-pre-wrap leading-relaxed shadow-inner max-h-[400px] overflow-y-auto">
                        {testResult.response || <span className="italic text-slate-400">Empty response from model</span>}
                      </div>
                    </div>
                  )}

                  {/* Assembled Prompt Tab */}
                  {activeSubTab === 'prompt' && (
                    <div className="p-5 space-y-4">
                      <div className="flex justify-between items-center text-xs text-slate-400 font-semibold uppercase tracking-wide">
                        <span>Final Assembled Payload (System + User Prompt templates)</span>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={handleCopyPrompt}
                          className="h-7 text-[10px] gap-1 px-2.5"
                        >
                          {copiedPrompt ? (
                            <>
                              <Check className="h-3 w-3 text-teal-600" />
                              Copied
                            </>
                          ) : (
                            <>
                              <Copy className="h-3 w-3" />
                              Copy Prompt
                            </>
                          )}
                        </Button>
                      </div>
                      <div className="rounded-lg border border-slate-200 bg-slate-900 p-5 font-mono text-xs text-teal-400 whitespace-pre-wrap leading-relaxed shadow-inner max-h-[400px] overflow-y-auto">
                        {testResult.prompt_template || <span className="italic text-slate-500">No prompt templates assembled</span>}
                      </div>
                    </div>
                  )}

                  {/* Metadata Traces Tab */}
                  {activeSubTab === 'metadata' && (
                    <div className="p-5 space-y-4 text-xs">
                      {/* Session Metadata */}
                      <div className="space-y-2 border-b border-slate-100 pb-4">
                        <h4 className="font-bold text-slate-700 uppercase tracking-wider">Execution Session Metadata</h4>
                        <div className="grid grid-cols-2 gap-4 text-slate-600">
                          <div>
                            <span className="font-semibold text-slate-500">Request Trace ID:</span>{' '}
                            <span className="font-mono bg-slate-100 px-1.5 py-0.5 rounded text-slate-700">
                              {testResult.execution_session?.request_id}
                            </span>
                          </div>
                          <div>
                            <span className="font-semibold text-slate-500">Execution Status:</span>{' '}
                            <span className="font-semibold text-teal-600 capitalize">
                              {testResult.execution_session?.status}
                            </span>
                          </div>
                          <div>
                            <span className="font-semibold text-slate-500">Start Time:</span>{' '}
                            <span>{testResult.execution_session?.start_time ? new Date(testResult.execution_session.start_time).toLocaleString() : 'N/A'}</span>
                          </div>
                          <div>
                            <span className="font-semibold text-slate-500">End Time:</span>{' '}
                            <span>{testResult.execution_session?.end_time ? new Date(testResult.execution_session.end_time).toLocaleString() : 'N/A'}</span>
                          </div>
                        </div>
                      </div>

                      {/* Context Metadata */}
                      <div className="space-y-2">
                        <h4 className="font-bold text-slate-700 uppercase tracking-wider">Assembled Context Sections</h4>
                        {testResult.patient_context_sections?.length > 0 ? (
                          <div className="flex flex-wrap gap-2 pt-1">
                            {testResult.patient_context_sections.map((section: string) => (
                              <span key={section} className="font-mono bg-slate-100 border border-slate-200 px-2 py-0.5 rounded text-slate-700 font-semibold">
                                {section}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="italic text-slate-400">No patient database records assembled in this call context.</span>
                        )}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

        </div>
      </div>
    </div>
  )
}

function IndexingHealthBadge() {
  const { 
    data: stats, 
    isLoading, 
    isError, 
    refetch 
  } = useIndexStatistics()

  return (
    <Card className="shadow-sm border-slate-200 bg-white px-4 py-2 flex items-center gap-3">
      <div className="flex flex-col">
        <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Indexing Pipeline</span>
        {isLoading ? (
          <span className="text-sm font-medium text-slate-500 flex items-center gap-1.5 mt-0.5">
            <RefreshCw className="h-3 w-3 animate-spin" />
            Loading...
          </span>
        ) : isError ? (
          <span className="text-sm font-medium text-red-500 flex items-center gap-1.5 mt-0.5">
            <AlertTriangle className="h-4 w-4" />
            Error Loading Stats
          </span>
        ) : (
          <span className="text-sm font-medium text-teal-600 flex items-center gap-1.5 mt-0.5">
            <CheckCircle2 className="h-4 w-4 text-teal-500" />
            Active ({stats?.embedding_version || 'v1'})
          </span>
        )}
      </div>
      <Button 
        variant="ghost" 
        size="icon" 
        onClick={() => refetch()} 
        disabled={isLoading}
        className="h-8 w-8 text-slate-400 hover:text-slate-600"
      >
        <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
      </Button>
    </Card>
  )
}

function IndexingPlaygroundView() {
  const { data: stats, isLoading: isStatsLoading, refetch: refetchStats } = useIndexStatistics()
  
  const indexDocMutation = useIndexDocument()
  const reindexDocMutation = useReindexDocument()
  const batchIndexDocMutation = useBatchIndexDocuments()
  const deleteDocMutation = useDeleteDocument()
  const deletePatientMutation = useDeletePatientDocuments()

  // Single test console state
  const [docId, setDocId] = useState('doc_test_' + Math.floor(Math.random() * 10000))
  const [docType, setDocType] = useState('REPORT')
  const [content, setContent] = useState('Patient displays high blood pressure of 145/95 mmHg. Recommended regular exercise and sodium-restricted diet.')
  const [strategy, setStrategy] = useState('fixed')
  const [chunkSize, setChunkSize] = useState(200)
  const [overlap, setOverlap] = useState(20)
  const [patientId, setPatientId] = useState('pat_123')
  const [reportId, setReportId] = useState('rep_456')
  const [pageNumber, setPageNumber] = useState(1)
  const [section, setSection] = useState('diagnosis')
  const [source, setSource] = useState('mongodb')
  const [language, setLanguage] = useState('en')
  
  const [singleResult, setSingleResult] = useState<any>(null)
  const [isReindexing, setIsReindexing] = useState(false)

  // Batch simulator state
  const [batchRawText, setBatchRawText] = useState(
    JSON.stringify([
      {
        document_id: "batch_doc_1",
        document_type: "REPORT",
        content: "Patient diagnosed with stage 1 chronic kidney disease. Plan to review serum creatinine in 3 months.",
        patient_id: "pat_789",
        report_id: "rep_001"
      },
      {
        document_id: "batch_doc_2",
        document_type: "MEDICAL_ARTICLE",
        content: "Metformin remains the primary first-line pharmacotherapeutic agent for type 2 diabetes mellitus mellitus care.",
        section: "introduction"
      }
    ], null, 2)
  )
  const [batchResult, setBatchResult] = useState<any>(null)
  const [batchError, setBatchError] = useState<string | null>(null)

  // Deletion tool state
  const [delDocId, setDelDocId] = useState('')
  const [delDocType, setDelDocType] = useState('REPORT')
  const [delPatientId, setDelPatientId] = useState('')
  const [deletionResult, setDeletionResult] = useState<string | null>(null)

  // single index submit handler
  const handleSingleIndexSubmit = async (e: React.FormEvent, reindex = false) => {
    e.preventDefault()
    if (!docId.trim() || !content.trim()) return

    setSingleResult(null)
    const payload = {
      document_id: docId,
      document_type: docType,
      content: content,
      chunking_strategy: strategy,
      chunk_size: chunkSize,
      overlap: overlap,
      patient_id: patientId || undefined,
      report_id: reportId || undefined,
      page_number: pageNumber,
      section: section || undefined,
      source: source || undefined,
      language: language || undefined,
      created_by: 'admin_playground'
    }

    try {
      let res
      if (reindex) {
        setIsReindexing(true)
        res = await reindexDocMutation.mutateAsync(payload)
      } else {
        setIsReindexing(false)
        res = await indexDocMutation.mutateAsync(payload)
      }
      setSingleResult(res)
      refetchStats()
    } catch (err: any) {
      setSingleResult({ success: false, error: err.message || 'Indexing failed' })
    }
  }

  // batch index submit handler
  const handleBatchIndexSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setBatchResult(null)
    setBatchError(null)
    try {
      const parsedDocs = JSON.parse(batchRawText)
      if (!Array.isArray(parsedDocs)) {
        throw new Error("Input must be a JSON array of document objects")
      }
      
      const payload = {
        documents: parsedDocs.map((doc: any, index: number) => ({
          document_id: doc.document_id || `batch_doc_${index}_${Math.floor(Math.random() * 1000)}`,
          document_type: doc.document_type || 'REPORT',
          content: doc.content || '',
          chunking_strategy: doc.chunking_strategy || strategy,
          chunk_size: doc.chunk_size || chunkSize,
          overlap: doc.overlap || overlap,
          patient_id: doc.patient_id,
          report_id: doc.report_id,
          page_number: doc.page_number || 1,
          section: doc.section || 'content',
          source: doc.source || 'mongodb',
          language: doc.language || 'en',
          created_by: 'admin_playground_batch'
        }))
      }

      const res = await batchIndexDocMutation.mutateAsync(payload)
      setBatchResult(res)
      refetchStats()
    } catch (err: any) {
      setBatchError(err.message || "Failed to process batch payload. Check JSON format validity.")
    }
  }

  // document deletion handler
  const handleDeleteDoc = async () => {
    if (!delDocId.trim()) return
    setDeletionResult(null)
    try {
      const res = await deleteDocMutation.mutateAsync({ documentId: delDocId, documentType: delDocType })
      setDeletionResult(res.message || (res.success ? "Document deleted successfully" : "Deletion failed"))
      refetchStats()
    } catch (err: any) {
      setDeletionResult(`Error: ${err.message || 'Deletion failed'}`)
    }
  }

  // patient reports deletion handler
  const handleDeletePatientDocs = async () => {
    if (!delPatientId.trim()) return
    setDeletionResult(null)
    try {
      const res = await deletePatientMutation.mutateAsync(delPatientId)
      setDeletionResult(res.message || (res.success ? "Patient documents deleted successfully" : "Deletion failed"))
      refetchStats()
    } catch (err: any) {
      setDeletionResult(`Error: ${err.message || 'Deletion failed'}`)
    }
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-350">
      
      {/* 1. Statistics Cards Panel */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-slate-200 shadow bg-gradient-to-br from-teal-50 to-white hover:shadow-md transition-all">
          <CardContent className="p-6 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Indexed Documents</p>
              <h3 className="text-3xl font-extrabold text-teal-900 mt-1">
                {isStatsLoading ? '...' : stats?.indexed_documents ?? 0}
              </h3>
              <p className="text-[10px] text-slate-400 mt-2">MongoDB documents vectorized in Qdrant</p>
            </div>
            <div className="p-3 rounded-full bg-teal-100 text-teal-700">
              <FileText className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow bg-gradient-to-br from-blue-50 to-white hover:shadow-md transition-all">
          <CardContent className="p-6 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Vector Chunks Count</p>
              <h3 className="text-3xl font-extrabold text-blue-900 mt-1">
                {isStatsLoading ? '...' : stats?.indexed_chunks ?? 0}
              </h3>
              <p className="text-[10px] text-slate-400 mt-2">Total active chunks in vector storage</p>
            </div>
            <div className="p-3 rounded-full bg-blue-100 text-blue-700">
              <Database className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow bg-gradient-to-br from-amber-50 to-white hover:shadow-md transition-all">
          <CardContent className="p-6 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Duplicate Skipped Chunks</p>
              <h3 className="text-3xl font-extrabold text-amber-900 mt-1">
                {isStatsLoading ? '...' : stats?.duplicate_documents_skipped ?? 0}
              </h3>
              <p className="text-[10px] text-slate-400 mt-2">Skipped using hash duplication check</p>
            </div>
            <div className="p-3 rounded-full bg-amber-100 text-amber-700">
              <AlertTriangle className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow bg-gradient-to-br from-indigo-50 to-white hover:shadow-md transition-all">
          <CardContent className="p-6 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Avg Chunk Size</p>
              <h3 className="text-2xl font-extrabold text-indigo-900 mt-1">
                {isStatsLoading ? '...' : Math.round(stats?.avg_chunk_size ?? 0)}{' '}
                <span className="text-xs font-semibold text-slate-500">chars</span>
              </h3>
              <p className="text-[10px] text-slate-400 mt-2">Average character length of indexed chunks</p>
            </div>
            <div className="p-3 rounded-full bg-indigo-100 text-indigo-700">
              <Activity className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Versioning and configuration metadata audit info */}
      {!isStatsLoading && stats && (
        <div className="p-3 bg-slate-50 border border-slate-200 rounded-md text-xs text-slate-600 flex flex-wrap gap-x-6 gap-y-2">
          <div><span className="font-semibold text-slate-500">Embedding Schema:</span> {stats.embedding_version}</div>
          <div><span className="font-semibold text-slate-500">Index Form Version:</span> v{stats.index_version}</div>
          <div><span className="font-semibold text-slate-500">Schema Version:</span> v{stats.schema_version}</div>
          <div className="ml-auto text-slate-400 italic">Centralized pipeline models mapping automatically loaded</div>
        </div>
      )}

      {/* 2. Double Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Single Test Console & Batch Simulator (col-span-2) */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Single Test Console */}
          <Card className="border-slate-200 shadow-md bg-white">
            <CardHeader className="border-b border-slate-100 bg-slate-50/50">
              <CardTitle className="text-base font-semibold text-slate-800 flex items-center gap-2">
                <Terminal className="h-4 w-4 text-slate-500" />
                Single Document Index Console
              </CardTitle>
              <CardDescription>
                Test chunking, embedding generation, hash lookup, and Qdrant ingestion for a single record.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <form className="space-y-4">
                
                {/* Document details grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-1.5">
                    <label htmlFor="index-doc-id" className="text-xs font-bold text-slate-600 uppercase">Document ID</label>
                    <input 
                      id="index-doc-id"
                      type="text" 
                      value={docId} 
                      onChange={(e) => setDocId(e.target.value)}
                      className="w-full rounded border border-slate-200 px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-teal-500"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label htmlFor="index-doc-type" className="text-xs font-bold text-slate-600 uppercase">Document Type</label>
                    <select 
                      id="index-doc-type"
                      value={docType} 
                      onChange={(e) => setDocType(e.target.value)}
                      className="w-full rounded border border-slate-200 px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-teal-500"
                    >
                      <option value="REPORT">REPORT (patient_reports)</option>
                      <option value="MEDICAL_ARTICLE">MEDICAL_ARTICLE (medical_knowledge)</option>
                      <option value="DRUG_DATASET">DRUG_DATASET (drug_knowledge)</option>
                      <option value="DOCTOR_PROFILE">DOCTOR_PROFILE (doctor_knowledge)</option>
                      <option value="CHAT_MEMORY">CHAT_MEMORY (chat_memory)</option>
                    </select>
                  </div>
                  <div className="space-y-1.5">
                    <label htmlFor="index-strategy" className="text-xs font-bold text-slate-600 uppercase">Chunking Strategy</label>
                    <select 
                      id="index-strategy"
                      value={strategy} 
                      onChange={(e) => setStrategy(e.target.value)}
                      className="w-full rounded border border-slate-200 px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-teal-500"
                    >
                      <option value="fixed">Fixed Character Limit</option>
                      <option value="paragraph">Paragraph Breaks</option>
                      <option value="sliding_window">Sliding Window</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="space-y-1.5">
                    <label htmlFor="index-chunk-size" className="text-xs font-bold text-slate-600 uppercase">Chunk Size</label>
                    <input 
                      id="index-chunk-size"
                      type="number" 
                      value={chunkSize} 
                      onChange={(e) => setChunkSize(parseInt(e.target.value))}
                      className="w-full rounded border border-slate-200 px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-teal-500"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label htmlFor="index-overlap" className="text-xs font-bold text-slate-600 uppercase">Overlap</label>
                    <input 
                      id="index-overlap"
                      type="number" 
                      value={overlap} 
                      onChange={(e) => setOverlap(parseInt(e.target.value))}
                      className="w-full rounded border border-slate-200 px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-teal-500"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label htmlFor="index-patient-id" className="text-xs font-bold text-slate-600 uppercase">Patient ID</label>
                    <input 
                      id="index-patient-id"
                      type="text" 
                      value={patientId} 
                      onChange={(e) => setPatientId(e.target.value)}
                      className="w-full rounded border border-slate-200 px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-teal-500"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label htmlFor="index-report-id" className="text-xs font-bold text-slate-600 uppercase">Report ID</label>
                    <input 
                      id="index-report-id"
                      type="text" 
                      value={reportId} 
                      onChange={(e) => setReportId(e.target.value)}
                      className="w-full rounded border border-slate-200 px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-teal-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="space-y-1.5">
                    <label htmlFor="index-page" className="text-xs font-bold text-slate-600 uppercase">Page No.</label>
                    <input 
                      id="index-page"
                      type="number" 
                      value={pageNumber} 
                      onChange={(e) => setPageNumber(parseInt(e.target.value))}
                      className="w-full rounded border border-slate-200 px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-teal-500"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label htmlFor="index-section" className="text-xs font-bold text-slate-600 uppercase">Section</label>
                    <input 
                      id="index-section"
                      type="text" 
                      value={section} 
                      onChange={(e) => setSection(e.target.value)}
                      className="w-full rounded border border-slate-200 px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-teal-500"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label htmlFor="index-source" className="text-xs font-bold text-slate-600 uppercase">Source</label>
                    <input 
                      id="index-source"
                      type="text" 
                      value={source} 
                      onChange={(e) => setSource(e.target.value)}
                      className="w-full rounded border border-slate-200 px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-teal-500"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label htmlFor="index-lang" className="text-xs font-bold text-slate-600 uppercase">Language</label>
                    <input 
                      id="index-lang"
                      type="text" 
                      value={language} 
                      onChange={(e) => setLanguage(e.target.value)}
                      className="w-full rounded border border-slate-200 px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-teal-500"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label htmlFor="index-content" className="text-xs font-bold text-slate-600 uppercase">Document Content Text</label>
                  <Textarea 
                    id="index-content"
                    value={content} 
                    onChange={(e) => setContent(e.target.value)}
                    rows={4}
                    className="text-xs border-slate-200 resize-none font-sans"
                    placeholder="Paste medical record text content here..."
                  />
                </div>

                <div className="flex gap-4 justify-end pt-2">
                  <Button
                    type="button"
                    onClick={(e) => handleSingleIndexSubmit(e, true)}
                    disabled={!content.trim() || indexDocMutation.isPending || reindexDocMutation.isPending}
                    variant="outline"
                    className="border-slate-200 text-slate-700 font-semibold"
                  >
                    {reindexDocMutation.isPending && isReindexing ? (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                        Reindexing...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Reindex Document
                      </>
                    )}
                  </Button>

                  <Button
                    type="button"
                    onClick={(e) => handleSingleIndexSubmit(e, false)}
                    disabled={!content.trim() || indexDocMutation.isPending || reindexDocMutation.isPending}
                    className="bg-teal-600 hover:bg-teal-700 text-white font-semibold"
                  >
                    {indexDocMutation.isPending && !isReindexing ? (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                        Vectorizing...
                      </>
                    ) : (
                      <>
                        <Zap className="h-4 w-4 mr-2" />
                        Index Document
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          {/* Single Test Console Result Panel */}
          {singleResult && (
            <Card className="border-slate-200 shadow bg-white overflow-hidden animate-in fade-in duration-350">
              <CardHeader className="border-b border-slate-100 bg-slate-50/50 py-3">
                <CardTitle className="text-sm font-bold text-slate-800 flex items-center gap-1.5">
                  {singleResult.success ? (
                    <CheckCircle2 className="h-4 w-4 text-teal-500" />
                  ) : (
                    <AlertTriangle className="h-4 w-4 text-red-500" />
                  )}
                  Single Document Outcome Traces
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 space-y-3 text-xs">
                {singleResult.success ? (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
                    <div className="bg-slate-50 border border-slate-100 rounded p-2">
                      <div className="font-bold text-slate-800 capitalize">{singleResult.status}</div>
                      <div className="text-[10px] text-slate-400 uppercase">Outcome Status</div>
                    </div>
                    <div className="bg-slate-50 border border-slate-100 rounded p-2">
                      <div className="font-bold text-slate-800">{singleResult.chunks_count}</div>
                      <div className="text-[10px] text-slate-400 uppercase">Chunks Indexed</div>
                    </div>
                    <div className="bg-slate-50 border border-slate-100 rounded p-2">
                      <div className="font-bold text-slate-800">{singleResult.skipped_count ?? 0}</div>
                      <div className="text-[10px] text-slate-400 uppercase">Duplicate Skipped</div>
                    </div>
                    <div className="bg-slate-50 border border-slate-100 rounded p-2">
                      <div className="font-bold text-slate-800">
                        {singleResult.latency_ms ? `${singleResult.latency_ms.toFixed(0)} ms` : 'N/A'}
                      </div>
                      <div className="text-[10px] text-slate-400 uppercase">Execution Time</div>
                    </div>
                  </div>
                ) : (
                  <div className="p-3 bg-rose-50 border border-rose-100 rounded text-rose-700 font-medium">
                    {singleResult.error}
                  </div>
                )}
                {singleResult.message && (
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded font-mono text-[10px] text-slate-600 whitespace-pre-wrap">
                    {singleResult.message}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Batch Simulator Console */}
          <Card className="border-slate-200 shadow-md bg-white">
            <CardHeader className="border-b border-slate-100 bg-slate-50/50">
              <CardTitle className="text-base font-semibold text-slate-800 flex items-center gap-2">
                <Layers className="h-4 w-4 text-slate-500" />
                Batch Document Indexing Simulator
              </CardTitle>
              <CardDescription>
                Index multiple documents in parallel using standard settings. Provide input as a JSON array of documents.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <form onSubmit={handleBatchIndexSubmit} className="space-y-4">
                <div className="space-y-1.5">
                  <div className="flex justify-between items-center">
                    <label htmlFor="batch-json" className="text-xs font-bold text-slate-600 uppercase">Batch JSON DTO List</label>
                    <span className="text-[10px] text-slate-400">Array mapping required fields: document_id, document_type, content</span>
                  </div>
                  <Textarea 
                    id="batch-json"
                    value={batchRawText}
                    onChange={(e) => setBatchRawText(e.target.value)}
                    rows={8}
                    className="font-mono text-xs border-slate-200 focus:border-teal-500"
                  />
                </div>

                <div className="flex justify-end">
                  <Button
                    type="submit"
                    disabled={!batchRawText.trim() || batchIndexDocMutation.isPending}
                    className="bg-teal-600 hover:bg-teal-700 text-white font-semibold"
                  >
                    {batchIndexDocMutation.isPending ? (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                        Processing Async Batch...
                      </>
                    ) : (
                      <>
                        <Zap className="h-4 w-4 mr-2" />
                        Execute Batch Index
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          {/* Batch Simulator Output */}
          {batchError && (
            <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
              {batchError}
            </div>
          )}

          {batchResult && (
            <Card className="border-slate-200 shadow bg-white overflow-hidden animate-in fade-in duration-350">
              <CardHeader className="border-b border-slate-100 bg-slate-50/50 py-3">
                <CardTitle className="text-sm font-bold text-slate-800 flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4 text-teal-500" />
                  Batch Process Run Results ({batchResult.results?.length ?? 0} docs)
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 space-y-3 text-xs">
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {batchResult.results?.map((res: any, idx: number) => (
                    <div key={idx} className="flex justify-between items-center p-2 rounded border border-slate-100 bg-slate-50/30">
                      <div>
                        <span className="font-mono text-[10px] bg-slate-200 text-slate-700 px-1 rounded mr-2">{res.document_id}</span>
                        {res.message && <span className="text-slate-500 text-[10px]">{res.message}</span>}
                        {res.error && <span className="text-red-500 font-semibold">{res.error}</span>}
                      </div>
                      <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${
                        res.status === 'indexed' ? 'bg-teal-50 text-teal-700 border border-teal-100' :
                        res.status === 'skipped' ? 'bg-amber-50 text-amber-700 border border-amber-100' :
                        'bg-red-50 text-red-700 border border-red-100'
                      }`}>
                        {res.status}
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

        </div>

        {/* Administration Tools and Collection Actions (col-span-1) */}
        <div className="space-y-6">
          
          <Card className="border-slate-200 shadow-md bg-white">
            <CardHeader className="border-b border-slate-100 bg-slate-50/50">
              <CardTitle className="text-base font-semibold text-slate-800 flex items-center gap-2">
                <Trash2 className="h-4 w-4 text-slate-500" />
                Index Removal Tools
              </CardTitle>
              <CardDescription>
                Perform administrative deletions of specific document vectors or patient contextual reports from the Qdrant collections.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6 space-y-4">
              
              {/* Delete specific document */}
              <div className="space-y-2 border-b border-slate-100 pb-4">
                <h4 className="text-xs font-bold text-slate-700 uppercase">Document Vector Purge</h4>
                <div className="grid grid-cols-1 gap-2">
                  <div className="space-y-1">
                    <label htmlFor="del-doc-id" className="text-[10px] text-slate-400 font-semibold uppercase">Document ID</label>
                    <input 
                      id="del-doc-id"
                      type="text" 
                      placeholder="e.g. report_123"
                      value={delDocId} 
                      onChange={(e) => setDelDocId(e.target.value)}
                      className="w-full rounded border border-slate-200 px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-teal-500"
                    />
                  </div>
                  <div className="space-y-1">
                    <label htmlFor="del-doc-type" className="text-[10px] text-slate-400 font-semibold uppercase">Document Type</label>
                    <select 
                      id="del-doc-type"
                      value={delDocType} 
                      onChange={(e) => setDelDocType(e.target.value)}
                      className="w-full rounded border border-slate-200 px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none"
                    >
                      <option value="REPORT">REPORT (patient_reports)</option>
                      <option value="MEDICAL_ARTICLE">MEDICAL_ARTICLE (medical_knowledge)</option>
                      <option value="DRUG_DATASET">DRUG_DATASET (drug_knowledge)</option>
                      <option value="DOCTOR_PROFILE">DOCTOR_PROFILE (doctor_knowledge)</option>
                      <option value="CHAT_MEMORY">CHAT_MEMORY (chat_memory)</option>
                    </select>
                  </div>
                  <Button 
                    onClick={handleDeleteDoc}
                    disabled={!delDocId.trim() || deleteDocMutation.isPending}
                    variant="destructive"
                    className="w-full font-semibold text-xs mt-1"
                  >
                    {deleteDocMutation.isPending ? (
                      <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                    ) : (
                      <Trash2 className="h-3.5 w-3.5 mr-1" />
                    )}
                    Purge Document Vectors
                  </Button>
                </div>
              </div>

              {/* Delete Patient reports */}
              <div className="space-y-2 pb-2">
                <h4 className="text-xs font-bold text-slate-700 uppercase">Patient Reports Purge</h4>
                <div className="space-y-1">
                  <label htmlFor="del-patient-id" className="text-[10px] text-slate-400 font-semibold uppercase">Patient ID</label>
                  <input 
                    id="del-patient-id"
                    type="text" 
                    placeholder="e.g. pat_abc"
                    value={delPatientId} 
                    onChange={(e) => setDelPatientId(e.target.value)}
                    className="w-full rounded border border-slate-200 px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-teal-500"
                  />
                </div>
                <Button 
                  onClick={handleDeletePatientDocs}
                  disabled={!delPatientId.trim() || deletePatientMutation.isPending}
                  variant="destructive"
                  className="w-full font-semibold text-xs mt-1"
                >
                  {deletePatientMutation.isPending ? (
                    <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                  ) : (
                    <Trash2 className="h-3.5 w-3.5 mr-1" />
                  )}
                  Purge Patient Reports Chunks
                </Button>
              </div>

              {/* Deletion output status info */}
              {deletionResult && (
                <div className="p-3 bg-slate-50 border border-slate-200 rounded font-mono text-[10px] text-slate-600 whitespace-pre-wrap leading-tight shadow-inner">
                  {deletionResult}
                </div>
              )}

            </CardContent>
          </Card>

          <Card className="border-slate-200 shadow-md bg-white">
            <CardHeader className="border-b border-slate-100 bg-slate-50/50">
              <CardTitle className="text-sm font-bold text-slate-800">Qdrant Collections Specs Mapping</CardTitle>
            </CardHeader>
            <CardContent className="pt-4 text-xs space-y-3">
              <p className="text-slate-500 leading-normal text-[11px]">
                Nura uses exact collection schemas targeting distinct domains. MongoDB remains the single System of Record. Vector configurations are synced dynamically:
              </p>
              <div className="space-y-1 font-mono text-[10px]">
                <div className="flex justify-between border-b border-slate-100 pb-1">
                  <span className="text-slate-400">Reports</span>
                  <span className="text-slate-700 font-bold">patient_reports</span>
                </div>
                <div className="flex justify-between border-b border-slate-100 pb-1">
                  <span className="text-slate-400">Knowledge Base</span>
                  <span className="text-slate-700 font-bold">medical_knowledge</span>
                </div>
                <div className="flex justify-between border-b border-slate-100 pb-1">
                  <span className="text-slate-400">Drugs Dataset</span>
                  <span className="text-slate-700 font-bold">drug_knowledge</span>
                </div>
                <div className="flex justify-between border-b border-slate-100 pb-1">
                  <span className="text-slate-400">Doctors</span>
                  <span className="text-slate-700 font-bold">doctor_knowledge</span>
                </div>
                <div className="flex justify-between pb-1">
                  <span className="text-slate-400">Chat History</span>
                  <span className="text-slate-700 font-bold">chat_memory</span>
                </div>
              </div>
            </CardContent>
          </Card>
          
        </div>

      </div>

    </div>
  )
}

function RetrievalHealthBadge() {
  const { 
    data: stats, 
    isLoading: isStatsLoading, 
    isError: isStatsError,
    refetch: refetchStats
  } = useRetrievalStatisticsRaw()

  return (
    <Card className="shadow-sm border-slate-200 bg-white px-4 py-2 flex items-center gap-3">
      <div className="flex flex-col">
        <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Retrieval Queries</span>
        {isStatsLoading ? (
          <span className="text-sm font-medium text-slate-500 flex items-center gap-1.5 mt-0.5">
            <RefreshCw className="h-3 w-3 animate-spin" />
            Loading...
          </span>
        ) : isStatsError ? (
          <span className="text-sm font-medium text-red-500 flex items-center gap-1.5 mt-0.5">
            <AlertTriangle className="h-4 w-4" />
            Error Loading
          </span>
        ) : (
          <span className="text-sm font-medium text-teal-600 flex items-center gap-1.5 mt-0.5">
            <Activity className="h-4 w-4 text-teal-500" />
            {stats?.searches_executed || 0} Executed
          </span>
        )}
      </div>
      <Button 
        variant="ghost" 
        size="icon" 
        onClick={() => refetchStats()} 
        disabled={isStatsLoading}
        className="h-8 w-8 text-slate-400 hover:text-slate-600"
      >
        <RefreshCw className={`h-4 w-4 ${isStatsLoading ? 'animate-spin' : ''}`} />
      </Button>
    </Card>
  )
}

function RetrievalPlaygroundView() {
  const { data: stats, isLoading: isStatsLoading, refetch: refetchStats } = useRetrievalStatisticsRaw()
  const retrieveMutation = useRetrievalMulti()

  const [query, setQuery] = useState('')
  const [selectedCollections, setSelectedCollections] = useState<string[]>(['patient_reports'])
  const [topK, setTopK] = useState(5)
  const [scoreThreshold, setScoreThreshold] = useState(0.5)

  // Dynamic filter state
  const [filterKey, setFilterKey] = useState('')
  const [filterValue, setFilterValue] = useState('')
  const [filters, setFilters] = useState<Record<string, any>>({})

  const [searchResult, setSearchResult] = useState<any>(null)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [showMetadataId, setShowMetadataId] = useState<string | null>(null)

  const handleAddFilter = () => {
    if (!filterKey.trim() || !filterValue.trim()) return
    setFilters(prev => ({
      ...prev,
      [filterKey.trim()]: filterValue.trim()
    }))
    setFilterKey('')
    setFilterValue('')
  }

  const handleRemoveFilter = (key: string) => {
    setFilters(prev => {
      const copy = { ...prev }
      delete copy[key]
      return copy
    })
  }

  const handleRunSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim() || selectedCollections.length === 0) return

    setSearchResult(null)
    const payload = {
      query: query.trim(),
      collections: selectedCollections,
      top_k: topK,
      score_threshold: scoreThreshold > 0 ? scoreThreshold : undefined,
      filters: Object.keys(filters).length > 0 ? filters : undefined
    }

    try {
      const res = await retrieveMutation.mutateAsync(payload)
      setSearchResult(res)
      refetchStats()
    } catch (err: any) {
      setSearchResult({ success: false, error: err.message || 'Retrieval query execution failed' })
    }
  }

  const toggleCollection = (colName: string) => {
    setSelectedCollections(prev => 
      prev.includes(colName)
        ? prev.filter(c => c !== colName)
        : [...prev, colName]
    )
  }

  const highlightText = (text: string, queryStr: string) => {
    if (!queryStr.trim()) return text
    const escaped = queryStr.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&')
    const parts = text.split(new RegExp(`(${escaped})`, 'gi'))
    return (
      <>
        {parts.map((part, i) => 
          part.toLowerCase() === queryStr.toLowerCase()
            ? <mark key={i} className="bg-yellow-200 text-slate-900 px-0.5 rounded font-medium">{part}</mark>
            : part
        )}
      </>
    )
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Telemetry Metrics Deck */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card className="border-slate-200 shadow bg-white">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Searches Executed</p>
              <h3 className="text-2xl font-bold text-slate-800 mt-1">
                {isStatsLoading ? '...' : stats?.searches_executed ?? 0}
              </h3>
            </div>
            <div className="p-2.5 rounded-full bg-teal-50 text-teal-600">
              <Search className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow bg-white">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Average Latency</p>
              <h3 className="text-2xl font-bold text-slate-800 mt-1">
                {isStatsLoading ? '...' : `${(stats?.avg_latency_ms ?? 0).toFixed(1)} ms`}
              </h3>
            </div>
            <div className="p-2.5 rounded-full bg-blue-50 text-blue-600">
              <Clock className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow bg-white">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Average Match Score</p>
              <h3 className="text-2xl font-bold text-slate-800 mt-1">
                {isStatsLoading ? '...' : `${((stats?.avg_score ?? 0) * 100).toFixed(1)}%`}
              </h3>
            </div>
            <div className="p-2.5 rounded-full bg-indigo-50 text-indigo-600">
              <Zap className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow bg-white">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Duplicates Removed</p>
              <h3 className="text-2xl font-bold text-slate-800 mt-1">
                {isStatsLoading ? '...' : stats?.duplicate_chunks_removed ?? 0}
              </h3>
            </div>
            <div className="p-2.5 rounded-full bg-amber-50 text-amber-600">
              <Layers className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow bg-white">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Failed & Timeouts</p>
              <h3 className="text-2xl font-bold text-slate-800 mt-1">
                {isStatsLoading ? '...' : `${stats?.failed_searches ?? 0} / ${stats?.timeout_count ?? 0}`}
              </h3>
            </div>
            <div className="p-2.5 rounded-full bg-red-50 text-red-600">
              <AlertTriangle className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Console Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Search & Configurations */}
        <div className="lg:col-span-1 space-y-6">
          <Card className="border-slate-200 shadow-md bg-white">
            <CardHeader className="border-b border-slate-100 bg-slate-50/50 py-4">
              <CardTitle className="text-base font-semibold text-slate-800 flex items-center gap-2">
                <Sliders className="h-4.5 w-4.5 text-slate-500" />
                Query Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6 space-y-5">
              <form onSubmit={handleRunSearch} className="space-y-4">
                <div className="space-y-2">
                  <label htmlFor="retrieval-query" className="text-sm font-semibold text-slate-700">
                    Search Phrase
                  </label>
                  <div className="relative">
                    <input
                      id="retrieval-query"
                      type="text"
                      placeholder="Enter search phrase query..."
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      disabled={retrieveMutation.isPending}
                      className="w-full rounded-md border border-slate-200 pl-10 pr-4 py-2 text-sm text-slate-800 focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
                    />
                    <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                  </div>
                </div>

                <div className="space-y-2.5">
                  <label className="text-sm font-semibold text-slate-700">Collections Targets</label>
                  <div className="space-y-2 rounded-lg border border-slate-100 p-3.5 bg-slate-50/50">
                    {[
                      { key: 'patient_reports', label: 'Patient Reports' },
                      { key: 'medical_knowledge', label: 'Medical Knowledge' },
                      { key: 'drug_knowledge', label: 'Drug Knowledge' },
                      { key: 'doctor_knowledge', label: 'Doctor Knowledge' },
                      { key: 'chat_memory', label: 'Chat Memory' }
                    ].map(col => (
                      <label key={col.key} className="flex items-center gap-2.5 text-sm text-slate-600 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={selectedCollections.includes(col.key)}
                          onChange={() => toggleCollection(col.key)}
                          className="h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                        />
                        {col.label}
                      </label>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <label className="font-semibold text-slate-700">Top K Chunks</label>
                    <span className="font-mono text-teal-600 font-bold">{topK} hits</span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="20"
                    value={topK}
                    onChange={(e) => setTopK(parseInt(e.target.value))}
                    className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-teal-600"
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <label className="font-semibold text-slate-700">Score Threshold</label>
                    <span className="font-mono text-teal-600 font-bold">{(scoreThreshold * 100).toFixed(0)}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={scoreThreshold}
                    onChange={(e) => setScoreThreshold(parseFloat(e.target.value))}
                    className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-teal-600"
                  />
                </div>

                {/* Metadata filters section */}
                <div className="space-y-3 pt-3 border-t border-slate-100">
                  <label className="text-sm font-semibold text-slate-700 block">Metadata Filters</label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      placeholder="Key (e.g. language)"
                      value={filterKey}
                      onChange={(e) => setFilterKey(e.target.value)}
                      className="w-1/2 rounded border border-slate-200 px-2 py-1 text-xs focus:outline-none focus:border-teal-500"
                    />
                    <input
                      type="text"
                      placeholder="Value (e.g. en)"
                      value={filterValue}
                      onChange={(e) => setFilterValue(e.target.value)}
                      className="w-1/2 rounded border border-slate-200 px-2 py-1 text-xs focus:outline-none focus:border-teal-500"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      onClick={handleAddFilter}
                      className="px-2 py-1 h-auto text-xs"
                    >
                      Add
                    </Button>
                  </div>

                  {/* Active filters badges */}
                  {Object.keys(filters).length > 0 && (
                    <div className="flex flex-wrap gap-1.5 p-2 rounded-md bg-slate-50 border border-slate-100">
                      {Object.entries(filters).map(([k, v]) => (
                        <div key={k} className="flex items-center gap-1 bg-white border border-slate-200 px-1.5 py-0.5 rounded text-[10px] text-slate-600 font-medium">
                          <span>{k}: <strong className="text-slate-800">{v}</strong></span>
                          <button
                            type="button"
                            onClick={() => handleRemoveFilter(k)}
                            className="text-red-400 hover:text-red-600 text-xs font-bold"
                          >
                            ×
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <Button
                  type="submit"
                  disabled={!query.trim() || selectedCollections.length === 0 || retrieveMutation.isPending}
                  className="w-full bg-teal-600 hover:bg-teal-700 text-white font-semibold py-2.5 transition-all mt-4"
                >
                  {retrieveMutation.isPending ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Retrieving Chunks...
                    </>
                  ) : (
                    <>
                      <Search className="h-4 w-4 mr-2" />
                      Execute Retrieval
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Search Results */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="border-slate-200 shadow-md bg-white min-h-[400px] flex flex-col overflow-hidden">
            <CardHeader className="border-b border-slate-100 bg-slate-50/50 py-4">
              <CardTitle className="text-base font-semibold text-slate-800 flex items-center justify-between">
                <span>Semantic Matches</span>
                {searchResult && !searchResult.error && (
                  <span className="text-xs text-slate-400 font-normal">
                    Fetched {searchResult.results.length} ranked hits in {(searchResult.retrieval_time).toFixed(1)} ms
                  </span>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 p-6 flex flex-col justify-between">
              {retrieveMutation.isPending ? (
                <div className="flex-1 flex flex-col items-center justify-center py-20 text-slate-400 gap-3">
                  <RefreshCw className="h-8 w-8 animate-spin text-teal-500" />
                  <p className="text-sm font-medium animate-pulse text-slate-500">Querying collections in parallel...</p>
                </div>
              ) : !searchResult ? (
                <div className="flex-1 flex flex-col items-center justify-center py-20 text-slate-400 text-center">
                  <Search className="h-12 w-12 text-slate-200 mb-3" />
                  <p className="text-sm font-medium text-slate-500">Retrieval Playground Ready</p>
                  <p className="text-xs text-slate-400 mt-1 max-w-[300px]">
                    Enter a search phrase and configure collection scopes to trigger semantic lookup testing.
                  </p>
                </div>
              ) : searchResult.error ? (
                <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 flex items-start gap-3">
                  <AlertTriangle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold">Retrieval Execution Failed</h4>
                    <p className="text-sm mt-1 text-red-600">{searchResult.error}</p>
                  </div>
                </div>
              ) : searchResult.results.length === 0 ? (
                <div className="flex-1 flex flex-col items-center justify-center py-20 text-slate-400 text-center">
                  <Activity className="h-12 w-12 text-slate-200 mb-3" />
                  <p className="text-sm font-medium text-slate-500">No matching chunks found</p>
                  <p className="text-xs text-slate-400 mt-1 max-w-[300px]">
                    Try adjusting the similarity score threshold slider down or search for a different phrase.
                  </p>
                </div>
              ) : (
                <div className="space-y-6">
                  {searchResult.results.map((hit: any, index: number) => {
                    const colColors: Record<string, string> = {
                      patient_reports: 'border-teal-200 bg-teal-50 text-teal-800',
                      medical_knowledge: 'border-indigo-200 bg-indigo-50 text-indigo-800',
                      drug_knowledge: 'border-violet-200 bg-violet-50 text-violet-800',
                      doctor_knowledge: 'border-blue-200 bg-blue-50 text-blue-800',
                      chat_memory: 'border-amber-200 bg-amber-50 text-amber-800'
                    }
                    const colClass = colColors[hit.collection] || 'border-slate-200 bg-slate-50 text-slate-800'

                    return (
                      <div key={hit.id} className="border border-slate-200 rounded-lg overflow-hidden shadow-sm hover:shadow transition-all bg-white">
                        {/* Hit Header */}
                        <div className="border-b border-slate-100 bg-slate-50/50 px-4 py-3 flex items-center justify-between text-xs">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-900 bg-slate-200 px-1.5 py-0.5 rounded text-[10px]">
                              Rank #{index + 1}
                            </span>
                            <span className={`px-2 py-0.5 rounded-full font-semibold border text-[10px] ${colClass}`}>
                              {hit.collection}
                            </span>
                            {hit.document_type && (
                              <span className="text-slate-400 font-medium font-mono text-[10px]">
                                {hit.document_type}
                              </span>
                            )}
                          </div>
                          
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-teal-600 bg-teal-50 px-2 py-0.5 rounded">
                              Score: {(hit.score * 100).toFixed(1)}%
                            </span>
                            
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => {
                                navigator.clipboard.writeText(JSON.stringify(hit, null, 2))
                                setCopiedId(hit.id)
                                setTimeout(() => setCopiedId(null), 2000)
                              }}
                              className="h-6 w-6 text-slate-400 hover:text-slate-600"
                            >
                              {copiedId === hit.id ? (
                                <Check className="h-3.5 w-3.5 text-teal-600" />
                              ) : (
                                <Copy className="h-3.5 w-3.5" />
                              )}
                            </Button>
                          </div>
                        </div>

                        {/* Content text */}
                        <div className="p-4 text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                          {highlightText(hit.content, query)}
                        </div>

                        {/* Citations Footer */}
                        <div className="bg-slate-50/50 border-t border-slate-100 px-4 py-2.5 flex items-center justify-between text-xs">
                          <div className="text-slate-400 flex items-center gap-4">
                            {hit.citations.page_number && (
                              <span>Page: <strong className="text-slate-600">{hit.citations.page_number}</strong></span>
                            )}
                            {hit.citations.section && (
                              <span>Section: <strong className="text-slate-600">{hit.citations.section}</strong></span>
                            )}
                            {hit.citations.document_id && (
                              <span>Doc ID: <strong className="text-slate-500 font-mono">{hit.citations.document_id}</strong></span>
                            )}
                          </div>

                          <Button
                            variant="ghost"
                            onClick={() => setShowMetadataId(showMetadataId === hit.id ? null : hit.id)}
                            className="text-teal-600 hover:text-teal-700 font-semibold text-xs h-auto p-0 flex items-center gap-1"
                          >
                            <Code className="h-3.5 w-3.5" />
                            {showMetadataId === hit.id ? 'Hide Headers' : 'View Payload'}
                          </Button>
                        </div>

                        {/* Metadata payload details */}
                        {showMetadataId === hit.id && (
                          <div className="border-t border-slate-100 bg-slate-900 p-4 overflow-x-auto text-[11px]">
                            <pre className="font-mono text-teal-400">{JSON.stringify(hit.metadata, null, 2)}</pre>
                          </div>
                        )}
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

function ContextBuilderHealthBadge() {
  const { data: stats, isLoading } = useContextAssemblyStatistics()

  return (
    <Card className="shadow-sm border-slate-200 bg-white px-4 py-2 flex items-center gap-3">
      <div className="flex flex-col">
        <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Assemblies Executed</span>
        {isLoading ? (
          <span className="text-sm font-medium text-slate-500 flex items-center gap-1.5 mt-0.5">
            <RefreshCw className="h-3 w-3 animate-spin" />
            Loading...
          </span>
        ) : (
          <span className="text-sm font-bold text-teal-600 flex items-center gap-1.5 mt-0.5">
            <Layers className="h-4 w-4 text-teal-500 animate-pulse" />
            {stats?.assemblies_executed || 0} runs
          </span>
        )}
      </div>
    </Card>
  )
}

function ContextBuilderPlaygroundView() {
  const [query, setQuery] = useState('')
  const [selectedPatientId, setSelectedPatientId] = useState('')
  const [selectedPatientName, setSelectedPatientName] = useState('')
  const [patientSearch, setPatientSearch] = useState('')
  const [tokenBudget, setTokenBudget] = useState<number>(4000)
  const [collections, setCollections] = useState<string[]>([
    'patient_reports',
    'chat_memory',
    'medical_knowledge',
    'drug_knowledge',
    'doctor_knowledge'
  ])
  const [testResult, setTestResult] = useState<any>(null)
  const [latency, setLatency] = useState<number | null>(null)
  const [copiedPrompt, setCopiedPrompt] = useState(false)
  const [copiedJSON, setCopiedJSON] = useState(false)
  const [activeSubTab, setActiveSubTab] = useState<'preview' | 'json'>('preview')
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    'PATIENT SUMMARY': true,
    'CURRENT CONDITION': true,
    'REPORT FINDINGS': true,
    'CONSULTATION HISTORY': true,
    'PRESCRIPTIONS': true,
    'MEDICAL KNOWLEDGE': true,
    'DRUG KNOWLEDGE': true,
    'DOCTOR INFORMATION': true,
    'CHAT MEMORY': true
  })

  // Fetch patients list
  const { data: patientsResponse, isLoading: isLoadingPatients, isError: isPatientsError } = useQuery({
    queryKey: ['admin', 'patients-list'],
    queryFn: () => adminUserService.listUsers(undefined, 'patient')
  })
  const patients = patientsResponse?.data || []

  // Filter patients list based on search term
  const filteredPatients = patients.filter((p: any) =>
    p.full_name?.toLowerCase().includes(patientSearch.toLowerCase()) ||
    p.email?.toLowerCase().includes(patientSearch.toLowerCase())
  )

  const buildMutation = useBuildContext()

  const handleBuild = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    const startTime = performance.now()
    try {
      const result = await buildMutation.mutateAsync({
        query: query,
        patient_id: selectedPatientId || undefined,
        token_budget: tokenBudget,
        collections: collections
      })
      const endTime = performance.now()
      setLatency(endTime - startTime)
      setTestResult(result)
    } catch (err) {
      setTestResult(null)
      setLatency(null)
    }
  }

  const getRawPromptText = () => {
    if (!testResult?.sections) return ''
    return Object.entries(testResult.sections)
      .map(([header, content]) => `=== ${header} ===\n${content}`)
      .join('\n\n')
  }

  const handleCopyPrompt = () => {
    if (!testResult) return
    navigator.clipboard.writeText(getRawPromptText())
    setCopiedPrompt(true)
    setTimeout(() => setCopiedPrompt(false), 2000)
  }

  const handleCopyJSON = () => {
    if (!testResult) return
    navigator.clipboard.writeText(JSON.stringify(testResult, null, 2))
    setCopiedJSON(true)
    setTimeout(() => setCopiedJSON(false), 2000)
  }

  const handleDownload = () => {
    const text = getRawPromptText()
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `context_build_${selectedPatientId || 'anonymous'}.txt`
    link.click()
    URL.revokeObjectURL(url)
  }

  const toggleCollection = (colName: string) => {
    if (collections.includes(colName)) {
      setCollections(collections.filter(c => c !== colName))
    } else {
      setCollections([...collections, colName])
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in duration-300">
      {/* Selector and Config Column (col-span-1) */}
      <div className="space-y-6">
        <Card className="border-slate-200 shadow-md bg-white">
          <CardHeader className="border-b border-slate-100 bg-slate-50/50">
            <CardTitle className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <Sliders className="h-5 w-5 text-slate-500" />
              Console Parameters
            </CardTitle>
            <CardDescription>
              Configure patient context and vector retrieval params for assembly.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-6 space-y-4">
            {/* Query Phrase */}
            <div className="space-y-1.5">
              <label htmlFor="query-text" className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Retrieval Query
              </label>
              <Textarea
                id="query-text"
                placeholder="Enter query to retrieve matching document chunks (e.g. chronic hypertension)..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                rows={2}
                className="border-slate-200 focus:border-teal-500 focus:ring-teal-500 text-sm font-sans"
              />
            </div>

            {/* Patient Select search */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Patient Select
              </label>
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search patient name/email..."
                  value={patientSearch}
                  onChange={(e) => setPatientSearch(e.target.value)}
                  className="w-full rounded-md border border-slate-200 pl-8 pr-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
                />
              </div>

              {isLoadingPatients ? (
                <div className="flex items-center justify-center py-4 text-slate-400 gap-1.5 text-xs">
                  <RefreshCw className="h-3 w-3 animate-spin text-teal-500" />
                  <span>Loading patients...</span>
                </div>
              ) : isPatientsError ? (
                <div className="text-center py-2 text-rose-500 text-xs">
                  Failed to fetch patients list.
                </div>
              ) : filteredPatients.length === 0 ? (
                <div className="text-center py-2 text-slate-500 text-xs">
                  No patients match.
                </div>
              ) : (
                <div className="max-h-36 overflow-y-auto border border-slate-100 rounded-md divide-y divide-slate-100 text-xs bg-slate-50/30">
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedPatientId('')
                      setSelectedPatientName('')
                    }}
                    className={`w-full text-left px-2.5 py-2 transition-colors flex items-center justify-between ${
                      selectedPatientId === ''
                        ? 'bg-teal-50 font-bold text-teal-700'
                        : 'hover:bg-slate-50 text-slate-600'
                    }`}
                  >
                    <span>No Patient (Null Context)</span>
                    {selectedPatientId === '' && (
                      <CheckCircle2 className="h-3.5 w-3.5 text-teal-600" />
                    )}
                  </button>
                  {filteredPatients.map((patient: any) => (
                    <button
                      key={patient.id}
                      type="button"
                      onClick={() => {
                        setSelectedPatientId(patient.id)
                        setSelectedPatientName(patient.full_name)
                      }}
                      className={`w-full text-left px-2.5 py-2 transition-colors flex items-center justify-between ${
                        selectedPatientId === patient.id
                          ? 'bg-teal-50 font-bold text-teal-700'
                          : 'hover:bg-slate-50 text-slate-600'
                      }`}
                    >
                      <div className="truncate">
                        <span className="font-semibold">{patient.full_name}</span>{' '}
                        <span className="text-[10px] text-slate-400 font-mono">({patient.email})</span>
                      </div>
                      {selectedPatientId === patient.id && (
                        <CheckCircle2 className="h-3.5 w-3.5 text-teal-600" />
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Token Budget Slider */}
            <div className="space-y-1.5">
              <div className="flex justify-between items-center text-xs font-bold text-slate-500 uppercase tracking-wider">
                <span>Token Budget</span>
                <span className="text-teal-600 font-bold text-xs">{tokenBudget} tokens</span>
              </div>
              <input
                type="range"
                min="500"
                max="8000"
                step="500"
                value={tokenBudget}
                onChange={(e) => setTokenBudget(parseInt(e.target.value))}
                className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-teal-600"
              />
              <div className="flex justify-between text-[10px] text-slate-400">
                <span>500</span>
                <span>4000</span>
                <span>8000</span>
              </div>
            </div>

            {/* Collections scopes */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block">
                Target Collections
              </label>
              <div className="space-y-1.5 bg-slate-50 border border-slate-100 p-3 rounded-md text-xs text-slate-600 font-medium">
                {[
                  { name: 'patient_reports', label: 'Patient Reports (REPORT)' },
                  { name: 'chat_memory', label: 'Chat Memory (CHAT_MEMORY)' },
                  { name: 'medical_knowledge', label: 'Medical Knowledge (MEDICAL_ARTICLE)' },
                  { name: 'drug_knowledge', label: 'Drug Knowledge (DRUG_DATASET)' },
                  { name: 'doctor_knowledge', label: 'Doctor Knowledge (DOCTOR_PROFILE)' }
                ].map((col) => (
                  <label key={col.name} className="flex items-center gap-2 cursor-pointer hover:text-slate-800 transition-colors">
                    <input
                      type="checkbox"
                      checked={collections.includes(col.name)}
                      onChange={() => toggleCollection(col.name)}
                      className="rounded border-slate-300 text-teal-600 focus:ring-teal-500 h-3.5 w-3.5"
                    />
                    <span>{col.label}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Run Button */}
            <Button
              onClick={handleBuild}
              disabled={!query.trim() || buildMutation.isPending}
              className="w-full bg-teal-600 hover:bg-teal-700 text-white font-semibold transition-all"
            >
              {buildMutation.isPending ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Building Context...
                </>
              ) : (
                <>
                  <Zap className="h-4 w-4 mr-2" />
                  Run Context Build
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Results Display Column (col-span-2) */}
      <div className="lg:col-span-2 space-y-6">
        {/* Loading and error states */}
        {buildMutation.isPending && (
          <Card className="border-slate-200 shadow-md bg-white">
            <CardContent className="py-12 flex flex-col items-center justify-center text-slate-400 gap-3">
              <RefreshCw className="h-8 w-8 animate-spin text-teal-500" />
              <p className="text-sm font-medium animate-pulse text-slate-500">Querying and ranking context...</p>
            </CardContent>
          </Card>
        )}

        {buildMutation.isError && (
          <Card className="border-slate-200 shadow-md bg-white">
            <CardContent className="pt-6">
              <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="font-semibold">Context Build Failed</h4>
                  <p className="text-sm mt-1 text-red-600">
                    {buildMutation.error?.message || 'An unexpected error occurred during context assembly.'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {!testResult && !buildMutation.isPending && !buildMutation.isError && (
          <Card className="border-slate-200 border-dashed border-2 bg-slate-50/50 p-12 text-center">
            <div className="mx-auto h-12 w-12 text-slate-400 flex items-center justify-center bg-white rounded-full border border-slate-200 shadow-sm mb-4">
              <Layers className="h-6 w-6 animate-pulse" />
            </div>
            <h3 className="text-sm font-bold text-slate-700">No Context Built</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto mt-2">
              Submit a retrieval query phrase, select optional patient context, and execute to see how the platform dynamically ranks and budgets prompt overlays.
            </p>
          </Card>
        )}

        {testResult && !buildMutation.isPending && (
          <div className="space-y-6 animate-in fade-in duration-300">
            {/* Telemetry Row */}
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
              {/* Estimated tokens */}
              <Card className="border-slate-200 shadow bg-gradient-to-br from-teal-50 to-white">
                <CardContent className="p-4 flex items-center justify-between">
                  <div>
                    <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Assembled Size</p>
                    <h3 className="text-2xl font-extrabold text-teal-900 mt-1">
                      {testResult.estimated_tokens} <span className="text-xs font-semibold text-teal-600">tokens</span>
                    </h3>
                  </div>
                </CardContent>
              </Card>

              {/* Latency */}
              <Card className="border-slate-200 shadow bg-gradient-to-br from-blue-50 to-white">
                <CardContent className="p-4 flex items-center justify-between">
                  <div>
                    <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Latency</p>
                    <h3 className="text-2xl font-extrabold text-blue-900 mt-1">
                      {testResult.assembly_time.toFixed(1)} <span className="text-xs font-semibold text-blue-600">ms</span>
                    </h3>
                  </div>
                </CardContent>
              </Card>

              {/* Compression Ratio */}
              <Card className="border-slate-200 shadow bg-gradient-to-br from-indigo-50 to-white">
                <CardContent className="p-4 flex items-center justify-between">
                  <div>
                    <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Compression</p>
                    <h3 className="text-2xl font-extrabold text-indigo-900 mt-1">
                      {(testResult.compression_ratio * 100).toFixed(0)}<span className="text-xs font-semibold text-indigo-600">%</span>
                    </h3>
                  </div>
                </CardContent>
              </Card>

              {/* Removed chunks / Citations */}
              <Card className="border-slate-200 shadow bg-gradient-to-br from-slate-50 to-white">
                <CardContent className="p-4 flex items-center justify-between">
                  <div>
                    <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Pruned / Citations</p>
                    <h3 className="text-xl font-bold text-slate-800 mt-1.5">
                      {testResult.metadata?.removed_chunks || 0} / {Object.keys(testResult.citations).length}
                    </h3>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Sections Accordion View */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wider">Collapsible Sections</h3>
              {Object.keys(testResult.sections).length === 0 ? (
                <p className="text-xs text-slate-500 bg-slate-50 border border-slate-100 p-4 rounded text-center">No sections compiled (all empty or omitted).</p>
              ) : (
                Object.entries(testResult.sections).map(([sectionName, sectionText]: any) => (
                  <div key={sectionName} className="border border-slate-200 rounded-lg bg-white overflow-hidden shadow-sm hover:border-slate-300/80 transition-colors">
                    <button
                      onClick={() => setOpenSections(prev => ({ ...prev, [sectionName]: !prev[sectionName] }))}
                      className="w-full flex items-center justify-between px-4 py-2.5 bg-slate-50/50 border-b border-slate-100 hover:bg-slate-100/30 transition-colors text-left"
                    >
                      <span className="text-xs font-bold text-slate-700 tracking-wide uppercase">{sectionName}</span>
                      <span className="text-xs text-slate-400 font-mono">
                        {openSections[sectionName] ? 'Collapse' : 'Expand'}
                      </span>
                    </button>
                    {openSections[sectionName] && (
                      <div className="p-4 text-xs text-slate-800 leading-relaxed whitespace-pre-wrap font-sans bg-white/50">
                        {sectionText}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>

            {/* Citations inspector */}
            {Object.keys(testResult.citations).length > 0 && (
              <Card className="border-slate-200 shadow-md bg-white overflow-hidden">
                <CardHeader className="border-b border-slate-100 bg-slate-50/50 py-3">
                  <CardTitle className="text-xs font-bold text-slate-700 uppercase tracking-wider">Citation Inspector</CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="overflow-x-auto">
                    <table className="w-full text-[11px] text-left border-collapse">
                      <thead>
                        <tr className="bg-slate-50 border-b border-slate-100 text-slate-500 font-semibold uppercase tracking-wider">
                          <th className="px-4 py-2">ID</th>
                          <th className="px-4 py-2">Collection</th>
                          <th className="px-4 py-2">Doc ID</th>
                          <th className="px-4 py-2">Chunk ID</th>
                          <th className="px-4 py-2">Page</th>
                          <th className="px-4 py-2">Cosine Score</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 text-slate-600 font-medium font-mono">
                        {Object.entries(testResult.citations).map(([citId, info]: any) => (
                          <tr key={citId} className="hover:bg-slate-50/50 transition-colors">
                            <td className="px-4 py-2 font-bold text-teal-600 font-sans">[{citId}]</td>
                            <td className="px-4 py-2">{info.collection}</td>
                            <td className="px-4 py-2 truncate max-w-[100px]" title={info.document_id}>{info.document_id || 'N/A'}</td>
                            <td className="px-4 py-2 truncate max-w-[100px]" title={info.chunk_id}>{info.chunk_id || 'N/A'}</td>
                            <td className="px-4 py-2 font-sans">{info.page_number}</td>
                            <td className="px-4 py-2 font-sans">
                              <span className="font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded-full border border-teal-100">
                                {info.score.toFixed(4)}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Raw Prompt Preview */}
            <Card className="border-slate-200 shadow-md bg-white overflow-hidden">
              <CardHeader className="border-b border-slate-100 bg-slate-50/50 flex flex-row items-center justify-between py-3">
                <div>
                  <CardTitle className="text-xs font-bold text-slate-700 uppercase tracking-wider">Raw Prompt Preview</CardTitle>
                </div>
                <div className="flex gap-2">
                  <div className="bg-slate-100 border border-slate-200 p-0.5 rounded flex text-xs">
                    <button
                      onClick={() => setActiveSubTab('preview')}
                      className={`px-2.5 py-1 rounded font-medium transition-all ${
                        activeSubTab === 'preview'
                          ? 'bg-white shadow-sm text-slate-800 font-bold'
                          : 'text-slate-500 hover:text-slate-700'
                      }`}
                    >
                      Text
                    </button>
                    <button
                      onClick={() => setActiveSubTab('json')}
                      className={`px-2.5 py-1 rounded font-medium transition-all ${
                        activeSubTab === 'json'
                          ? 'bg-white shadow-sm text-slate-800 font-bold'
                          : 'text-slate-500 hover:text-slate-700'
                      }`}
                    >
                      JSON
                    </button>
                  </div>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={activeSubTab === 'preview' ? handleCopyPrompt : handleCopyJSON}
                    className="h-8 gap-1.5 text-xs"
                  >
                    {copiedPrompt || copiedJSON ? (
                      <>
                        <Check className="h-3.5 w-3.5 text-teal-600" />
                        Copied
                      </>
                    ) : (
                      <>
                        <Copy className="h-3.5 w-3.5" />
                        Copy
                      </>
                    )}
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleDownload}
                    className="h-8 gap-1.5 text-xs"
                  >
                    Download
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                {activeSubTab === 'json' ? (
                  <pre className="p-5 font-mono text-[11px] text-teal-400 bg-slate-900 shadow-inner overflow-x-auto max-h-[400px] overflow-y-auto">
                    {JSON.stringify(testResult, null, 2)}
                  </pre>
                ) : (
                  <pre className="p-5 font-mono text-[11px] text-slate-300 bg-slate-900 shadow-inner overflow-x-auto max-h-[400px] overflow-y-auto whitespace-pre-wrap leading-relaxed">
                    {getRawPromptText()}
                  </pre>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}

function RetrievalAgentHealthBadge() {
  const { data: stats, isLoading } = useRetrievalStatistics()

  return (
    <Card className="shadow-sm border-slate-200 bg-white px-4 py-2 flex items-center gap-3">
      <div className="flex flex-col">
        <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Cache Hit Ratio</span>
        {isLoading ? (
          <span className="text-sm font-medium text-slate-500 flex items-center gap-1.5 mt-0.5">
            <RefreshCw className="h-3 w-3 animate-spin" />
            Checking...
          </span>
        ) : (
          <span className="text-sm font-bold text-teal-600 flex items-center gap-1.5 mt-0.5">
            <Zap className="h-4 w-4 text-teal-500 animate-pulse" />
            {((stats?.cache_hit_ratio || 0) * 100).toFixed(0)}% Hit Rate
          </span>
        )}
      </div>
    </Card>
  )
}

function RetrievalAgentPlaygroundView() {
  const { data: stats, isLoading: isStatsLoading, refetch: refetchStats } = useRetrievalStatistics()
  const agentMutation = useRetrievalAgent()
  const debugMutation = useRetrievalAgentDebug()

  const [query, setQuery] = useState('')
  const [selectedPatientId, setSelectedPatientId] = useState('')
  const [patientSearch, setPatientSearch] = useState('')
  const [forcedIntent, setForcedIntent] = useState<string>('auto')
  const [tokenBudget, setTokenBudget] = useState<number>(4000)
  const [runMode, setRunMode] = useState<'standard' | 'debug'>('standard')

  const [result, setResult] = useState<any>(null)
  const [latency, setLatency] = useState<number | null>(null)
  const [copiedContext, setCopiedContext] = useState(false)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [showMetadataId, setShowMetadataId] = useState<string | null>(null)
  
  // Debug view active accordions
  const [debugAccordion, setDebugAccordion] = useState<Record<string, boolean>>({
    intent: true,
    retrieval: false,
    ranking: false,
    assembly: false,
    output: false
  })

  // Fetch patients list
  const { data: patientsResponse, isLoading: isLoadingPatients } = useQuery({
    queryKey: ['admin', 'patients-list'],
    queryFn: () => adminUserService.listUsers(undefined, 'patient')
  })
  const patients = patientsResponse?.data || []

  // Filter patients list based on search term
  const filteredPatients = patients.filter((p: any) =>
    p.full_name?.toLowerCase().includes(patientSearch.toLowerCase()) ||
    p.email?.toLowerCase().includes(patientSearch.toLowerCase())
  )

  const handleRunAgent = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setResult(null)
    const startTime = performance.now()
    
    const payload = {
      query: query.trim(),
      patient_id: selectedPatientId || undefined,
      intent: forcedIntent !== 'auto' ? forcedIntent : undefined,
      top_k: 5,
      score_threshold: undefined,
      filters: undefined
    }

    try {
      let res
      if (runMode === 'debug') {
        res = await debugMutation.mutateAsync(payload)
      } else {
        res = await agentMutation.mutateAsync(payload)
      }
      const endTime = performance.now()
      setLatency(endTime - startTime)
      setResult(res)
      refetchStats()
    } catch (err: any) {
      setResult({ success: false, error: err.message || 'Agent query run failed' })
      setLatency(null)
    }
  }

  const toggleDebugAccordion = (section: string) => {
    setDebugAccordion(prev => ({
      ...prev,
      [section]: !prev[section]
    }))
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Statistics Header Deck */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-slate-200 shadow bg-white">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Runs</p>
              <h3 className="text-2xl font-bold text-slate-800 mt-1">
                {isStatsLoading ? '...' : stats?.requests ?? 0}
              </h3>
            </div>
            <div className="p-2.5 rounded-full bg-teal-50 text-teal-600">
              <Zap className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow bg-white">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Average Latency</p>
              <h3 className="text-2xl font-bold text-slate-800 mt-1">
                {isStatsLoading ? '...' : `${(stats?.avg_latency_ms ?? 0).toFixed(1)} ms`}
              </h3>
            </div>
            <div className="p-2.5 rounded-full bg-blue-50 text-blue-600">
              <Clock className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow bg-white">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Cache Hits / Misses</p>
              <h3 className="text-2xl font-bold text-slate-800 mt-1">
                {isStatsLoading ? '...' : `${stats?.cache_hits ?? 0} / ${stats?.cache_misses ?? 0}`}
              </h3>
            </div>
            <div className="p-2.5 rounded-full bg-indigo-50 text-indigo-600">
              <Database className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow bg-white">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Failed Requests</p>
              <h3 className="text-2xl font-bold text-slate-800 mt-1 text-red-600">
                {isStatsLoading ? '...' : stats?.failures ?? 0}
              </h3>
            </div>
            <div className="p-2.5 rounded-full bg-red-50 text-red-600">
              <AlertTriangle className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Control Panel Column */}
        <div className="lg:col-span-1 space-y-6">
          <Card className="border-slate-200 shadow-md bg-white">
            <CardHeader className="border-b border-slate-100 bg-slate-50/50 py-4">
              <CardTitle className="text-base font-semibold text-slate-800 flex items-center gap-2">
                <Sliders className="h-4.5 w-4.5 text-slate-500" />
                Retrieval Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6 space-y-4">
              <form onSubmit={handleRunAgent} className="space-y-4">
                {/* Search Phrase Query */}
                <div className="space-y-1.5">
                  <label htmlFor="agent-query" className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                    Query Phrase
                  </label>
                  <div className="relative">
                    <input
                      id="agent-query"
                      type="text"
                      placeholder="e.g. side effects of paracetamol..."
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      required
                      className="w-full rounded-md border border-slate-200 pl-10 pr-4 py-2 text-sm text-slate-800 focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
                    />
                    <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                  </div>
                </div>

                {/* Patient Context Select */}
                <div className="space-y-1.5">
                  <label htmlFor="agent-patient" className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                    Patient Profile
                  </label>
                  <div className="space-y-2">
                    <input
                      type="text"
                      placeholder="Search patient..."
                      value={patientSearch}
                      onChange={(e) => setPatientSearch(e.target.value)}
                      className="w-full rounded-md border border-slate-200 px-3 py-1.5 text-xs focus:border-teal-500 focus:outline-none"
                    />
                    <select
                      id="agent-patient"
                      value={selectedPatientId}
                      onChange={(e) => {
                        setSelectedPatientId(e.target.value)
                      }}
                      className="w-full rounded-md border border-slate-200 px-3 py-2 text-xs bg-white focus:border-teal-500 focus:outline-none"
                    >
                      <option value="">Anonymous (No patient history context)</option>
                      {isLoadingPatients ? (
                        <option disabled>Loading patients...</option>
                      ) : (
                        filteredPatients.map((p: any) => (
                          <option key={p.id} value={p.id}>
                            {p.full_name} ({p.email})
                          </option>
                        ))
                      )}
                    </select>
                  </div>
                </div>

                {/* Intent Override Options */}
                <div className="space-y-1.5">
                  <label htmlFor="agent-intent" className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                    Retrieval Intent Override
                  </label>
                  <select
                    id="agent-intent"
                    value={forcedIntent}
                    onChange={(e) => setForcedIntent(e.target.value)}
                    className="w-full rounded-md border border-slate-200 px-3 py-2 text-xs bg-white focus:border-teal-500 focus:outline-none"
                  >
                    <option value="auto">Auto-Detect Intent (Deterministic Classifier)</option>
                    <option value="medical_question">Medical Question</option>
                    <option value="report_analysis">Report Analysis</option>
                    <option value="drug_question">Drug Question</option>
                    <option value="doctor_recommendation">Doctor Recommendation</option>
                    <option value="conversation_recall">Conversation Recall</option>
                    <option value="general_health">General Health</option>
                  </select>
                </div>

                {/* Debug vs Standard Mode Toggle */}
                <div className="space-y-1.5 pt-2 border-t border-slate-100 flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Debug Trace Mode</span>
                  <div className="flex gap-2 bg-slate-100 p-1 rounded-md">
                    <button
                      type="button"
                      onClick={() => setRunMode('standard')}
                      className={`px-3 py-1 text-xs font-medium rounded transition-all ${
                        runMode === 'standard' ? 'bg-white text-teal-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'
                      }`}
                    >
                      Standard
                    </button>
                    <button
                      type="button"
                      onClick={() => setRunMode('debug')}
                      className={`px-3 py-1 text-xs font-medium rounded transition-all ${
                        runMode === 'debug' ? 'bg-white text-teal-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'
                      }`}
                    >
                      Debug (No Cache)
                    </button>
                  </div>
                </div>

                {/* Run Query Button */}
                <Button
                  type="submit"
                  disabled={!query.trim() || agentMutation.isPending || debugMutation.isPending}
                  className="w-full bg-teal-600 hover:bg-teal-700 text-white font-semibold py-2.5 transition-all mt-4"
                >
                  {agentMutation.isPending || debugMutation.isPending ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Running Agent...
                    </>
                  ) : (
                    <>
                      <Zap className="h-4 w-4 mr-2" />
                      Run Retrieval Agent
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Collection usage distribution card */}
          {stats?.collection_usage && Object.keys(stats.collection_usage).length > 0 && (
            <Card className="border-slate-200 shadow bg-white text-xs">
              <CardHeader className="py-3.5 border-b border-slate-100">
                <CardTitle className="text-xs font-bold text-slate-500 uppercase tracking-wider">Top Searched Collections</CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-2">
                {Object.entries(stats.collection_usage)
                  .sort((a, b) => b[1] - a[1])
                  .map(([col, count]) => (
                    <div key={col} className="flex justify-between items-center text-slate-600 py-1 border-b border-slate-50/50">
                      <span className="font-mono text-slate-700">{col}</span>
                      <span className="font-bold text-teal-600 bg-teal-50 px-2 py-0.5 rounded">{count} calls</span>
                    </div>
                  ))}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right Output Panels Column */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="border-slate-200 shadow-md bg-white min-h-[450px] flex flex-col overflow-hidden">
            <CardHeader className="border-b border-slate-100 bg-slate-50/50 py-4 flex flex-row items-center justify-between">
              <CardTitle className="text-base font-semibold text-slate-800">
                Agent Output & Traces
              </CardTitle>
              {result && (
                <div className="flex items-center gap-3">
                  <span className={`px-2 py-0.5 rounded-full font-semibold border text-[10px] uppercase ${
                    result.cache_status === 'hit' ? 'bg-teal-50 border-teal-200 text-teal-800' : 'bg-amber-50 border-amber-200 text-amber-800'
                  }`}>
                    Cache: {result.cache_status}
                  </span>
                  {latency && (
                    <span className="text-xs text-slate-400 font-normal">
                      Completed in {latency.toFixed(0)} ms
                    </span>
                  )}
                </div>
              )}
            </CardHeader>
            <CardContent className="flex-1 p-6 flex flex-col justify-between">
              {agentMutation.isPending || debugMutation.isPending ? (
                <div className="flex-1 flex flex-col items-center justify-center py-20 text-slate-400 gap-3">
                  <RefreshCw className="h-8 w-8 animate-spin text-teal-500 animate-pulse" />
                  <p className="text-sm font-medium text-slate-500">Classifying query and routing vector lookups...</p>
                </div>
              ) : !result ? (
                <div className="flex-1 flex flex-col items-center justify-center py-20 text-slate-400 text-center">
                  <Zap className="h-12 w-12 text-slate-200 mb-3 animate-bounce" />
                  <p className="text-sm font-medium text-slate-500">Retrieval Agent Console Ready</p>
                  <p className="text-xs text-slate-400 mt-1 max-w-[350px]">
                    Configure query settings and click Run. The agent will determine intent, execute search on required collections, and compile token-safe context.
                  </p>
                </div>
              ) : result.error ? (
                <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 flex items-start gap-3">
                  <AlertTriangle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold">Execution Error</h4>
                    <p className="text-sm mt-1 text-red-600">{result.error}</p>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* General Results Header: Intent & Timings */}
                  <div className="p-4 bg-slate-50 rounded-lg border border-slate-100 flex flex-wrap gap-4 justify-between items-center text-sm">
                    <div className="space-y-1">
                      <span className="text-xs text-slate-400 font-semibold block uppercase">Detected Intent</span>
                      <strong className="text-teal-700 uppercase text-base">{result.intent}</strong>
                    </div>

                    <div className="flex gap-4">
                      {result.latency.retrieval && (
                        <div className="text-center">
                          <span className="text-[10px] text-slate-400 block uppercase">Search</span>
                          <span className="font-semibold text-slate-700">{result.latency.retrieval.toFixed(0)}ms</span>
                        </div>
                      )}
                      {result.latency.context && (
                        <div className="text-center">
                          <span className="text-[10px] text-slate-400 block uppercase">Assembly</span>
                          <span className="font-semibold text-slate-700">{result.latency.context.toFixed(0)}ms</span>
                        </div>
                      )}
                      {result.latency.total && (
                        <div className="text-center bg-teal-50 border border-teal-100 px-2.5 py-0.5 rounded">
                          <span className="text-[10px] text-teal-600 block uppercase font-bold">Total</span>
                          <span className="font-bold text-teal-800">{result.latency.total.toFixed(0)}ms</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Debug Mode Accordion Section */}
                  {runMode === 'debug' ? (
                    <div className="space-y-3">
                      <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Debug Execution Traces</h4>
                      
                      {/* Accordion: Intent Detection Score Matches */}
                      <div className="border border-slate-100 rounded-lg overflow-hidden bg-white">
                        <button
                          type="button"
                          onClick={() => toggleDebugAccordion('intent')}
                          className="w-full bg-slate-50 px-4 py-2.5 flex items-center justify-between text-xs font-semibold text-slate-700 hover:bg-slate-100 transition-all border-b border-slate-100"
                        >
                          <span>Step 1: Deterministic Intent Scoring</span>
                          <span className="font-mono text-teal-600">Scores</span>
                        </button>
                        {debugAccordion.intent && (
                          <div className="p-4 space-y-2 text-xs max-h-[200px] overflow-y-auto bg-slate-900 text-slate-300 font-mono">
                            {result.metadata.intent_scores && Object.entries(result.metadata.intent_scores).map(([intentName, scoreVal]: any) => (
                              <div key={intentName} className="flex justify-between">
                                <span className={intentName === result.intent ? 'text-teal-400 font-bold' : ''}>
                                  {intentName} {intentName === result.intent && '◀ Winner'}
                                </span>
                                <span className={intentName === result.intent ? 'text-teal-400 font-bold' : ''}>
                                  {scoreVal} pts
                                </span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Accordion: Raw Chunks list */}
                      <div className="border border-slate-100 rounded-lg overflow-hidden bg-white">
                        <button
                          type="button"
                          onClick={() => toggleDebugAccordion('retrieval')}
                          className="w-full bg-slate-50 px-4 py-2.5 flex items-center justify-between text-xs font-semibold text-slate-700 hover:bg-slate-100 transition-all border-b border-slate-100"
                        >
                          <span>Step 2: Raw Retrieved Vector Points ({result.retrieved_chunks.length} points)</span>
                          <span className="font-mono text-teal-600">Raw Hits</span>
                        </button>
                        {debugAccordion.retrieval && (
                          <div className="p-0 max-h-[300px] overflow-y-auto bg-slate-900 text-slate-400 text-[11px] font-mono divide-y divide-slate-800">
                            {result.retrieved_chunks.map((hit: any, i: number) => (
                              <div key={hit.id} className="p-3.5 space-y-1">
                                <div className="flex justify-between text-teal-400 text-[10px]">
                                  <span>Hit #{i + 1} | Point ID: {hit.id.slice(0, 8)}...</span>
                                  <span>Col: {hit.collection} | Score: {(hit.score * 100).toFixed(0)}%</span>
                                </div>
                                <p className="text-slate-300 whitespace-pre-wrap">{hit.content}</p>
                              </div>
                            ))}
                            {result.retrieved_chunks.length === 0 && (
                              <div className="p-4 text-center text-slate-500">No raw hits found</div>
                            )}
                          </div>
                        )}
                      </div>

                      {/* Accordion: Ranked & Deduplicated Chunks */}
                      <div className="border border-slate-100 rounded-lg overflow-hidden bg-white">
                        <button
                          type="button"
                          onClick={() => toggleDebugAccordion('ranking')}
                          className="w-full bg-slate-50 px-4 py-2.5 flex items-center justify-between text-xs font-semibold text-slate-700 hover:bg-slate-100 transition-all border-b border-slate-100"
                        >
                          <span>Step 3: Ranked Chunks & Scores mapping</span>
                          <span className="font-mono text-teal-600">Rankings</span>
                        </button>
                        {debugAccordion.ranking && (
                          <div className="p-4 space-y-2 text-xs max-h-[250px] overflow-y-auto bg-slate-900 text-slate-300 font-mono">
                            {result.scores && Object.entries(result.scores).map(([chunkId, chunkScore]: any) => (
                              <div key={chunkId} className="flex justify-between border-b border-slate-800 pb-1">
                                <span>ID: {chunkId}</span>
                                <span className="text-teal-400 font-semibold">{(chunkScore * 100).toFixed(1)}%</span>
                              </div>
                            ))}
                            {(!result.scores || Object.keys(result.scores).length === 0) && (
                              <div className="text-center text-slate-500">No chunk rankings found</div>
                            )}
                          </div>
                        )}
                      </div>

                      {/* Accordion: Final Context Assembly */}
                      <div className="border border-slate-100 rounded-lg overflow-hidden bg-white">
                        <button
                          type="button"
                          onClick={() => toggleDebugAccordion('assembly')}
                          className="w-full bg-slate-50 px-4 py-2.5 flex items-center justify-between text-xs font-semibold text-slate-700 hover:bg-slate-100 transition-all border-b border-slate-100"
                        >
                          <span>Step 4: Assembled Raw Context Prompt ({result.metadata.estimated_tokens} tokens)</span>
                          <span className="font-mono text-teal-600">Prompt</span>
                        </button>
                        {debugAccordion.assembly && (
                          <div className="p-0 bg-slate-900 border border-slate-950 overflow-x-auto max-h-[350px] overflow-y-auto shadow-inner">
                            <pre className="p-5 font-mono text-[11px] text-slate-300 whitespace-pre-wrap leading-relaxed">
                              {result.context || 'Context is empty'}
                            </pre>
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    // Standard Mode Output Views
                    <div className="space-y-4">
                      {/* Context Prompt Text area */}
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Assembled Context Preview</h4>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              navigator.clipboard.writeText(result.context)
                              setCopiedContext(true)
                              setTimeout(() => setCopiedContext(false), 2000)
                            }}
                            className="h-7 text-xs text-teal-600 hover:text-teal-700 flex items-center gap-1.5"
                          >
                            {copiedContext ? (
                              <>
                                <Check className="h-3.5 w-3.5 text-teal-600" />
                                Copied context
                              </>
                            ) : (
                              <>
                                <Copy className="h-3.5 w-3.5" />
                                Copy Context
                              </>
                            )}
                          </Button>
                        </div>
                        
                        <div className="rounded-lg border border-slate-200 overflow-hidden bg-slate-900 text-slate-300">
                          <pre className="p-5 font-mono text-[11px] whitespace-pre-wrap leading-relaxed max-h-[300px] overflow-y-auto">
                            {result.context || 'Patient profile summary has no records.'}
                          </pre>
                        </div>
                      </div>

                      {/* Reference Citations Lookup List */}
                      {result.citations && Object.keys(result.citations).length > 0 && (
                        <div className="space-y-2">
                          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Source Reference Citations</h4>
                          <div className="border border-slate-200 rounded-lg overflow-hidden divide-y divide-slate-100 bg-white">
                            {Object.entries(result.citations).map(([indexBadge, details]: any) => (
                              <div key={indexBadge} className="p-3 text-xs flex justify-between items-center gap-4 bg-white hover:bg-slate-50/50 transition-all">
                                <div className="flex items-center gap-3">
                                  <span className="font-bold text-teal-700 bg-teal-50 border border-teal-100 px-2 py-0.5 rounded font-mono text-center min-w-[28px]">
                                    [{indexBadge}]
                                  </span>
                                  <div className="space-y-0.5">
                                    <span className="font-semibold text-slate-700 block">
                                      Collection: <code className="text-slate-600 bg-slate-100 px-1 rounded text-[10px] font-normal">{details.collection || 'patient_reports'}</code>
                                    </span>
                                    <span className="text-slate-400 font-mono text-[10px] block">
                                      Document: {details.document_id || 'N/A'}
                                    </span>
                                  </div>
                                </div>
                                <div className="text-right text-[10px] text-slate-400">
                                  {details.score && (
                                    <span className="font-medium text-slate-500 block">Score: {(details.score * 100).toFixed(0)}%</span>
                                  )}
                                  {details.page_number && (
                                    <span className="block">Page {details.page_number}</span>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

function GraphHealthSummaryBadge() {
  const { data: health, isLoading, isError, refetch } = useGraphHealth()

  return (
    <Card className="shadow-sm border-slate-200 bg-white px-4 py-2 flex items-center gap-3">
      <div className="flex flex-col">
        <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Workflow Engine Status</span>
        {isLoading ? (
          <span className="text-sm font-medium text-slate-500 flex items-center gap-1.5 mt-0.5">
            <RefreshCw className="h-3 w-3 animate-spin" />
            Loading...
          </span>
        ) : isError ? (
          <span className="text-sm font-medium text-red-500 flex items-center gap-1.5 mt-0.5">
            <AlertTriangle className="h-4 w-4" />
            Connection Error
          </span>
        ) : health?.graph_compiled ? (
          <span className="text-sm font-medium text-teal-600 flex items-center gap-1.5 mt-0.5">
            <CheckCircle2 className="h-4 w-4 text-teal-500" />
            Compiled & Live (v{health.graph_version})
          </span>
        ) : (
          <span className="text-sm font-medium text-amber-500 flex items-center gap-1.5 mt-0.5">
            <AlertTriangle className="h-4 w-4" />
            Uncompiled
          </span>
        )}
      </div>
      <Button 
        variant="ghost" 
        size="icon" 
        onClick={() => refetch()} 
        disabled={isLoading}
        className="h-8 w-8 text-slate-400 hover:text-slate-600"
      >
        <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
      </Button>
    </Card>
  )
}

function CoreAgentsView() {
  const [activePlayground, setActivePlayground] = useState<'medical' | 'symptom' | 'memory'>('medical')
  
  const [medicalQuery, setMedicalQuery] = useState('What are the long-term management protocols for Type 2 Diabetes Mellitus?')
  const [medicalPatientId, setMedicalPatientId] = useState('')
  const [medicalDebug, setMedicalDebug] = useState(false)
  
  const [symptomQuery, setSymptomQuery] = useState('My patient reports sharp chest pain radiating to left arm with mild dyspnea and sweating.')
  const [symptomPatientId, setSymptomPatientId] = useState('')
  
  const [memoryPatientId, setMemoryPatientId] = useState('65f7c32b5e28a425fca68341')
  const [memoryQuery, setMemoryQuery] = useState('retrieve recent surgeries or allergies')

  const medicalMutation = useMedicalAgentTest()
  const symptomMutation = useSymptomAgentTest()
  const memoryMutation = useMemoryAgentTest()
  
  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useCoreAgentsStatistics()

  const handleTestMedical = () => {
    medicalMutation.mutate({
      query: medicalQuery,
      patient_id: medicalPatientId || undefined,
      debug_mode: medicalDebug
    })
  }

  const handleTestSymptom = () => {
    symptomMutation.mutate({
      query: symptomQuery,
      patient_id: symptomPatientId || undefined
    })
  }

  const handleTestMemory = () => {
    memoryMutation.mutate({
      query: memoryQuery,
      patient_id: memoryPatientId || undefined
    })
  }

  // Helper to safely fetch metrics per agent
  const getAgentStat = (agentName: string, metric: string, defaultValue: any = 0) => {
    if (!stats || !stats[agentName]) return defaultValue
    return stats[agentName][metric] ?? defaultValue
  }

  return (
    <div className="space-y-6">
      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {['MedicalKnowledgeAgent', 'SymptomAgent', 'MemoryAgent'].map((agent) => {
          const count = getAgentStat(agent, 'execution_count')
          const latency = getAgentStat(agent, 'average_latency_ms').toFixed(1)
          const tokens = getAgentStat(agent, 'total_tokens')
          const failures = getAgentStat(agent, 'failures')
          const cost = getAgentStat(agent, 'estimated_cost').toFixed(4)
          
          return (
            <Card key={agent} className="border border-slate-200 shadow-sm relative overflow-hidden bg-white">
              <CardHeader className="pb-2 border-b border-slate-100 bg-slate-50/50">
                <div className="flex justify-between items-center">
                  <CardTitle className="text-sm font-bold text-slate-800 tracking-tight">{agent}</CardTitle>
                  <span className="px-2 py-0.5 text-[10px] font-semibold bg-emerald-100 text-emerald-800 rounded-full">
                    Production
                  </span>
                </div>
              </CardHeader>
              <CardContent className="pt-4 grid grid-cols-2 gap-4">
                <div>
                  <span className="text-xs text-slate-400 block uppercase font-semibold">Executions</span>
                  <span className="text-lg font-bold text-slate-900">{count}</span>
                  <span className="text-[10px] text-red-500 block">Failures: {failures}</span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block uppercase font-semibold">Avg Latency</span>
                  <span className="text-lg font-bold text-slate-900">{latency} ms</span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block uppercase font-semibold">Tokens</span>
                  <span className="text-sm font-bold text-slate-900">{tokens.toLocaleString()}</span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block uppercase font-semibold">LLM Cost</span>
                  <span className="text-sm font-bold text-slate-900">${cost}</span>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Selector and Main Container */}
      <Card className="border border-slate-200 shadow-md overflow-hidden bg-white">
        <CardHeader className="pb-0 border-b border-slate-100 bg-slate-50/50">
          <div className="flex justify-between items-center">
            <div className="flex gap-4">
              <button
                onClick={() => setActivePlayground('medical')}
                className={`pb-3 text-sm font-semibold border-b-2 transition-all ${
                  activePlayground === 'medical'
                    ? 'border-teal-600 text-teal-600 font-bold'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                Medical Knowledge
              </button>
              <button
                onClick={() => setActivePlayground('symptom')}
                className={`pb-3 text-sm font-semibold border-b-2 transition-all ${
                  activePlayground === 'symptom'
                    ? 'border-teal-600 text-teal-600 font-bold'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                Symptom Guidance
              </button>
              <button
                onClick={() => setActivePlayground('memory')}
                className={`pb-3 text-sm font-semibold border-b-2 transition-all ${
                  activePlayground === 'memory'
                    ? 'border-teal-600 text-teal-600 font-bold'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                Memory Sync & Recall
              </button>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetchStats()}
              disabled={statsLoading}
              className="mb-2 text-xs flex items-center gap-1.5"
            >
              <RefreshCw className={`h-3 w-3 ${statsLoading ? 'animate-spin' : ''}`} />
              Refresh Stats
            </Button>
          </div>
        </CardHeader>

        <CardContent className="pt-6">
          {activePlayground === 'medical' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Inputs Panel */}
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-slate-700 block">Clinical Query</label>
                  <textarea
                    rows={4}
                    value={medicalQuery}
                    onChange={(e) => setMedicalQuery(e.target.value)}
                    className="w-full p-3 border border-slate-300 rounded-lg text-sm bg-slate-50 focus:bg-white focus:ring-2 focus:ring-teal-500 focus:outline-none transition-all leading-relaxed"
                    placeholder="Enter medical question..."
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700 block">Patient ID (Optional)</label>
                    <Input
                      type="text"
                      value={medicalPatientId}
                      onChange={(e) => setMedicalPatientId(e.target.value)}
                      placeholder="e.g. 65f7c3..."
                      className="border-slate-300"
                    />
                  </div>
                  <div className="flex items-center gap-2 pt-8">
                    <input
                      type="checkbox"
                      id="medical_debug"
                      checked={medicalDebug}
                      onChange={(e) => setMedicalDebug(e.target.checked)}
                      className="rounded text-teal-600 focus:ring-teal-500"
                    />
                    <label htmlFor="medical_debug" className="text-sm text-slate-600 font-semibold cursor-pointer">
                      Debug Mode
                    </label>
                  </div>
                </div>
                <Button
                  onClick={handleTestMedical}
                  disabled={medicalMutation.isPending}
                  className="w-full bg-teal-600 hover:bg-teal-700 text-white font-bold"
                >
                  {medicalMutation.isPending ? 'Executing RAG pipeline...' : 'Execute Medical Agent'}
                </Button>
              </div>

              {/* Outputs Panel */}
              <div className="space-y-4">
                {medicalMutation.data ? (
                  <div className="space-y-4">
                    <div className="p-4 bg-emerald-50 border border-emerald-100 rounded-lg shadow-sm">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-xs font-bold text-emerald-800 uppercase tracking-wider block">Agent Answer Output</span>
                        <span className="text-[10px] font-semibold bg-emerald-200 text-emerald-900 rounded-full px-2 py-0.5">
                          Confidence: {(medicalMutation.data.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-sm text-slate-800 leading-relaxed font-sans whitespace-pre-wrap">
                        {medicalMutation.data.answer}
                      </p>
                    </div>

                    {medicalMutation.data.sources && medicalMutation.data.sources.length > 0 && (
                      <div className="space-y-1.5">
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Sources Consulted</span>
                        <div className="flex flex-wrap gap-2">
                          {medicalMutation.data.sources.map((src) => (
                            <span key={src} className="px-2.5 py-1 text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200 rounded-md">
                              {src}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {medicalMutation.data.citations && medicalMutation.data.citations.length > 0 && (
                      <div className="space-y-2">
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Citations & Grounding Chunks</span>
                        <div className="space-y-2 max-h-[220px] overflow-y-auto">
                          {medicalMutation.data.citations.map((c, i) => (
                            <div key={i} className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs leading-relaxed">
                              <div className="flex justify-between items-center mb-1">
                                <span className="font-bold text-teal-800">[{c.source}]</span>
                                <span className="text-[10px] font-mono text-slate-400">Score: {(c.score * 100).toFixed(0)}%</span>
                              </div>
                              <p className="text-slate-600 font-sans italic">&ldquo;{c.text}&rdquo;</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : medicalMutation.error ? (
                  <div className="p-4 bg-red-50 border border-red-100 rounded-lg flex items-start gap-2 text-sm text-red-800 leading-relaxed font-semibold">
                    <AlertTriangle className="h-5 w-5 text-red-500 flex-shrink-0" />
                    Error: {medicalMutation.error.message}
                  </div>
                ) : (
                  <div className="h-[250px] border border-dashed border-slate-300 rounded-lg flex flex-col justify-center items-center text-slate-400 gap-2">
                    <Brain className="h-10 w-10 text-slate-300" />
                    <span className="text-sm font-semibold">Ready to execute Medical Knowledge RAG test.</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {activePlayground === 'symptom' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Inputs Panel */}
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-slate-700 block">Reported Symptoms</label>
                  <textarea
                    rows={4}
                    value={symptomQuery}
                    onChange={(e) => setSymptomQuery(e.target.value)}
                    className="w-full p-3 border border-slate-300 rounded-lg text-sm bg-slate-50 focus:bg-white focus:ring-2 focus:ring-teal-500 focus:outline-none transition-all leading-relaxed"
                    placeholder="Describe patient symptoms..."
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-slate-700 block">Patient ID (Optional)</label>
                  <Input
                    type="text"
                    value={symptomPatientId}
                    onChange={(e) => setSymptomPatientId(e.target.value)}
                    placeholder="e.g. 65f7c3..."
                    className="border-slate-300"
                  />
                </div>
                <Button
                  onClick={handleTestSymptom}
                  disabled={symptomMutation.isPending}
                  className="w-full bg-teal-600 hover:bg-teal-700 text-white font-bold"
                >
                  {symptomMutation.isPending ? 'Analyzing symptoms...' : 'Analyze Symptoms'}
                </Button>
              </div>

              {/* Outputs Panel */}
              <div className="space-y-4">
                {symptomMutation.data ? (
                  <div className="space-y-4">
                    {symptomMutation.data.emergency && (
                      <div className="p-3 bg-red-100 border border-red-200 rounded-lg text-red-900 font-bold flex items-center gap-2 text-sm shadow-sm animate-pulse">
                        <AlertTriangle className="h-5 w-5 text-red-600 flex-shrink-0" />
                        EMERGENCY NOTICE: Immediate medical check recommended!
                      </div>
                    )}

                    <div className="p-4 bg-emerald-50 border border-emerald-100 rounded-lg shadow-sm">
                      <span className="text-xs font-bold text-emerald-800 uppercase tracking-wider block mb-2">Guidance Summary</span>
                      <p className="text-sm text-slate-800 leading-relaxed font-sans whitespace-pre-wrap">
                        {symptomMutation.data.summary}
                      </p>
                    </div>

                    {symptomMutation.data.possible_causes && symptomMutation.data.possible_causes.length > 0 && (
                      <div className="space-y-1.5">
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Possible Causes</span>
                        <div className="flex flex-wrap gap-1.5">
                          {symptomMutation.data.possible_causes.map((c) => (
                            <span key={c} className="px-2 py-0.5 text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200 rounded-md">
                              {c}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {symptomMutation.data.red_flags && symptomMutation.data.red_flags.length > 0 && (
                      <div className="space-y-1.5">
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Red Flags / Risks</span>
                        <div className="flex flex-wrap gap-1.5">
                          {symptomMutation.data.red_flags.map((flag) => (
                            <span key={flag} className="px-2 py-0.5 text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200 rounded-md flex items-center gap-1">
                              <AlertTriangle className="h-3 w-3" />
                              {flag}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs leading-relaxed">
                      <span className="text-[10px] font-bold text-slate-400 uppercase block mb-1">Recommended Action Protocols</span>
                      <p className="text-slate-700 font-sans font-semibold">
                        {symptomMutation.data.recommended_action}
                      </p>
                    </div>
                  </div>
                ) : symptomMutation.error ? (
                  <div className="p-4 bg-red-50 border border-red-100 rounded-lg flex items-start gap-2 text-sm text-red-800 leading-relaxed font-semibold">
                    <AlertTriangle className="h-5 w-5 text-red-500 flex-shrink-0" />
                    Error: {symptomMutation.error.message}
                  </div>
                ) : (
                  <div className="h-[250px] border border-dashed border-slate-300 rounded-lg flex flex-col justify-center items-center text-slate-400 gap-2">
                    <Brain className="h-10 w-10 text-slate-300" />
                    <span className="text-sm font-semibold">Ready to analyze symptoms.</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {activePlayground === 'memory' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Inputs Panel */}
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-slate-700 block">Patient ID (Required for MongoDB retrieval)</label>
                  <Input
                    type="text"
                    value={memoryPatientId}
                    onChange={(e) => setMemoryPatientId(e.target.value)}
                    placeholder="e.g. 65f7c3..."
                    className="border-slate-300"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-slate-700 block">Semantic Query (Search chat vector memories)</label>
                  <textarea
                    rows={2}
                    value={memoryQuery}
                    onChange={(e) => setMemoryQuery(e.target.value)}
                    className="w-full p-3 border border-slate-300 rounded-lg text-sm bg-slate-50 focus:bg-white focus:ring-2 focus:ring-teal-500 focus:outline-none transition-all leading-relaxed"
                    placeholder="Describe memory concepts to recall..."
                  />
                </div>
                <Button
                  onClick={handleTestMemory}
                  disabled={memoryMutation.isPending || !memoryPatientId}
                  className="w-full bg-teal-600 hover:bg-teal-700 text-white font-bold"
                >
                  {memoryMutation.isPending ? 'Syncing and recalling memory...' : 'Execute Memory Agent (Sync & Recall)'}
                </Button>
              </div>

              {/* Outputs Panel */}
              <div className="space-y-4">
                {memoryMutation.data ? (
                  <div className="space-y-4">
                    <div className="p-4 bg-emerald-50 border border-emerald-100 rounded-lg shadow-sm">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-xs font-bold text-emerald-800 uppercase tracking-wider block">Longitudinal Summary (MongoDB Memory)</span>
                        <span className="text-[10px] font-mono text-emerald-700 font-bold bg-emerald-100 rounded-full px-2 py-0.5">
                          Synced Live
                        </span>
                      </div>
                      <p className="text-sm text-slate-800 leading-relaxed font-sans whitespace-pre-wrap">
                        {memoryMutation.data.memory_summary}
                      </p>
                    </div>

                    <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs max-h-[150px] overflow-y-auto">
                      <span className="font-bold text-slate-500 uppercase block mb-1">AGGREGATED CLINICAL PROFILE</span>
                      <pre className="text-[11px] font-mono text-slate-600 leading-normal whitespace-pre-wrap">
                        {memoryMutation.data.patient_summary}
                      </pre>
                    </div>

                    {memoryMutation.data.relevant_context && memoryMutation.data.relevant_context.length > 0 && (
                      <div className="space-y-2">
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Semantic Memories Recalled (Qdrant vectors)</span>
                        <div className="space-y-1.5 max-h-[150px] overflow-y-auto">
                          {memoryMutation.data.relevant_context.map((m, i) => (
                            <div key={i} className="p-2 bg-slate-50 border border-slate-200 rounded text-xs leading-normal">
                              <p className="text-slate-600 italic">&ldquo;{m.content || m.text}&rdquo;</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {memoryMutation.data.conversation_history && memoryMutation.data.conversation_history.length > 0 && (
                      <div className="space-y-2">
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Recent Chats Audit (MongoDB logs)</span>
                        <div className="space-y-1.5 max-h-[150px] overflow-y-auto border border-slate-100 rounded-lg p-2 bg-slate-50/50">
                          {memoryMutation.data.conversation_history.map((h, i) => (
                            <div key={i} className="text-[11px] border-b border-slate-100 pb-1.5 last:border-0">
                              <span className="font-bold text-teal-800 uppercase text-[9px] mr-1 block">[{h.role}]</span>
                              <span className="text-slate-600 font-sans leading-snug">{h.content}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : memoryMutation.error ? (
                  <div className="p-4 bg-red-50 border border-red-100 rounded-lg flex items-start gap-2 text-sm text-red-800 leading-relaxed font-semibold">
                    <AlertTriangle className="h-5 w-5 text-red-500 flex-shrink-0" />
                    Error: {memoryMutation.error.message}
                  </div>
                ) : (
                  <div className="h-[250px] border border-dashed border-slate-300 rounded-lg flex flex-col justify-center items-center text-slate-400 gap-2">
                    <Brain className="h-10 w-10 text-slate-300" />
                    <span className="text-sm font-semibold">Ready to test Patient Memory Sync pipeline.</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}


function RouterAgentView() {
  const { data: intents, isLoading: isIntentsLoading } = useRouterIntents()
  const { data: stats, isLoading: isStatsLoading, refetch: refetchStats } = useRouterStatistics()
  
  const classifyMutation = useRouterClassify()
  const testMutation = useRouterTest()
  
  const [queryInput, setQueryInput] = useState('My patient has high blood sugar and a headache. recommend a specialist.')
  const [patientIdInput, setPatientIdInput] = useState('')
  const [debugMode, setDebugMode] = useState(false)
  const [activeViewTab, setActiveViewTab] = useState<'classification' | 'pipeline'>('classification')
  
  const handleClassifyOnly = () => {
    classifyMutation.mutate({ query: queryInput })
  }
  
  const handleTestPipeline = () => {
    testMutation.mutate({
      query: queryInput,
      patient_id: patientIdInput || undefined,
      debug_mode: debugMode
    })
  }

  const handleRefresh = () => {
    refetchStats()
  }

  const isLoading = isIntentsLoading || isStatsLoading

  return (
    <div className="space-y-6">
      {/* Action Bar */}
      <div className="flex justify-between items-center bg-slate-50 border border-slate-200 px-4 py-3 rounded-xl shadow-sm">
        <div className="flex items-center gap-2.5">
          <Sparkles className="h-5 w-5 text-teal-600 animate-pulse" />
          <span className="font-semibold text-slate-800 text-sm">Router Agent Console & Analytics</span>
        </div>
        <Button
          onClick={handleRefresh}
          disabled={isLoading}
          variant="outline"
          size="sm"
          className="h-8 text-xs flex items-center gap-1.5 hover:bg-slate-100"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh Stats
        </Button>
      </div>

      {/* Telemetry Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="shadow-sm border-slate-200 bg-white">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Routed Requests</span>
              <Activity className="h-4 w-4 text-teal-500" />
            </div>
            <div className="mt-2.5 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-900">{stats?.total_routed_requests ?? 0}</span>
            </div>
            <p className="mt-1 text-xs text-slate-400">Cumulative router entrypoint runs</p>
          </CardContent>
        </Card>

        <Card className="shadow-sm border-slate-200 bg-white">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Average Latency</span>
              <Clock className="h-4 w-4 text-teal-500" />
            </div>
            <div className="mt-2.5 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-900">{stats?.average_routing_latency_ms ?? 0} ms</span>
            </div>
            <p className="mt-1 text-xs text-slate-400">Mean query evaluation latency</p>
          </CardContent>
        </Card>

        <Card className="shadow-sm border-slate-200 bg-white">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Fallback Rate</span>
              <AlertTriangle className="h-4 w-4 text-amber-500" />
            </div>
            <div className="mt-2.5 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-900">{stats?.fallback_percentage ?? 0}%</span>
              <span className="text-xs font-semibold text-slate-400">({stats?.fallback_count ?? 0} runs)</span>
            </div>
            <p className="mt-1 text-xs text-slate-400">Queries matching low confidence</p>
          </CardContent>
        </Card>

        <Card className="shadow-sm border-slate-200 bg-white">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Unknown Rate</span>
              <AlertTriangle className="h-4 w-4 text-red-500" />
            </div>
            <div className="mt-2.5 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-900">{stats?.unknown_percentage ?? 0}%</span>
              <span className="text-xs font-semibold text-slate-400">({stats?.unknown_queries_count ?? 0} queries)</span>
            </div>
            <p className="mt-1 text-xs text-slate-400">Queries resolved as UNKNOWN</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Workspace Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column: Tester sandbox */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="shadow-sm border-slate-200 bg-white">
            <CardHeader className="border-b border-slate-100">
              <CardTitle className="text-slate-800 text-base font-bold flex items-center gap-2">
                <Terminal className="h-4 w-4 text-teal-600" />
                Deterministic Query Classifier Sandbox
              </CardTitle>
              <CardDescription>
                Input text prompts to test confidence ratios matching and target agent routing decisions.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 pt-6">
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">User Query Prompt</label>
                <Textarea
                  value={queryInput}
                  onChange={(e) => setQueryInput(e.target.value)}
                  placeholder="Type symptoms, medical questions, drug side-effects, or lab reports to route..."
                  className="min-h-[100px] text-slate-800 text-sm border-slate-200 focus:border-teal-500 focus:ring-teal-500 rounded-xl"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Patient ID (Optional)</label>
                  <input
                    type="text"
                    value={patientIdInput}
                    onChange={(e) => setPatientIdInput(e.target.value)}
                    placeholder="MongoDB reference ID"
                    className="w-full text-slate-800 text-sm px-3.5 py-2 border border-slate-200 focus:border-teal-500 focus:ring-teal-500 rounded-xl"
                  />
                </div>
                <div className="flex items-center gap-2 pt-6">
                  <input
                    type="checkbox"
                    id="router-debug-mode"
                    checked={debugMode}
                    onChange={(e) => setDebugMode(e.target.checked)}
                    className="h-4 w-4 text-teal-600 focus:ring-teal-500 border-slate-200 rounded"
                  />
                  <label htmlFor="router-debug-mode" className="text-sm font-semibold text-slate-700 select-none">
                    Enable Graph Tracing Mode
                  </label>
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <Button
                  onClick={handleClassifyOnly}
                  disabled={classifyMutation.isPending || !queryInput.trim()}
                  className="bg-teal-600 hover:bg-teal-700 text-white rounded-xl px-4 text-sm"
                >
                  {classifyMutation.isPending ? 'Classifying...' : 'Classify Intent Only'}
                </Button>
                <Button
                  onClick={handleTestPipeline}
                  disabled={testMutation.isPending || !queryInput.trim()}
                  variant="outline"
                  className="border-slate-200 hover:bg-slate-50 rounded-xl px-4 text-sm flex items-center gap-1.5"
                >
                  {testMutation.isPending ? 'Running Pipeline...' : 'Run Stateful Graph Pipeline'}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Classification / Run result panels */}
          {(classifyMutation.data || testMutation.data) && (
            <Card className="shadow-sm border-slate-200 bg-white">
              <CardHeader className="border-b border-slate-100 flex flex-row items-center justify-between py-4">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-teal-500 animate-pulse" />
                  <CardTitle className="text-slate-800 text-sm font-bold uppercase tracking-wide">
                    Routing Engine Outputs
                  </CardTitle>
                </div>
                <div className="flex border border-slate-200 rounded-lg p-0.5 bg-slate-50">
                  <button
                    onClick={() => setActiveViewTab('classification')}
                    className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                      activeViewTab === 'classification'
                        ? 'bg-white shadow-sm text-teal-600'
                        : 'text-slate-500 hover:text-slate-700'
                    }`}
                  >
                    Scoring Details
                  </button>
                  <button
                    onClick={() => setActiveViewTab('pipeline')}
                    disabled={!testMutation.data}
                    className={`px-3 py-1 text-xs font-semibold rounded-md transition-all disabled:opacity-50 ${
                      activeViewTab === 'pipeline'
                        ? 'bg-white shadow-sm text-teal-600'
                        : 'text-slate-500 hover:text-slate-700'
                    }`}
                  >
                    State Graph Trace
                  </button>
                </div>
              </CardHeader>
              <CardContent className="pt-6">
                {activeViewTab === 'classification' ? (
                  <div className="space-y-5">
                    {/* Winner layout */}
                    {(() => {
                      const data = classifyMutation.data || testMutation.data
                      if (!data) return null
                      const confPercent = Math.round(data.confidence * 100)
                      return (
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-slate-50 border border-slate-100 p-4 rounded-xl">
                          <div>
                            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Detected Intent</span>
                            <span className="text-base font-bold text-slate-800 block mt-0.5">{data.detected_intent}</span>
                          </div>
                          <div>
                            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Confidence Rating</span>
                            <div className="flex items-center gap-2 mt-1">
                              <div className="flex-1 bg-slate-200 h-2 rounded-full overflow-hidden">
                                <div className="bg-teal-500 h-full rounded-full" style={{ width: `${confPercent}%` }} />
                              </div>
                              <span className="text-xs font-bold text-teal-600">{confPercent}%</span>
                            </div>
                          </div>
                          <div>
                            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Target Destination Agent</span>
                            <span className="text-xs font-bold bg-teal-50 text-teal-700 border border-teal-200 rounded-md px-2 py-0.5 inline-block mt-1">
                              {data.selected_agent}
                            </span>
                          </div>
                        </div>
                      )
                    })()}

                    {/* Matched rules logs */}
                    <div>
                      <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-2">Matched Logic Rules Logs</span>
                      <div className="flex flex-wrap gap-1.5">
                        {(() => {
                          const data = classifyMutation.data || testMutation.data
                          const rules = classifyMutation.data ? classifyMutation.data.matched_rules : (testMutation.data?.routing_trace || [])
                          if (!rules || rules.length === 0) {
                            return <span className="text-xs text-slate-400 italic">No direct keyword or regex patterns matched. Resolving fallback.</span>
                          }
                          return rules.map((rule, idx) => (
                            <span 
                              key={idx} 
                              className={`text-[11px] font-medium px-2 py-0.5 rounded-full border ${
                                rule.startsWith('regex') 
                                  ? 'bg-purple-50 text-purple-700 border-purple-200' 
                                  : rule.startsWith('keyword') 
                                  ? 'bg-blue-50 text-blue-700 border-blue-200' 
                                  : 'bg-amber-50 text-amber-700 border-amber-200'
                              }`}
                            >
                              {rule}
                            </span>
                          ))
                        })()}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {testMutation.data && (
                      <>
                        <div className="flex justify-between items-center text-xs border-b border-slate-100 pb-2">
                          <span className="font-semibold text-slate-500">Routing Latency Performance:</span>
                          <span className="font-bold text-teal-600">{testMutation.data.latency_ms.toFixed(2)} ms</span>
                        </div>
                        <div className="space-y-2.5">
                          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">Graph Nodes Trace Order</span>
                          <div className="flex flex-col gap-2 pl-4 border-l-2 border-slate-100">
                            {testMutation.data.graph_trace.map((node, idx) => (
                              <div key={idx} className="flex items-center gap-2 text-xs">
                                <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 flex items-center justify-center text-[8px] font-bold text-white ${
                                  node === '__start__' ? 'bg-slate-400' : node === '__finish__' ? 'bg-slate-950' : 'bg-teal-500'
                                }`}>
                                  {idx + 1}
                                </div>
                                <span className={node === 'router_agent' ? 'font-bold text-teal-600' : 'text-slate-600'}>
                                  {node}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right column: Intent registry & Active settings */}
        <div className="space-y-6">
          {/* Active Settings card */}
          <Card className="shadow-sm border-slate-200 bg-white">
            <CardHeader className="border-b border-slate-100 py-4">
              <CardTitle className="text-slate-800 text-sm font-bold flex items-center gap-2">
                <Sparkles className="h-4.5 w-4.5 text-teal-600" />
                Routing Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 text-xs space-y-3">
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500 font-medium">High Threshold:</span>
                <span className="font-bold text-slate-800">{intents?.routing_rules.ROUTER_CONFIDENCE_HIGH ?? 0.7}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500 font-medium">Medium Threshold:</span>
                <span className="font-bold text-slate-800">{intents?.routing_rules.ROUTER_CONFIDENCE_MEDIUM ?? 0.4}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500 font-medium">Regex Checks:</span>
                <span className={`font-bold ${intents?.routing_rules.ROUTER_ENABLE_REGEX ? 'text-emerald-600' : 'text-slate-400'}`}>
                  {intents?.routing_rules.ROUTER_ENABLE_REGEX ? 'Enabled' : 'Disabled'}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500 font-medium">Keyword Checks:</span>
                <span className={`font-bold ${intents?.routing_rules.ROUTER_ENABLE_KEYWORDS ? 'text-emerald-600' : 'text-slate-400'}`}>
                  {intents?.routing_rules.ROUTER_ENABLE_KEYWORDS ? 'Enabled' : 'Disabled'}
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Mappings directory card */}
          <Card className="shadow-sm border-slate-200 bg-white">
            <CardHeader className="border-b border-slate-100 py-4">
              <CardTitle className="text-slate-800 text-sm font-bold flex items-center gap-2">
                <Database className="h-4.5 w-4.5 text-teal-600" />
                Active Mappings Registry
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 p-0 max-h-[350px] overflow-y-auto">
              <div className="divide-y divide-slate-100">
                {intents ? (
                  Object.entries(intents.registered_agents).map(([intent, agent]) => (
                    <div key={intent} className="px-4 py-2.5 flex flex-col gap-0.5 hover:bg-slate-50 transition-colors">
                      <span className="text-[10px] font-bold text-slate-400 tracking-wider uppercase">{intent}</span>
                      <span className="text-xs font-semibold text-slate-700">{agent}</span>
                    </div>
                  ))
                ) : (
                  <div className="p-4 text-xs text-slate-400 italic text-center">Loading mappings...</div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}


function WorkflowEngineView() {
  const { data: health, isLoading: isHealthLoading, refetch: refetchHealth } = useGraphHealth()
  const { data: stats, isLoading: isStatsLoading, refetch: refetchStats } = useGraphStatistics()
  const testRunMutation = useGraphTestRun()

  const [queryInput, setQueryInput] = useState('Analyse my lab report for high cholesterol')
  const [patientIdInput, setPatientIdInput] = useState('')
  const [debugMode, setDebugMode] = useState(false)
  const [customMetadata, setCustomMetadata] = useState('{\n  "source": "admin_console"\n}')
  const [activeTraceTab, setActiveTraceTab] = useState<'timeline' | 'timings' | 'json'>('timeline')

  const handleMockExecute = () => {
    let parsedMetadata = {}
    try {
      parsedMetadata = JSON.parse(customMetadata)
    } catch (e) {
      alert('Invalid custom metadata JSON format.')
      return
    }

    testRunMutation.mutate({
      query: queryInput || undefined,
      patient_id: patientIdInput || undefined,
      debug_mode: debugMode,
      metadata: parsedMetadata
    })
  }

  const handleRefreshAll = () => {
    refetchHealth()
    refetchStats()
  }

  const successRate = stats ? (stats.successful_executions / (stats.total_executions || 1)) * 100 : 100

  return (
    <div className="space-y-6">
      {/* Top action bar */}
      <div className="flex justify-between items-center bg-slate-50 border border-slate-200 px-4 py-3 rounded-xl shadow-sm">
        <div className="flex items-center gap-2.5">
          <Activity className="h-5 w-5 text-teal-600 animate-pulse" />
          <span className="font-semibold text-slate-800 text-sm">Stateful Orchestration Workflow Sandbox</span>
        </div>
        <Button
          onClick={handleRefreshAll}
          disabled={isHealthLoading || isStatsLoading}
          variant="outline"
          size="sm"
          className="h-8 text-xs flex items-center gap-1.5 hover:bg-slate-100"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isHealthLoading || isStatsLoading ? 'animate-spin' : ''}`} />
          Live Refresh Metrics
        </Button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-white border-slate-200 shadow-sm relative overflow-hidden group">
          <CardHeader className="pb-2">
            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Compiled Status</span>
            <CardTitle className="text-xl font-bold flex items-center gap-2 mt-1">
              {health?.graph_compiled ? (
                <>
                  <CheckCircle2 className="h-5 w-5 text-teal-500" />
                  <span className="text-teal-700">Compiled</span>
                </>
              ) : (
                <>
                  <AlertTriangle className="h-5 w-5 text-amber-500 animate-bounce" />
                  <span className="text-amber-700">Uncompiled</span>
                </>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <p className="text-xs text-slate-500">Version: <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-600 font-mono text-[10px]">{health?.graph_version || '1.0.0'}</code></p>
          </CardContent>
          <div className="absolute top-0 right-0 h-full w-1.5 bg-teal-500" />
        </Card>

        <Card className="bg-white border-slate-200 shadow-sm">
          <CardHeader className="pb-2">
            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Total Executions</span>
            <CardTitle className="text-2xl font-black text-slate-800 mt-1">
              {stats?.total_executions || 0}
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <p className="text-xs text-slate-500">Active Execs: <span className="font-semibold text-slate-700">{stats?.active_executions || 0}</span></p>
          </CardContent>
        </Card>

        <Card className="bg-white border-slate-200 shadow-sm">
          <CardHeader className="pb-2">
            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Success Rate</span>
            <CardTitle className="text-2xl font-black mt-1 text-teal-600">
              {successRate.toFixed(1)}%
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <p className="text-xs text-slate-500">Failed: <span className="font-semibold text-red-600">{stats?.failed_executions || 0}</span></p>
          </CardContent>
        </Card>

        <Card className="bg-white border-slate-200 shadow-sm">
          <CardHeader className="pb-2">
            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Avg Latency</span>
            <CardTitle className="text-2xl font-black text-slate-800 mt-1 flex items-baseline gap-1">
              {stats?.avg_latency ? stats.avg_latency.toFixed(1) : '0.0'}
              <span className="text-xs text-slate-400 font-normal">ms</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <p className="text-xs text-slate-500">Timeouts: <span className="font-semibold text-amber-600">{stats?.timeout_count || 0}</span> | Cancelled: <span className="font-semibold text-indigo-600">{stats?.cancelled_count || 0}</span></p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Col: Setup & Sandbox */}
        <div className="lg:col-span-2 space-y-6">
          {/* Active Nodes Setup config */}
          <Card className="bg-white border-slate-200 shadow-sm">
            <CardHeader className="border-b border-slate-100 pb-3 flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base font-bold text-slate-800 flex items-center gap-2">
                  <Cpu className="h-4.5 w-4.5 text-teal-600" />
                  Stateful Graph Nodes Layout
                </CardTitle>
                <CardDescription className="text-xs mt-0.5">
                  Static visual graph of currently compiled pipeline nodes and transitions rules.
                </CardDescription>
              </div>
              <span className="text-[10px] bg-teal-50 border border-teal-100 text-teal-700 px-2 py-0.5 rounded-full font-bold uppercase font-mono">
                {health?.registered_nodes.length || 0} Nodes
              </span>
            </CardHeader>
            <CardContent className="p-4 space-y-4">
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Registered Nodes Directory</h4>
                <div className="flex flex-wrap gap-2">
                  {health?.registered_nodes.map((nodeName) => (
                    <span 
                      key={nodeName} 
                      className={`text-xs px-2.5 py-1 rounded-lg border font-mono font-medium flex items-center gap-1.5 ${
                        nodeName === '__start__' 
                          ? 'bg-teal-50 border-teal-200 text-teal-700' 
                          : nodeName === '__finish__'
                          ? 'bg-slate-100 border-slate-300 text-slate-700'
                          : nodeName === 'initialize_state'
                          ? 'bg-blue-50 border-blue-200 text-blue-700'
                          : 'bg-amber-50 border-amber-200 text-amber-700'
                      }`}
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
                      {nodeName}
                    </span>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Configured Directed Transitions</h4>
                <div className="border border-slate-200 rounded-lg overflow-hidden divide-y divide-slate-100">
                  {health?.registered_transitions && health.registered_transitions.length > 0 ? (
                    health.registered_transitions.map((t, idx) => (
                      <div key={idx} className="p-2.5 text-xs flex justify-between items-center gap-4 bg-white hover:bg-slate-50/50 transition-all font-mono">
                        <div className="flex items-center gap-2 text-slate-700 font-semibold">
                          <code className="text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded border border-blue-100">{t.source}</code>
                          <span className="text-slate-400 font-bold">➔</span>
                          <code className="text-teal-600 bg-teal-50 px-1.5 py-0.5 rounded border border-teal-100">{t.target || 'Conditional'}</code>
                        </div>
                        <div className="text-right">
                          <span className={`text-[10px] px-2 py-0.5 rounded border font-semibold ${
                            t.type === 'normal' 
                              ? 'bg-slate-100 border-slate-200 text-slate-600'
                              : t.type === 'conditional'
                              ? 'bg-amber-100 border-amber-200 text-amber-700'
                              : 'bg-teal-100 border-teal-200 text-teal-700'
                          }`}>
                            {t.type}
                          </span>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="p-4 text-center text-slate-400 text-xs font-mono bg-white">No active transitions registered</div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Sandbox console sandbox card */}
          <Card className="bg-white border-slate-200 shadow-sm">
            <CardHeader className="border-b border-slate-100 pb-3">
              <CardTitle className="text-base font-bold text-slate-800 flex items-center gap-2">
                <Terminal className="h-4.5 w-4.5 text-teal-600" />
                Workflow Execution Sandbox Console
              </CardTitle>
              <CardDescription className="text-xs mt-0.5">
                Trigger validation execution using custom queries payload to verify state variables updates.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-5 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block">Query Input String</label>
                  <input
                    type="text"
                    value={queryInput}
                    onChange={(e) => setQueryInput(e.target.value)}
                    placeholder="Enter query..."
                    className="w-full text-xs bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-800 placeholder-slate-400 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 font-medium transition-all"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block">Associated Patient ID (Optional)</label>
                  <input
                    type="text"
                    value={patientIdInput}
                    onChange={(e) => setPatientIdInput(e.target.value)}
                    placeholder="Patient ObjectId reference..."
                    className="w-full text-xs bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-800 placeholder-slate-400 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 font-mono transition-all"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between items-center">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block">Custom State Metadata JSON</label>
                  <span className="text-[10px] text-slate-400 block font-mono">Parsed at execution</span>
                </div>
                <textarea
                  value={customMetadata}
                  onChange={(e) => setCustomMetadata(e.target.value)}
                  rows={3}
                  className="w-full text-xs bg-slate-900 text-slate-300 font-mono border border-slate-950 rounded-lg px-3 py-2.5 focus:outline-none focus:ring-1 focus:ring-teal-500 shadow-inner"
                />
              </div>

              <div className="flex items-center justify-between pt-1">
                <div className="flex items-center gap-3">
                  <input
                    id="debugModeGraph"
                    type="checkbox"
                    checked={debugMode}
                    onChange={(e) => setDebugMode(e.target.checked)}
                    className="h-4 w-4 text-teal-600 focus:ring-teal-500 border-slate-300 rounded"
                  />
                  <label htmlFor="debugModeGraph" className="text-xs font-semibold text-slate-600 block cursor-pointer">
                    Bypass Execution Caches (Debug Mode)
                  </label>
                </div>

                <Button
                  onClick={handleMockExecute}
                  disabled={testRunMutation.isPending}
                  className="h-9 px-4 text-xs font-bold text-white bg-teal-600 hover:bg-teal-700 rounded-lg shadow-sm flex items-center gap-1.5 transition-all"
                >
                  {testRunMutation.isPending ? (
                    <>
                      <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                      Executing...
                    </>
                  ) : (
                    <>
                      <Zap className="h-3.5 w-3.5 fill-current" />
                      Trigger Mock Execution
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Col: Cumulative execution analytics */}
        <div className="space-y-6">
          <Card className="bg-white border-slate-200 shadow-sm">
            <CardHeader className="border-b border-slate-100 pb-3">
              <CardTitle className="text-base font-bold text-slate-800 flex items-center gap-2">
                <Activity className="h-4.5 w-4.5 text-teal-600" />
                Traversal Statistics Mapping
              </CardTitle>
              <CardDescription className="text-xs mt-0.5">
                Lifetime invocation metrics for nodes and transitions keys.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-4 space-y-4">
              <div className="space-y-2">
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Node Executions Counts</span>
                <div className="border border-slate-150 rounded-lg divide-y divide-slate-100 overflow-hidden text-xs bg-white font-mono max-h-[160px] overflow-y-auto">
                  {stats?.node_execution_count && Object.keys(stats.node_execution_count).length > 0 ? (
                    Object.entries(stats.node_execution_count).map(([node, count]) => (
                      <div key={node} className="p-2 flex justify-between bg-white hover:bg-slate-50/50">
                        <span className="text-slate-600">{node}</span>
                        <span className="font-bold text-slate-800">{count} runs</span>
                      </div>
                    ))
                  ) : (
                    <div className="p-4 text-center text-slate-400 text-xs">No metrics data logged yet</div>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Transition Traversals Counts</span>
                <div className="border border-slate-150 rounded-lg divide-y divide-slate-100 overflow-hidden text-xs bg-white font-mono max-h-[160px] overflow-y-auto">
                  {stats?.transition_count && Object.keys(stats.transition_count).length > 0 ? (
                    Object.entries(stats.transition_count).map(([transition, count]) => (
                      <div key={transition} className="p-2 flex justify-between bg-white hover:bg-slate-50/50">
                        <span className="text-slate-600">{transition}</span>
                        <span className="font-bold text-slate-800">{count} hits</span>
                      </div>
                    ))
                  ) : (
                    <div className="p-4 text-center text-slate-400 text-xs">No metrics data logged yet</div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Mock run execution output panel */}
      {testRunMutation.data && (
        <Card className="bg-white border-slate-200 shadow-md">
          <CardHeader className="border-b border-slate-100 pb-3 flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-sm font-bold text-slate-800 flex items-center gap-1.5">
                <Terminal className="h-4 w-4 text-teal-600" />
                Execution Results Trace Log Output
              </CardTitle>
              <CardDescription className="text-xs mt-0.5">
                Traversed step timelines and finalized state variables payload.
              </CardDescription>
            </div>
            {/* View selector tabs */}
            <div className="flex border border-slate-200 rounded-lg overflow-hidden p-0.5 bg-slate-50 text-[11px] font-semibold">
              <button
                onClick={() => setActiveTraceTab('timeline')}
                className={`px-3 py-1.5 rounded-md transition-all ${
                  activeTraceTab === 'timeline'
                    ? 'bg-white shadow-sm font-bold text-teal-600'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                Timeline
              </button>
              <button
                onClick={() => setActiveTraceTab('timings')}
                className={`px-3 py-1.5 rounded-md transition-all ${
                  activeTraceTab === 'timings'
                    ? 'bg-white shadow-sm font-bold text-teal-600'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                Timings
              </button>
              <button
                onClick={() => setActiveTraceTab('json')}
                className={`px-3 py-1.5 rounded-md transition-all ${
                  activeTraceTab === 'json'
                    ? 'bg-white shadow-sm font-bold text-teal-600'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                State JSON
              </button>
            </div>
          </CardHeader>
          <CardContent className="p-4 bg-slate-50 rounded-b-lg">
            {activeTraceTab === 'timeline' && (
              <div className="py-2.5 space-y-4">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Execution Path Timeline</h4>
                <div className="flex flex-col md:flex-row items-start md:items-center gap-3 md:gap-4 overflow-x-auto py-2">
                  {testRunMutation.data.trace.map((nodeName, idx) => (
                    <div key={idx} className="flex items-center gap-3 md:gap-4">
                      <div className="flex flex-col items-center border border-slate-200 bg-white p-3 rounded-lg shadow-sm font-mono text-center min-w-[130px] relative">
                        <span className="text-[10px] text-slate-400 font-semibold block uppercase">Step #{idx + 1}</span>
                        <span className="font-bold text-xs text-slate-700 block mt-1">{nodeName}</span>
                      </div>
                      {idx < testRunMutation.data.trace.length - 1 && (
                        <span className="text-slate-400 font-black text-lg block rotate-90 md:rotate-0 self-center">➔</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTraceTab === 'timings' && (
              <div className="py-2.5 space-y-3">
                <div className="flex justify-between items-center border-b border-slate-200 pb-2">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Node Performance Execution Times</span>
                  <span className="text-xs font-bold text-teal-700 font-mono bg-teal-50 border border-teal-100 px-2 py-0.5 rounded">
                    Total: {testRunMutation.data.timings.overall?.toFixed(1) || '0.0'}ms
                  </span>
                </div>
                <div className="space-y-2 max-w-xl text-xs font-mono">
                  {Object.entries(testRunMutation.data.timings).map(([nodeName, timeVal]) => {
                    if (nodeName === 'overall') return null
                    const percent = testRunMutation.data.timings.overall ? (timeVal / testRunMutation.data.timings.overall) * 100 : 0
                    return (
                      <div key={nodeName} className="space-y-1 bg-white p-2.5 rounded-lg border border-slate-200">
                        <div className="flex justify-between">
                          <span className="font-semibold text-slate-700">{nodeName}</span>
                          <span className="font-semibold text-slate-500">{timeVal.toFixed(1)}ms</span>
                        </div>
                        <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                          <div className="bg-teal-500 h-full rounded-full" style={{ width: `${percent}%` }} />
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {activeTraceTab === 'json' && (
              <div className="space-y-2 py-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Finalized State Variables JSON</span>
                  <span className="text-[10px] text-slate-400 font-mono">Output State Dict</span>
                </div>
                <pre className="p-4 bg-slate-900 border border-slate-950 rounded-lg text-[11px] font-mono text-slate-300 overflow-x-auto max-h-[300px] leading-relaxed shadow-inner">
                  {JSON.stringify(testRunMutation.data.state, null, 2)}
                </pre>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

function DrugLookupPlaygroundView() {
  const [lookupName, setLookupName] = useState('')
  const [normalizeInput, setNormalizeInput] = useState('')
  const [lookupResult, setLookupResult] = useState<any>(null)
  const [normalizedOutput, setNormalizedOutput] = useState<string>('')
  
  const lookupMutation = useDrugLookup()
  const normalizeMutation = useDrugNormalize()
  const { data: stats, refetch: refetchStats } = useDrugStatistics()

  const handleLookup = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!lookupName.trim()) return
    try {
      const res = await lookupMutation.mutateAsync(lookupName)
      setLookupResult(res)
    } catch (err) {
      setLookupResult(null)
    }
  }

  const handleNormalize = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!normalizeInput.trim()) return
    try {
      const res = await normalizeMutation.mutateAsync(normalizeInput)
      setNormalizedOutput(res.normalized_name)
    } catch (err) {
      setNormalizedOutput('')
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in duration-300">
      <div className="lg:col-span-2 space-y-6">
        {/* Drug Lookup Card */}
        <Card className="border-slate-200 shadow-md bg-white">
          <CardHeader className="border-b border-slate-100 bg-slate-50/50">
            <CardTitle className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <Search className="h-5 w-5 text-teal-600" />
              Drug Master Lookup
            </CardTitle>
            <CardDescription>
              Query medications by name or alias to resolve their standard names and aliases in the MongoDB master catalog.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <form onSubmit={handleLookup} className="flex gap-3 mb-6">
              <Input
                placeholder="Enter drug name or alias (e.g. Paracetamol, Acetaminophen, Advil)..."
                value={lookupName}
                onChange={(e) => setLookupName(e.target.value)}
                disabled={lookupMutation.isPending}
                className="border-slate-200 focus:border-teal-500 focus:ring-teal-500"
              />
              <Button
                type="submit"
                disabled={!lookupName.trim() || lookupMutation.isPending}
                className="bg-teal-600 hover:bg-teal-700 text-white font-semibold"
              >
                {lookupMutation.isPending ? <RefreshCw className="h-4 w-4 animate-spin" /> : "Lookup"}
              </Button>
            </form>

            {lookupMutation.isPending && (
              <div className="flex justify-center py-8">
                <RefreshCw className="h-8 w-8 animate-spin text-teal-500" />
              </div>
            )}

            {lookupMutation.isError && (
              <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
                Error looking up drug. Please try again.
              </div>
            )}

            {lookupResult && (
              <div className="space-y-4 animate-in slide-in-from-top-2 duration-200">
                <div className={`p-4 rounded-lg border flex items-start gap-3 ${
                  lookupResult.exists 
                    ? 'bg-teal-50/50 border-teal-100 text-teal-900' 
                    : 'bg-amber-50/50 border-amber-100 text-amber-900'
                }`}>
                  {lookupResult.exists ? (
                    <CheckCircle2 className="h-5 w-5 text-teal-600 mt-0.5 flex-shrink-0" />
                  ) : (
                    <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
                  )}
                  <div>
                    <h4 className="font-semibold text-sm">
                      {lookupResult.exists ? "Drug Found in Master Catalog" : "Drug Not Found"}
                    </h4>
                    <p className="text-xs mt-1 text-slate-500">
                      Query normalized to <code className="font-mono bg-slate-100 px-1 py-0.5 rounded text-slate-800">{lookupResult.normalized_name}</code>
                    </p>
                  </div>
                </div>

                {lookupResult.exists && lookupResult.matched_drug && (
                  <Card className="border-slate-100 shadow-sm">
                    <CardContent className="p-4 space-y-3 text-sm">
                      <div className="grid grid-cols-3 gap-2 py-1 border-b border-slate-50">
                        <span className="text-slate-400 font-medium">Canonical Name:</span>
                        <span className="col-span-2 font-semibold text-slate-800">{lookupResult.matched_drug.drug_name}</span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 py-1 border-b border-slate-50">
                        <span className="text-slate-400 font-medium">Normalized:</span>
                        <span className="col-span-2 font-mono text-xs text-slate-600">{lookupResult.matched_drug.normalized_name}</span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 py-1 border-b border-slate-50">
                        <span className="text-slate-400 font-medium">Aliases:</span>
                        <span className="col-span-2 text-slate-600">
                          {lookupResult.matched_drug.aliases.length > 0 
                            ? lookupResult.matched_drug.aliases.join(', ') 
                            : <span className="text-slate-400 italic">None</span>
                          }
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 py-1 border-b border-slate-50">
                        <span className="text-slate-400 font-medium">Resolution Score:</span>
                        <span className="col-span-2 flex items-center gap-1.5">
                          <span className={`px-2 py-0.5 rounded-full text-[11px] font-bold ${
                            lookupResult.confidence === 1.0 
                              ? 'bg-teal-100 text-teal-800' 
                              : 'bg-blue-100 text-blue-800'
                          }`}>
                            {lookupResult.confidence === 1.0 ? "Exact Match (1.0)" : "Alias Match (0.9)"}
                          </span>
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 py-1 border-b border-slate-50">
                        <span className="text-slate-400 font-medium">Data Source:</span>
                        <span className="col-span-2 text-slate-600 font-medium uppercase text-xs">{lookupResult.matched_drug.source_dataset}</span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 py-1">
                        <span className="text-slate-400 font-medium">Lookup Source:</span>
                        <span className="col-span-2 text-slate-600 font-medium capitalize text-xs">{lookupResult.lookup_source}</span>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Normalization Sandbox Card */}
        <Card className="border-slate-200 shadow-md bg-white">
          <CardHeader className="border-b border-slate-100 bg-slate-50/50">
            <CardTitle className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <Sliders className="h-5 w-5 text-indigo-600" />
              Normalization Sandbox
            </CardTitle>
            <CardDescription>
              Test the deterministic drug normalization rules (lowercase, remove dosage, strength, form words, extra spaces).
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <form onSubmit={handleNormalize} className="flex gap-3 mb-4">
              <Input
                placeholder="Enter raw medication string (e.g. Paracetamol 650mg Tablet)..."
                value={normalizeInput}
                onChange={(e) => setNormalizeInput(e.target.value)}
                disabled={normalizeMutation.isPending}
                className="border-slate-200 focus:border-indigo-500 focus:ring-indigo-500"
              />
              <Button
                type="submit"
                disabled={!normalizeInput.trim() || normalizeMutation.isPending}
                className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold"
              >
                {normalizeMutation.isPending ? <RefreshCw className="h-4 w-4 animate-spin" /> : "Normalize"}
              </Button>
            </form>

            {normalizedOutput && (
              <div className="mt-4 p-4 rounded-lg bg-indigo-50/50 border border-indigo-100 flex items-center justify-between animate-in slide-in-from-top-2 duration-200">
                <div>
                  <span className="text-xs text-indigo-500 font-medium uppercase tracking-wider block">Normalized Output</span>
                  <span className="font-mono font-bold text-indigo-900 mt-1 block">{normalizedOutput}</span>
                </div>
                <div className="text-[10px] text-indigo-500 font-medium bg-white border border-indigo-200/50 px-2 py-1 rounded-full shadow-sm">
                  Deterministic Regex Rule Set
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Telemetry and Sidebar */}
      <div className="space-y-6">
        {/* Latency card */}
        <Card className="border-slate-200 shadow bg-gradient-to-br from-teal-50 to-white hover:shadow-md transition-all">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Avg Resolution Latency</p>
                <h3 className="text-3xl font-extrabold text-teal-900 mt-1">
                  {stats?.avg_latency_ms ?? 0} <span className="text-lg font-semibold text-teal-600">ms</span>
                </h3>
              </div>
              <div className="p-3 rounded-full bg-teal-100 text-teal-700">
                <Clock className="h-6 w-6" />
              </div>
            </div>
            <div className="mt-3 text-xs text-slate-400 flex items-center gap-1">
              <Activity className="h-3 w-3 text-teal-500" />
              Running average drug lookup resolution latency
            </div>
          </CardContent>
        </Card>

        {/* Cache Performance Card */}
        <Card className="border-slate-200 shadow-md bg-white">
          <CardHeader className="pb-3 border-b border-slate-100">
            <CardTitle className="text-sm font-semibold text-slate-700 flex items-center gap-2">
              <Layers className="h-4 w-4 text-slate-500" />
              Cache Telemetry
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4 space-y-3 text-xs text-slate-600">
            <div className="flex justify-between items-center">
              <span>Total Lookups:</span>
              <span className="font-semibold text-slate-800">{stats?.total_lookups ?? 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Cache Hits:</span>
              <span className="font-semibold text-teal-600">{stats?.cache_hits ?? 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Cache Misses:</span>
              <span className="font-semibold text-amber-600">{stats?.cache_misses ?? 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Cache Hit Ratio:</span>
              <span className="font-bold text-slate-800">
                {stats?.cache_hit_ratio ? `${(stats.cache_hit_ratio * 100).toFixed(1)}%` : "0.0%"}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span>Total Normalizations:</span>
              <span className="font-semibold text-slate-800">{stats?.normalization_count ?? 0}</span>
            </div>
          </CardContent>
        </Card>

        {/* Warnings Card */}
        {stats && stats.unknown_drug_count > 0 && (
          <Card className="border-amber-200 bg-amber-50/50 shadow-sm">
            <CardContent className="p-4 flex gap-3 text-xs text-amber-900">
              <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0" />
              <div>
                <h5 className="font-semibold">Unknown Lookup Warnings</h5>
                <p className="mt-1 text-slate-500 leading-relaxed">
                  Detected <span className="font-bold text-amber-800">{stats.unknown_drug_count}</span> lookup failures in this session. Patients submitting unrecognized drug names will fail deterministic lookup and interaction screening.
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

function DrugInteractionPlaygroundView() {
  const [medList, setMedList] = useState<string[]>(['Warfarin', 'Aspirin', 'Metformin'])
  const [newMed, setNewMed] = useState('')
  const [checkResult, setCheckResult] = useState<any>(null)
  
  const checkMutation = useCheckDrugInteractions()
  const { data: stats, refetch: refetchStats } = useDrugInteractionsStatistics()

  const handleAddMed = (e: React.FormEvent) => {
    e.preventDefault()
    if (newMed.trim() && !medList.includes(newMed.trim())) {
      setMedList([...medList, newMed.trim()])
      setNewMed('')
    }
  }

  const handleRemoveMed = (index: number) => {
    setMedList(medList.filter((_, i) => i !== index))
  }

  const handleCheck = async () => {
    if (medList.length === 0) return
    try {
      const res = await checkMutation.mutateAsync(medList)
      setCheckResult(res)
      refetchStats()
    } catch (err) {
      setCheckResult(null)
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in duration-300">
      <div className="lg:col-span-2 space-y-6">
        {/* Medication Editor Card */}
        <Card className="border-slate-200 shadow-md bg-white">
          <CardHeader className="border-b border-slate-100 bg-slate-50/50">
            <CardTitle className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <Sliders className="h-5 w-5 text-teal-600" />
              Medication List Editor
            </CardTitle>
            <CardDescription>
              Build the list of drugs to analyze for potential drug-drug interactions.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-6 space-y-4">
            <form onSubmit={handleAddMed} className="flex gap-2">
              <Input
                placeholder="Type medication name (e.g. Warfarin, Aspirin)..."
                value={newMed}
                onChange={(e) => setNewMed(e.target.value)}
                className="border-slate-200 focus:border-teal-500 focus:ring-teal-500"
              />
              <Button type="submit" variant="outline" className="border-slate-200 text-slate-700 hover:bg-slate-50 font-medium">
                Add Medication
              </Button>
            </form>

            <div className="flex flex-wrap gap-2 py-2">
              {medList.length === 0 ? (
                <span className="text-sm text-slate-400 italic">No medications added yet.</span>
              ) : (
                medList.map((med, index) => (
                  <div key={index} className="flex items-center gap-1.5 bg-slate-100 border border-slate-200 rounded-full pl-3 pr-1 py-1 text-sm text-slate-800 animate-in zoom-in-95 duration-100">
                    <span>{med}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveMed(index)}
                      className="h-5 w-5 rounded-full hover:bg-slate-200 text-slate-500 hover:text-slate-700 flex items-center justify-center font-bold text-xs"
                    >
                      ×
                    </button>
                  </div>
                ))
              )}
            </div>

            <div className="flex justify-end pt-2 border-t border-slate-100">
              <Button
                onClick={handleCheck}
                disabled={medList.length === 0 || checkMutation.isPending}
                className="bg-teal-600 hover:bg-teal-700 text-white font-semibold shadow"
              >
                {checkMutation.isPending ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Checking Interactions...
                  </>
                ) : (
                  <>
                    <Zap className="h-4 w-4 mr-2" />
                    Check Interactions
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Results Panel */}
        {checkResult && (
          <Card className="border-slate-200 shadow-md bg-white overflow-hidden animate-in slide-in-from-top-2 duration-200">
            <CardHeader className="border-b border-slate-100 bg-slate-50/50 flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-lg font-semibold text-slate-800">
                  Interaction Evaluation Report
                </CardTitle>
                <CardDescription>
                  Deterministic matching results from MongoDB `drug_interactions` collection.
                </CardDescription>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${
                checkResult.severity === 'HIGH' ? 'bg-red-100 text-red-800 border border-red-200' :
                checkResult.severity === 'MEDIUM' ? 'bg-amber-100 text-amber-800 border border-amber-200' :
                checkResult.severity === 'LOW' ? 'bg-yellow-100 text-yellow-800 border border-yellow-200' :
                checkResult.severity === 'UNKNOWN' ? 'bg-slate-100 text-slate-800 border border-slate-200' :
                'bg-teal-50 text-teal-800 border border-teal-100'
              }`}>
                Overall Severity: {checkResult.severity}
              </span>
            </CardHeader>
            <CardContent className="pt-6 space-y-6">
              {/* Recommendations */}
              <div className="p-4 rounded-lg bg-slate-50 border border-slate-100">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Deterministic Action Plan</h4>
                <ul className="list-disc pl-5 space-y-1 text-sm text-slate-700 font-medium">
                  {checkResult.recommendations.map((rec: string, i: number) => (
                    <li key={i}>{rec}</li>
                  ))}
                </ul>
              </div>

              {/* Interactions Table */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Matched Interaction Pairs</h4>
                {checkResult.detected_interactions.length === 0 ? (
                  <div className="p-8 border border-dashed rounded-lg text-center text-slate-400 text-sm">
                    No active drug-drug interactions detected between these medications.
                  </div>
                ) : (
                  <div className="border border-slate-100 rounded-lg overflow-hidden">
                    <table className="w-full text-left text-sm text-slate-700">
                      <thead className="bg-slate-50 text-xs font-semibold text-slate-600 border-b border-slate-100">
                        <tr>
                          <th className="px-4 py-2">Medication A</th>
                          <th className="px-4 py-2">Medication B</th>
                          <th className="px-4 py-2">Severity</th>
                          <th className="px-4 py-2">Description</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-50 bg-white">
                        {checkResult.detected_interactions.map((pair: any, i: number) => (
                          <tr key={i} className="hover:bg-slate-50/50">
                            <td className="px-4 py-3 font-medium text-slate-900">
                              {pair.drug_a} <span className="block text-[10px] text-slate-400 font-mono">{pair.drug_a_normalized}</span>
                            </td>
                            <td className="px-4 py-3 font-medium text-slate-900">
                              {pair.drug_b} <span className="block text-[10px] text-slate-400 font-mono">{pair.drug_b_normalized}</span>
                            </td>
                            <td className="px-4 py-3">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                pair.severity === 'HIGH' ? 'bg-red-50 text-red-700' :
                                pair.severity === 'MEDIUM' ? 'bg-amber-50 text-amber-700' :
                                pair.severity === 'LOW' ? 'bg-yellow-50 text-yellow-700' :
                                'bg-slate-50 text-slate-700'
                              }`}>
                                {pair.severity}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-xs text-slate-600 leading-relaxed max-w-[250px] truncate" title={pair.description}>
                              {pair.description}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Latency check */}
              <div className="text-right text-[10px] text-slate-400 font-mono">
                Evaluation latency: {checkResult.latency_ms} ms
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Telemetry and Stats Sidebar */}
      <div className="space-y-6">
        {/* Latency card */}
        <Card className="border-slate-200 shadow bg-gradient-to-br from-teal-50 to-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Avg Check Latency</p>
                <h3 className="text-3xl font-extrabold text-teal-900 mt-1">
                  {stats?.interaction_avg_latency_ms ?? 0} <span className="text-lg font-semibold text-teal-600">ms</span>
                </h3>
              </div>
              <div className="p-3 rounded-full bg-teal-100 text-teal-700">
                <Clock className="h-6 w-6" />
              </div>
            </div>
            <div className="mt-3 text-xs text-slate-400 flex items-center gap-1">
              <Activity className="h-3 w-3 text-teal-500" />
              Running latency of interaction checks
            </div>
          </CardContent>
        </Card>

        {/* Evaluation Summary Card */}
        <Card className="border-slate-200 shadow-md bg-white">
          <CardHeader className="pb-3 border-b border-slate-100">
            <CardTitle className="text-sm font-semibold text-slate-700 flex items-center gap-2">
              <Layers className="h-4 w-4 text-slate-500" />
              Execution Statistics
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4 space-y-3 text-xs text-slate-600">
            <div className="flex justify-between items-center">
              <span>Total Check Requests:</span>
              <span className="font-semibold text-slate-800">{stats?.interaction_checks ?? 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Pairs Evaluated:</span>
              <span className="font-semibold text-slate-800">{stats?.pairs_evaluated ?? 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Total Master Lookups:</span>
              <span className="font-semibold text-slate-800">{stats?.total_lookups ?? 0}</span>
            </div>
          </CardContent>
        </Card>

        {/* Severity Distribution Card */}
        {stats && stats.severity_distribution && (
          <Card className="border-slate-200 shadow-md bg-white">
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-sm font-semibold text-slate-700">
                Severity Profile
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-2">
              {Object.entries(stats.severity_distribution).map(([sev, count]: [string, any]) => (
                <div key={sev} className="space-y-1">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-medium text-slate-600">{sev}</span>
                    <span className="font-semibold text-slate-800">{count}</span>
                  </div>
                  <div className="w-full bg-slate-100 h-1 rounded-full overflow-hidden">
                    <div 
                      className={`h-full rounded-full ${
                        sev === 'HIGH' ? 'bg-red-500' :
                        sev === 'MEDIUM' ? 'bg-amber-500' :
                        sev === 'LOW' ? 'bg-yellow-400' :
                        sev === 'UNKNOWN' ? 'bg-slate-400' : 'bg-teal-500'
                      }`} 
                      style={{ width: `${stats.interaction_checks > 0 ? (count / stats.interaction_checks) * 100 : 0}%` }} 
                    />
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

function MedicationValidationPlaygroundView() {
  const [patientId, setPatientId] = useState('patient-123')
  const [medsList, setMedsList] = useState<string[]>(['Aspirin'])
  const [newMed, setNewMed] = useState('')
  const [validationResult, setValidationResult] = useState<any>(null)

  const validateMutation = useValidateMedications()
  const { data: stats, refetch: refetchStats } = useMedicationValidationStatistics()

  const handleAddMed = (e: React.FormEvent) => {
    e.preventDefault()
    if (newMed.trim() && !medsList.includes(newMed.trim())) {
      setMedsList([...medsList, newMed.trim()])
      setNewMed('')
    }
  }

  const handleRemoveMed = (index: number) => {
    setMedsList(medsList.filter((_, i) => i !== index))
  }

  const handleValidate = async () => {
    if (medsList.length === 0 || !patientId.trim()) return
    try {
      const res = await validateMutation.mutateAsync({
        patient_id: patientId.trim(),
        incoming_medications: medsList
      })
      setValidationResult(res)
      refetchStats()
    } catch (err) {
      setValidationResult(null)
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in duration-300">
      <div className="lg:col-span-2 space-y-6">
        <Card className="border-slate-200 shadow-md bg-white">
          <CardHeader className="border-b border-slate-100 bg-slate-50/50">
            <CardTitle className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-teal-600" />
              Medication Validation Pipeline
            </CardTitle>
            <CardDescription>
              Validate incoming medications against a patient's active drug profile and audit interaction triggers.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-6 space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700">Patient Identifier</label>
              <Input
                placeholder="Enter Patient ID (e.g. patient-123)..."
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                className="border-slate-200 focus:border-teal-500 focus:ring-teal-500"
              />
            </div>

            <div className="space-y-2 pt-2">
              <label className="text-sm font-semibold text-slate-700">Incoming Medications to Validate</label>
              <form onSubmit={handleAddMed} className="flex gap-2">
                <Input
                  placeholder="Type medication name (e.g. Aspirin, Warfarin)..."
                  value={newMed}
                  onChange={(e) => setNewMed(e.target.value)}
                  className="border-slate-200 focus:border-teal-500 focus:ring-teal-500"
                />
                <Button type="submit" variant="outline" className="border-slate-200 text-slate-700 hover:bg-slate-50 font-medium">
                  Add
                </Button>
              </form>
            </div>

            <div className="flex flex-wrap gap-2 py-2">
              {medsList.length === 0 ? (
                <span className="text-sm text-slate-400 italic">No incoming medications added yet.</span>
              ) : (
                medsList.map((med, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-800 border border-slate-200"
                  >
                    {med}
                    <button
                      type="button"
                      onClick={() => handleRemoveMed(idx)}
                      className="text-slate-400 hover:text-red-500 transition-colors"
                    >
                      &times;
                    </button>
                  </span>
                ))
              )}
            </div>

            <div className="pt-4 border-t border-slate-100 flex justify-end">
              <Button
                onClick={handleValidate}
                disabled={medsList.length === 0 || !patientId.trim() || validateMutation.isPending}
                className="bg-teal-600 hover:bg-teal-700 text-white font-medium shadow-sm transition-all"
              >
                {validateMutation.isPending ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Validating...
                  </>
                ) : (
                  <>
                    <Zap className="h-4 w-4 mr-2" />
                    Run Validation Pipeline
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {validationResult && (
          <Card className="border-slate-200 shadow-md bg-white overflow-hidden animate-in slide-in-from-bottom-4 duration-300">
            <CardHeader className="border-b border-slate-100 bg-slate-50/50">
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle className="text-lg font-semibold text-slate-800">
                    Validation Results
                  </CardTitle>
                  <CardDescription>
                    Pipeline evaluation outputs and clinician advisory.
                  </CardDescription>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">
                    Latency: {validationResult.latency_ms} ms
                  </span>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
                      validationResult.decision === 'ALLOW'
                        ? 'bg-teal-100 text-teal-800 border border-teal-200'
                        : validationResult.decision === 'WARNING'
                        ? 'bg-amber-100 text-amber-800 border border-amber-200'
                        : 'bg-red-100 text-red-800 border border-red-200'
                    }`}
                  >
                    {validationResult.decision}
                  </span>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-6 space-y-6">
              {/* Collected active medications */}
              <div className="space-y-2">
                <h4 className="text-sm font-semibold text-slate-700">Collected Active Patient Medications:</h4>
                <div className="flex flex-wrap gap-1.5">
                  {validationResult.collected_medications?.length === 0 ? (
                    <span className="text-sm text-slate-400 italic">No existing medications active in patient memory.</span>
                  ) : (
                    validationResult.collected_medications?.map((med: string, idx: number) => (
                      <span key={idx} className="px-2.5 py-1 rounded-md text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200 font-mono">
                        {med}
                      </span>
                    ))
                  )}
                </div>
              </div>

              {/* Recommendations list */}
              {validationResult.recommendations?.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold text-slate-700">Clinician Advisory Recommendations:</h4>
                  <ul className="space-y-1.5">
                    {validationResult.recommendations.map((rec: string, idx: number) => (
                      <li key={idx} className="text-sm text-slate-600 flex items-start gap-2">
                        <CheckCircle2 className="h-4 w-4 text-teal-500 shrink-0 mt-0.5" />
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Interaction Details Table */}
              <div className="space-y-3 pt-2">
                <h4 className="text-sm font-semibold text-slate-700">Detected Interaction Details:</h4>
                {validationResult.detected_interactions?.length === 0 ? (
                  <div className="p-4 rounded-lg bg-teal-50 text-teal-800 text-sm border border-teal-100 text-center font-medium">
                    No potential safety conflicts or drug-drug interactions detected.
                  </div>
                ) : (
                  <div className="border border-slate-200 rounded-lg overflow-hidden">
                    <table className="w-full text-left text-sm">
                      <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
                        <tr>
                          <th className="p-3">Medication A</th>
                          <th className="p-3">Medication B</th>
                          <th className="p-3">Severity</th>
                          <th className="p-3">Clinical Description</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {validationResult.detected_interactions.map((pair: any, idx: number) => (
                          <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                            <td className="p-3 font-medium text-slate-800 font-mono">
                              {pair.drug_a}
                              <span className="block text-[10px] text-slate-400">{pair.drug_a_normalized}</span>
                            </td>
                            <td className="p-3 font-medium text-slate-800 font-mono">
                              {pair.drug_b}
                              <span className="block text-[10px] text-slate-400">{pair.drug_b_normalized}</span>
                            </td>
                            <td className="p-3">
                              <span
                                className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                                  pair.severity === 'HIGH'
                                    ? 'bg-red-100 text-red-800'
                                    : pair.severity === 'MEDIUM'
                                    ? 'bg-amber-100 text-amber-800'
                                    : pair.severity === 'LOW'
                                    ? 'bg-yellow-100 text-yellow-800'
                                    : 'bg-slate-100 text-slate-800'
                                }`}
                              >
                                {pair.severity}
                              </span>
                            </td>
                            <td className="p-3 text-slate-600 leading-relaxed text-xs">
                              {pair.description}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      <div className="space-y-6">
        <Card className="border-slate-200 shadow-md bg-white">
          <CardHeader className="pb-3 border-b border-slate-100">
            <div className="flex justify-between items-center">
              <CardTitle className="text-sm font-semibold text-slate-700">
                Pipeline Telemetry
              </CardTitle>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => refetchStats()}
                className="h-8 w-8 text-slate-400 hover:text-slate-600"
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="pt-4 space-y-4 text-sm text-slate-600">
            <div className="flex justify-between items-center">
              <span>Validation Queries:</span>
              <span className="font-semibold text-slate-800">{stats?.validation_checks ?? 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Average Latency:</span>
              <span className="font-semibold text-slate-800">
                {stats?.validation_avg_latency_ms ? `${stats.validation_avg_latency_ms} ms` : '0 ms'}
              </span>
            </div>
            <div className="pt-2 border-t border-slate-100 space-y-2">
              <h5 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Decision Breakdown</h5>
              <div className="flex justify-between items-center text-xs">
                <span>ALLOW:</span>
                <span className="font-semibold text-teal-600">{stats?.allow_decisions ?? 0}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span>WARNING:</span>
                <span className="font-semibold text-amber-600">{stats?.warning_decisions ?? 0}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span>BLOCK:</span>
                <span className="font-semibold text-red-600">{stats?.blocked_decisions ?? 0}</span>
              </div>
            </div>
            <div className="pt-2 border-t border-slate-100 space-y-2">
              <h5 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Trigger Sources</h5>
              <div className="flex justify-between items-center text-xs">
                <span>Reminder Agent:</span>
                <span className="font-semibold text-slate-800">{stats?.reminder_validations ?? 0}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span>Prescription API:</span>
                <span className="font-semibold text-slate-800">{stats?.prescription_validations ?? 0}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span>Report Sync:</span>
                <span className="font-semibold text-slate-800">{stats?.report_validations ?? 0}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span>Patient Memory Summary:</span>
                <span className="font-semibold text-slate-800">{stats?.patient_memory_validations ?? 0}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span>Other:</span>
                <span className="font-semibold text-slate-800">{stats?.other_validations ?? 0}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
function DrugAIExplanationPlaygroundView() {
  const [patientId, setPatientId] = useState('patient-123')
  const [medsList, setMedsList] = useState<string[]>(['Aspirin', 'Warfarin'])
  const [newMed, setNewMed] = useState('')
  const [explainResult, setExplainResult] = useState<any>(null)

  const explainMutation = useExplainDrugSafety()
  const { data: stats, refetch: refetchStats } = useDrugAISafetyStatistics()

  const handleAddMed = (e: React.FormEvent) => {
    e.preventDefault()
    if (newMed.trim() && !medsList.includes(newMed.trim())) {
      setMedsList([...medsList, newMed.trim()])
      setNewMed('')
    }
  }

  const handleRemoveMed = (index: number) => {
    setMedsList(medsList.filter((_, i) => i !== index))
  }

  const handleExplain = async () => {
    if (medsList.length === 0 || !patientId.trim()) return
    try {
      const res = await explainMutation.mutateAsync({
        patient_id: patientId.trim(),
        incoming_medications: medsList
      })
      setExplainResult(res)
      refetchStats()
    } catch (err) {
      setExplainResult(null)
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in duration-300">
      <div className="lg:col-span-2 space-y-6">
        <Card className="border-slate-200 shadow-md bg-white">
          <CardHeader className="border-b border-slate-100 bg-slate-50/50">
            <CardTitle className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <Brain className="h-5 w-5 text-teal-600 animate-pulse" />
              Drug AI Explanation Engine
            </CardTitle>
            <CardDescription>
              Validate safety metrics and generate AI-driven narrative safety warnings for patients and clinicians.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-6 space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700">Patient Identifier</label>
              <Input
                placeholder="Enter Patient ID (e.g. patient-123)..."
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                className="border-slate-200 focus:border-teal-500 focus:ring-teal-500"
              />
            </div>

            <div className="space-y-2 pt-2">
              <label className="text-sm font-semibold text-slate-700">Incoming Medications list</label>
              <form onSubmit={handleAddMed} className="flex gap-2">
                <Input
                  placeholder="Type medication name (e.g. Aspirin, Warfarin, Metformin)..."
                  value={newMed}
                  onChange={(e) => setNewMed(e.target.value)}
                  className="border-slate-200 focus:border-teal-500 focus:ring-teal-500"
                />
                <Button type="submit" variant="outline" className="border-slate-200 text-slate-700 hover:bg-slate-50 font-medium">
                  Add Medication
                </Button>
              </form>
            </div>

            <div className="flex flex-wrap gap-2 py-2">
              {medsList.length === 0 ? (
                <span className="text-sm text-slate-400 italic">No medications selected.</span>
              ) : (
                medsList.map((med, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-800 border border-slate-200"
                  >
                    {med}
                    <button
                      type="button"
                      onClick={() => handleRemoveMed(idx)}
                      className="text-slate-400 hover:text-red-500 transition-colors"
                    >
                      &times;
                    </button>
                  </span>
                ))
              )}
            </div>

            <div className="pt-4 border-t border-slate-100 flex justify-end">
              <Button
                onClick={handleExplain}
                disabled={medsList.length === 0 || !patientId.trim() || explainMutation.isPending}
                className="bg-teal-600 hover:bg-teal-700 text-white font-medium shadow-sm transition-all"
              >
                {explainMutation.isPending ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Generating Explanations...
                  </>
                ) : (
                  <>
                    <Zap className="h-4 w-4 mr-2" />
                    Generate AI Safety Explanations
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {explainResult && (
          <Card className="border-slate-200 shadow-md bg-white overflow-hidden animate-in slide-in-from-bottom-4 duration-300">
            <CardHeader className="border-b border-slate-100 bg-slate-50/50">
              <div className="flex flex-wrap justify-between items-center gap-4">
                <div>
                  <CardTitle className="text-lg font-semibold text-slate-800">
                    Clinical Narrative & Safety Advisory
                  </CardTitle>
                  <CardDescription>
                    AI-powered narrative safety check results.
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  {explainResult.fallback_used && (
                    <span className="px-3 py-1.5 rounded-full text-xs font-bold uppercase bg-amber-100 text-amber-800 border border-amber-200 flex items-center gap-1">
                      <AlertTriangle className="h-3.5 w-3.5" />
                      Fallback Used
                    </span>
                  )}
                  <span
                    className={`px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                      explainResult.severity === 'HIGH'
                        ? 'bg-red-100 text-red-800 border border-red-200'
                        : explainResult.severity === 'MEDIUM'
                        ? 'bg-amber-100 text-amber-800 border border-amber-200'
                        : 'bg-teal-100 text-teal-800 border border-teal-200'
                    }`}
                  >
                    Severity: {explainResult.severity}
                  </span>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-6 space-y-6">
              {/* Summary Sentence */}
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
                <h4 className="text-xs font-semibold uppercase text-slate-400 tracking-wider">Summary</h4>
                <p className="mt-1.5 text-sm font-medium text-slate-800 leading-relaxed">
                  {explainResult.summary}
                </p>
              </div>

              {/* Patient Explanation */}
              <div className="space-y-2">
                <h4 className="text-xs font-semibold uppercase text-teal-600 tracking-wider">Patient Explanation</h4>
                <div className="text-sm text-slate-700 whitespace-pre-line leading-relaxed bg-teal-50/20 border border-teal-100/50 p-4 rounded-lg">
                  {explainResult.patient_explanation}
                </div>
              </div>

              {/* Clinical Doctor Explanation */}
              <div className="space-y-2">
                <h4 className="text-xs font-semibold uppercase text-violet-600 tracking-wider">Doctor Clinical Details</h4>
                <div className="text-sm text-slate-700 whitespace-pre-line leading-relaxed bg-violet-50/20 border border-violet-100/50 p-4 rounded-lg font-mono text-[13px]">
                  {explainResult.doctor_explanation}
                </div>
              </div>

              {/* Precautions */}
              <div className="space-y-2">
                <h4 className="text-xs font-semibold uppercase text-amber-600 tracking-wider">Lifestyle & Clinical Precautions</h4>
                <div className="text-sm text-slate-700 whitespace-pre-line leading-relaxed bg-amber-50/20 border border-amber-100/50 p-4 rounded-lg">
                  {explainResult.precautions}
                </div>
              </div>

              {/* Recommendations */}
              {explainResult.deterministic_recommendation?.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold uppercase text-slate-400 tracking-wider">Deterministic Clinical Advisory</h4>
                  <ul className="space-y-1.5">
                    {explainResult.deterministic_recommendation.map((rec: string, idx: number) => (
                      <li key={idx} className="text-sm text-slate-600 flex items-start gap-2">
                        <CheckCircle2 className="h-4 w-4 text-teal-500 shrink-0 mt-0.5" />
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      <div className="space-y-6">
        <Card className="border-slate-200 shadow-md bg-white">
          <CardHeader className="pb-3 border-b border-slate-100">
            <div className="flex justify-between items-center">
              <CardTitle className="text-sm font-semibold text-slate-700">
                Drug Safety AI Telemetry
              </CardTitle>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => refetchStats()}
                className="h-8 w-8 text-slate-400 hover:text-slate-600"
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="pt-4 space-y-4 text-sm text-slate-600">
            <div className="flex justify-between items-center">
              <span>Total Requests:</span>
              <span className="font-semibold text-slate-800">{stats?.explanation_requests ?? 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Successful Runs:</span>
              <span className="font-semibold text-slate-800">{stats?.successful_generations ?? 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Fallback Executions:</span>
              <span className="font-semibold text-amber-600">{stats?.fallback_executions ?? 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Average Generation Latency:</span>
              <span className="font-semibold text-slate-800">
                {stats?.avg_latency_ms ? `${stats.avg_latency_ms} ms` : '0 ms'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span>Estimated Cost:</span>
              <span className="font-semibold text-teal-600">
                {stats?.estimated_cost ? `$${stats.estimated_cost.toFixed(6)}` : '$0.00'}
              </span>
            </div>

            <div className="pt-2 border-t border-slate-100 space-y-2">
              <h5 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Token Totals</h5>
              <div className="flex justify-between items-center text-xs">
                <span>Prompt Tokens:</span>
                <span className="font-semibold text-slate-800">{stats?.prompt_tokens ?? 0}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span>Completion Tokens:</span>
                <span className="font-semibold text-slate-800">{stats?.completion_tokens ?? 0}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span>Total Tokens:</span>
                <span className="font-semibold text-slate-800">{stats?.total_tokens ?? 0}</span>
              </div>
            </div>

            {stats && stats.model_usage && Object.keys(stats.model_usage).length > 0 && (
              <div className="pt-2 border-t border-slate-100 space-y-2">
                <h5 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Model Distribution</h5>
                {Object.entries(stats.model_usage).map(([model, count]) => (
                  <div key={model} className="flex justify-between items-center text-xs">
                    <span className="font-mono text-[10px]">{model}:</span>
                    <span className="font-semibold">{count} runs</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}


function AIPlaygroundContent() {
  const [activeTab, setActiveTab] = useState<'llm' | 'embeddings' | 'vector' | 'patient-context' | 'integration' | 'indexing' | 'retrieval' | 'context-builder' | 'retrieval-agent' | 'workflow-engine' | 'router-agent' | 'core-agents' | 'healthcare-agents' | 'operations-agents' | 'drug-lookup' | 'drug-interactions' | 'drug-validation' | 'drug-explain'>('llm')

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Sparkles className="h-8 w-8 text-teal-600 animate-pulse" />
            AI Infrastructure Console
          </h1>
          <p className="text-slate-500 mt-1">
            Validate platform AI services connectivity, test vector embeddings, and monitor model latencies.
          </p>
        </div>
        
        {/* Dynamic Health Check Summary Badge based on active tab */}
        {activeTab === 'llm' ? (
          <LLMHealthBadge />
        ) : activeTab === 'embeddings' ? (
          <EmbeddingHealthBadge />
        ) : activeTab === 'vector' ? (
          <VectorHealthBadge />
        ) : activeTab === 'patient-context' ? (
          <PatientContextHealthBadge />
        ) : activeTab === 'indexing' ? (
          <IndexingHealthBadge />
        ) : activeTab === 'retrieval' ? (
          <RetrievalHealthBadge />
        ) : activeTab === 'context-builder' ? (
          <ContextBuilderHealthBadge />
        ) : activeTab === 'retrieval-agent' ? (
          <RetrievalAgentHealthBadge />
        ) : activeTab === 'workflow-engine' ? (
          <GraphHealthSummaryBadge />
        ) : activeTab === 'router-agent' ? (
          <GraphHealthSummaryBadge />
        ) : (
          <IntegrationHealthSummaryBadge />
        )}
      </div>

      {/* Tabs list */}
      <div className="flex border-b border-slate-200 gap-6 overflow-x-auto">
        <button
          onClick={() => setActiveTab('llm')}
          className={`pb-3 font-semibold text-sm transition-all border-b-2 flex items-center gap-2 relative flex-shrink-0 ${
            activeTab === 'llm'
              ? 'border-teal-600 text-teal-600 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Cpu className="h-4 w-4" />
          LLM Playground
        </button>
        <button
          onClick={() => setActiveTab('embeddings')}
          className={`pb-3 font-semibold text-sm transition-all border-b-2 flex items-center gap-2 relative flex-shrink-0 ${
            activeTab === 'embeddings'
              ? 'border-teal-600 text-teal-600 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <FileText className="h-4 w-4" />
          Embeddings Pipeline
        </button>
        <button
          onClick={() => setActiveTab('vector')}
          className={`pb-3 font-semibold text-sm transition-all border-b-2 flex items-center gap-2 relative flex-shrink-0 ${
            activeTab === 'vector'
              ? 'border-teal-600 text-teal-600 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Database className="h-4 w-4" />
          Vector Database
        </button>
        <button
          onClick={() => setActiveTab('patient-context')}
          className={`pb-3 font-semibold text-sm transition-all border-b-2 flex items-center gap-2 relative flex-shrink-0 ${
            activeTab === 'patient-context'
              ? 'border-teal-600 text-teal-600 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Users className="h-4 w-4" />
          Patient Context
        </button>
        <button
          onClick={() => setActiveTab('indexing')}
          className={`pb-3 font-semibold text-sm transition-all border-b-2 flex-shrink-0 flex items-center gap-2 relative ${
            activeTab === 'indexing'
              ? 'border-teal-600 text-teal-600 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Database className="h-4 w-4" />
          Indexing Pipeline
        </button>
        <button
          onClick={() => setActiveTab('retrieval')}
          className={`pb-3 font-semibold text-sm transition-all border-b-2 flex-shrink-0 flex items-center gap-2 relative ${
            activeTab === 'retrieval'
              ? 'border-teal-600 text-teal-600 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Search className="h-4 w-4" />
          Retrieval Engine
        </button>
        <button
          onClick={() => setActiveTab('context-builder')}
          className={`pb-3 font-semibold text-sm transition-all border-b-2 flex-shrink-0 flex items-center gap-2 relative ${
            activeTab === 'context-builder'
              ? 'border-teal-600 text-teal-600 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Layers className="h-4 w-4" />
          Context Builder
        </button>
        <button
          onClick={() => setActiveTab('retrieval-agent')}
          className={`pb-3 font-semibold text-sm transition-all border-b-2 flex-shrink-0 flex items-center gap-2 relative ${
            activeTab === 'retrieval-agent'
              ? 'border-teal-600 text-teal-600 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Zap className="h-4 w-4" />
          Retrieval Agent
        </button>
        <button
          onClick={() => setActiveTab('workflow-engine')}
          className={`pb-3 font-semibold text-sm transition-all border-b-2 flex-shrink-0 flex items-center gap-2 relative ${
            activeTab === 'workflow-engine'
              ? 'border-teal-600 text-teal-600 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Activity className="h-4 w-4" />
          Workflow Engine
        </button>
        <button
          onClick={() => setActiveTab('router-agent')}
          className={`pb-3 font-semibold text-sm transition-all border-b-2 flex-shrink-0 flex items-center gap-2 relative ${
            activeTab === 'router-agent'
              ? 'border-teal-600 text-teal-600 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Sparkles className="h-4 w-4" />
          Router Agent
        </button>
        <button
          onClick={() => setActiveTab('core-agents')}
          className={`pb-3 font-semibold text-sm transition-all border-b-2 flex-shrink-0 flex items-center gap-2 relative ${
            activeTab === 'core-agents'
              ? 'border-teal-600 text-teal-600 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Activity className="h-4 w-4" />
          Core Agents
        </button>
        <button
          onClick={() => setActiveTab('healthcare-agents')}
          className={`pb-3 font-semibold text-sm transition-all border-b-2 flex-shrink-0 flex items-center gap-2 relative ${
            activeTab === 'healthcare-agents'
              ? 'border-teal-600 text-teal-600 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Activity className="h-4 w-4" />
          Healthcare Agents
        </button>
        <button
          onClick={() => setActiveTab('operations-agents')}
          className={`pb-3 font-semibold text-sm transition-all border-b-2 flex-shrink-0 flex items-center gap-2 relative ${
            activeTab === 'operations-agents'
              ? 'border-teal-600 text-teal-600 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Terminal className="h-4 w-4" />
          Operations Agents
        </button>
        <button
          onClick={() => setActiveTab('drug-lookup')}
          className={`pb-3 font-semibold text-sm transition-all border-b-2 flex-shrink-0 flex items-center gap-2 relative ${
            activeTab === 'drug-lookup'
              ? 'border-teal-600 text-teal-600 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Search className="h-4 w-4" />
          Drug Lookup
        </button>
        <button
          onClick={() => setActiveTab('drug-interactions')}
          className={`pb-3 font-semibold text-sm transition-all border-b-2 flex-shrink-0 flex items-center gap-2 relative ${
            activeTab === 'drug-interactions'
              ? 'border-teal-600 text-teal-600 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Zap className="h-4 w-4" />
          Drug Interaction Engine
        </button>
        <button
          onClick={() => setActiveTab('drug-validation')}
          className={`pb-3 font-semibold text-sm transition-all border-b-2 flex-shrink-0 flex items-center gap-2 relative ${
            activeTab === 'drug-validation'
              ? 'border-teal-600 text-teal-600 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Sparkles className="h-4 w-4" />
          Medication Validation
        </button>
        <button
          onClick={() => setActiveTab('drug-explain')}
          className={`pb-3 font-semibold text-sm transition-all border-b-2 flex-shrink-0 flex items-center gap-2 relative ${
            activeTab === 'drug-explain'
              ? 'border-teal-600 text-teal-600 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Brain className="h-4 w-4" />
          Drug AI Explanation
        </button>
        <button
          onClick={() => setActiveTab('integration')}
          className={`pb-3 font-semibold text-sm transition-all border-b-2 flex-shrink-0 flex items-center gap-2 relative ${
            activeTab === 'integration'
              ? 'border-teal-600 text-teal-600 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Settings className="h-4 w-4" />
          Integration Orchestrator
        </button>
      </div>

      {activeTab === 'llm' ? (
        <LLMPlaygroundView />
      ) : activeTab === 'embeddings' ? (
        <EmbeddingsPlaygroundView />
      ) : activeTab === 'vector' ? (
        <VectorPlaygroundView />
      ) : activeTab === 'patient-context' ? (
        <PatientContextPlaygroundView />
      ) : activeTab === 'indexing' ? (
        <IndexingPlaygroundView />
      ) : activeTab === 'retrieval' ? (
        <RetrievalPlaygroundView />
      ) : activeTab === 'context-builder' ? (
        <ContextBuilderPlaygroundView />
      ) : activeTab === 'retrieval-agent' ? (
        <RetrievalAgentPlaygroundView />
      ) : activeTab === 'workflow-engine' ? (
        <WorkflowEngineView />
      ) : activeTab === 'router-agent' ? (
        <RouterAgentView />
      ) : activeTab === 'core-agents' ? (
        <CoreAgentsView />
      ) : activeTab === 'healthcare-agents' ? (
        <HealthcareAgentsView />
      ) : activeTab === 'operations-agents' ? (
        <OperationsAgentsView />
      ) : activeTab === 'drug-lookup' ? (
        <DrugLookupPlaygroundView />
      ) : activeTab === 'drug-interactions' ? (
        <DrugInteractionPlaygroundView />
      ) : activeTab === 'drug-validation' ? (
        <MedicationValidationPlaygroundView />
      ) : activeTab === 'drug-explain' ? (
        <DrugAIExplanationPlaygroundView />
      ) : (
        <IntegrationPlaygroundView />
      )}
    </div>
  )
}

export default function AIPlaygroundPage() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <AIPlaygroundContent />
    </ProtectedRoute>
  )
}
