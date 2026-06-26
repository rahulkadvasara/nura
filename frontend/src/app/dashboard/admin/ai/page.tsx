'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
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
  useDeletePatientDocuments
} from '@/hooks/use-ai'
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
  Layers
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

function AIPlaygroundContent() {
  const [activeTab, setActiveTab] = useState<'llm' | 'embeddings' | 'vector' | 'patient-context' | 'integration' | 'indexing'>('llm')

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
          className={`pb-3 font-semibold text-sm transition-all border-b-2 flex items-center gap-2 relative flex-shrink-0 ${
            activeTab === 'indexing'
              ? 'border-teal-600 text-teal-600 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Database className="h-4 w-4" />
          Indexing Pipeline
        </button>
        <button
          onClick={() => setActiveTab('integration')}
          className={`pb-3 font-semibold text-sm transition-all border-b-2 flex items-center gap-2 relative flex-shrink-0 ${
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
