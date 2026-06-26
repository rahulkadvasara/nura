'use client'

import { useState } from 'react'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { useAIHealth, useAIPlaygroundTest } from '@/hooks/use-ai'
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
  Database 
} from 'lucide-react'

function AIPlaygroundContent() {
  const [prompt, setPrompt] = useState('')
  const [testResult, setTestResult] = useState<any>(null)
  
  const { 
    data: health, 
    isLoading: isHealthLoading, 
    isError: isHealthError, 
    error: healthError,
    refetch: refetchHealth 
  } = useAIHealth()
  
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
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Sparkles className="h-8 w-8 text-teal-600 animate-pulse" />
            AI Infrastructure Playground
          </h1>
          <p className="text-slate-500 mt-1">
            Validate platform AI services connectivity, monitor LLM latency, and debug token allocations.
          </p>
        </div>
        
        {/* Health Check Summary Badge */}
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
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
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
        </div>
      </div>
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
