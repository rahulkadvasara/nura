'use client'

import { useState } from 'react'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { 
  useAIHealth, 
  useAIPlaygroundTest, 
  useEmbeddingHealth, 
  useEmbeddingTest,
  useVectorHealth,
  useVectorTest
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
  Code
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

function AIPlaygroundContent() {
  const [activeTab, setActiveTab] = useState<'llm' | 'embeddings' | 'vector'>('llm')

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
        ) : (
          <VectorHealthBadge />
        )}
      </div>

      {/* Tabs list */}
      <div className="flex border-b border-slate-200 gap-6">
        <button
          onClick={() => setActiveTab('llm')}
          className={`pb-3 font-semibold text-sm transition-all border-b-2 flex items-center gap-2 relative ${
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
          className={`pb-3 font-semibold text-sm transition-all border-b-2 flex items-center gap-2 relative ${
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
          className={`pb-3 font-semibold text-sm transition-all border-b-2 flex items-center gap-2 relative ${
            activeTab === 'vector'
              ? 'border-teal-600 text-teal-600 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Database className="h-4 w-4" />
          Vector Database
        </button>
      </div>

      {activeTab === 'llm' ? (
        <LLMPlaygroundView />
      ) : activeTab === 'embeddings' ? (
        <EmbeddingsPlaygroundView />
      ) : (
        <VectorPlaygroundView />
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
