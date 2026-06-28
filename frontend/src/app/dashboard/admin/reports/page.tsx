'use client'

import { useState, useEffect } from 'react'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { reportService, ReportResponse, ReportTelemetryStats, ReportOcrData } from '@/services/report.service'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  FileText,
  Activity,
  Zap,
  RefreshCw,
  Clock,
  CheckCircle,
  AlertTriangle,
  Play,
  Trash2,
  Eye,
  AlertCircle,
  TrendingUp,
  Cpu,
  Database,
  Layers,
  Shield,
  BarChart4
} from 'lucide-react'

function AdminReportsDashboardContent() {
  const [reports, setReports] = useState<ReportResponse[]>([])
  const [telemetry, setTelemetry] = useState<ReportTelemetryStats | null>(null)
  const [extractTelemetry, setExtractTelemetry] = useState<any | null>(null)
  const [riskTelemetry, setRiskTelemetry] = useState<any | null>(null)
  const [aiTelemetry, setAiTelemetry] = useState<any | null>(null)
  const [syncTelemetry, setSyncTelemetry] = useState<any | null>(null)
  const [pipelineTelemetry, setPipelineTelemetry] = useState<any | null>(null)
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('all')
  
  // Inspecting report details
  const [inspectingReport, setInspectingReport] = useState<ReportResponse | null>(null)
  const [ocrData, setOcrData] = useState<ReportOcrData | null>(null)
  const [structuredData, setStructuredData] = useState<any | null>(null)
  const [riskData, setRiskData] = useState<any | null>(null)
  const [summaryData, setSummaryData] = useState<any | null>(null)
  const [insightsData, setInsightsData] = useState<any | null>(null)
  const [reportSyncStatus, setReportSyncStatus] = useState<any | null>(null)
  const [loadingOcr, setLoadingOcr] = useState(false)
  const [loadingExtraction, setLoadingExtraction] = useState(false)
  const [loadingRisk, setLoadingRisk] = useState(false)
  const [loadingSummary, setLoadingSummary] = useState(false)
  const [loadingSync, setLoadingSync] = useState(false)
  const [inspectTab, setInspectTab] = useState<'ocr' | 'json' | 'warnings' | 'risk' | 'summary_json' | 'prompt_debug' | 'sync_validation'>('json')

  const fetchData = async () => {
    try {
      setLoading(true)
      const list = await reportService.getReports()
      setReports(list.reverse())
      
      const stats = await reportService.getProcessingTelemetry()
      setTelemetry(stats)

      try {
        const extraStats = await reportService.getExtractionTelemetry()
        setExtractTelemetry(extraStats)
      } catch (err) {
        console.error('Failed to load extraction telemetry', err)
      }

      try {
        const rStats = await reportService.getRiskTelemetry()
        setRiskTelemetry(rStats)
      } catch (err) {
        console.error('Failed to load risk telemetry', err)
      }

      try {
        const aiStats = await reportService.getReportAiTelemetry()
        setAiTelemetry(aiStats)
      } catch (err) {
        console.error('Failed to load report AI telemetry', err)
      }

      try {
        const syncStats = await reportService.getReportSyncTelemetry()
        setSyncTelemetry(syncStats)
      } catch (err) {
        console.error('Failed to load synchronization telemetry', err)
      }

      try {
        const pipeStats = await reportService.getPipelineStatistics()
        setPipelineTelemetry(pipeStats)
      } catch (err) {
        console.error('Failed to load pipeline telemetry', err)
      }
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const handleRebuildSync = async () => {
    if (!confirm('Rebuild synchronization indexes for all completed reports? This performs vector indexing.')) return
    try {
      setLoadingSync(true)
      await reportService.rebuildReportSync()
      fetchData()
    } catch (err) {
      console.error(err)
    } finally {
      setLoadingSync(false)
    }
  }

  const handleSingleSync = async (reportId: string) => {
    try {
      setLoadingSync(true)
      await reportService.synchronizeReport(reportId)
      fetchData()
      if (inspectingReport?.id === reportId) {
        const check = await reportService.getReportSyncStatus(reportId)
        setReportSyncStatus(check)
      }
    } catch (err) {
      console.error(err)
    } finally {
      setLoadingSync(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleDelete = async (reportId: string) => {
    if (!confirm('Permanently delete this report and files?')) return
    try {
      await reportService.deleteReport(reportId)
      setReports(reports.filter(r => r.id !== reportId))
      if (inspectingReport?.id === reportId) {
        setInspectingReport(null)
      }
    } catch (e) {
      console.error(e)
    }
  }

  const handleRetryOcr = async (reportId: string) => {
    try {
      await reportService.processReport(reportId)
      fetchData()
    } catch (e) {
      console.error(e)
    }
  }

  const handleExtract = async (reportId: string) => {
    try {
      setLoadingExtraction(true)
      await reportService.extractReport(reportId)
      fetchData()
      setTimeout(async () => {
        const struct = await reportService.getStructuredData(reportId)
        setStructuredData(struct)
      }, 2000)
    } catch (e) {
      console.error(e)
    } finally {
      setLoadingExtraction(false)
    }
  }

  const handleRunRiskAnalysis = async (reportId: string) => {
    try {
      setLoadingRisk(true)
      await reportService.analyzeReportRisks(reportId)
      fetchData()
      setTimeout(async () => {
        const rDetails = await reportService.getReportRisks(reportId)
        setRiskData(rDetails)
      }, 2000)
    } catch (e) {
      console.error(e)
    } finally {
      setLoadingRisk(false)
    }
  }

  const handleInspect = async (report: ReportResponse) => {
    setInspectingReport(report)
    setOcrData(null)
    setStructuredData(null)
    setRiskData(null)
    setSummaryData(null)
    setInsightsData(null)
    setInspectTab(report.patient_summary || report.ai_summary ? 'summary_json' : report.overall_risk ? 'risk' : report.extraction_status === 'completed' ? 'json' : 'ocr')

    if (report.ocr_status === 'completed') {
      try {
        setLoadingOcr(true)
        const ocr = await reportService.getOcrResults(report.id)
        setOcrData(ocr)
      } catch (e) {
        console.error(e)
      } finally {
        setLoadingOcr(false)
      }
    }

    if (report.extraction_status === 'completed') {
      try {
        setLoadingExtraction(true)
        const struct = await reportService.getStructuredData(report.id)
        setStructuredData(struct)
      } catch (e) {
        console.error(e)
      } finally {
        setLoadingExtraction(false)
      }
    }

    if (report.overall_risk) {
      try {
        setLoadingRisk(true)
        const risk = await reportService.getReportRisks(report.id)
        setRiskData(risk)
      } catch (e) {
        console.error(e)
      } finally {
        setLoadingRisk(false)
      }
    }

    if (report.patient_summary || report.ai_summary) {
      try {
        setLoadingSummary(true)
        const summary = await reportService.getReportSummary(report.id)
        setSummaryData(summary)
        const insights = await reportService.getReportInsights(report.id)
        setInsightsData(insights)
        try {
          const sync = await reportService.getReportSyncStatus(report.id)
          setReportSyncStatus(sync)
        } catch (syncErr) {
          console.error('Failed to load sync status in admin', syncErr)
        }
      } catch (e) {
        console.error(e)
      } finally {
        setLoadingSummary(false)
      }
    }
  }

  const handleGenerateSummary = async (reportId: string) => {
    try {
      setLoadingSummary(true)
      await reportService.summarizeReport(reportId)
      fetchData()
      setTimeout(async () => {
        const summary = await reportService.getReportSummary(reportId)
        setSummaryData(summary)
        const insights = await reportService.getReportInsights(reportId)
        setInsightsData(insights)
      }, 4000)
    } catch (e) {
      console.error(e)
    } finally {
      setLoadingSummary(false)
    }
  }

  const getRiskBadgeColor = (risk?: string) => {
    switch (risk?.toLowerCase()) {
      case 'critical':
        return 'bg-red-50 text-red-700 border-red-200 font-extrabold'
      case 'high':
        return 'bg-rose-50 text-rose-700 border-rose-200'
      case 'medium':
        return 'bg-amber-50 text-amber-700 border-amber-200'
      case 'low':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200'
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200'
    }
  }

  const filteredReports = statusFilter === 'all'
    ? reports
    : reports.filter(r => {
        if (statusFilter === 'ocr_failed') return r.ocr_status === 'failed'
        if (statusFilter === 'extract_failed') return r.extraction_status === 'failed'
        if (statusFilter === 'completed') return r.extraction_status === 'completed'
        if (statusFilter === 'processing') return r.ocr_status === 'processing' || r.extraction_status === 'processing'
        return true
      })

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-4 md:p-6 bg-slate-50 min-h-screen">
      {/* Header section */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Cpu className="h-8 w-8 text-teal-600" />
            Medical Processing Pipeline Control
          </h1>
          <p className="text-slate-500 mt-1">
            Track OCR queues, trigger AI medical extractions, validate warning layouts, and monitor telemetry.
          </p>
        </div>
        <Button
          variant="outline"
          onClick={fetchData}
          className="flex items-center gap-1.5 border-slate-200 bg-white"
          disabled={loading}
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh Pipeline Status
        </Button>
      </div>

      {/* Production Monitoring Console */}
      {pipelineTelemetry && (
        <Card className="border border-slate-200 shadow-sm bg-white">
          <CardHeader className="pb-3 border-b border-slate-100 bg-slate-50/50 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <CardTitle className="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                <BarChart4 className="h-5 w-5 text-teal-600" />
                Pipeline Production Monitoring Console
              </CardTitle>
              <p className="text-xs text-slate-500 mt-1">
                Real-time dashboard for end-to-end stage durations, pipeline queue depth, failure rates, and retry counts.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-slate-500 font-bold">Health Status:</span>
              <Badge className={`capitalize font-bold text-xs ${
                pipelineTelemetry.health === 'healthy' 
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-700 hover:bg-emerald-50' 
                  : 'bg-rose-50 border-rose-200 text-rose-700 hover:bg-rose-50'
              }`}>
                {pipelineTelemetry.health || 'UNKNOWN'}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="pt-6 space-y-6">
            {/* Row 1: Key Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-center">
              <div className="border rounded-md p-3 bg-slate-50/50">
                <span className="text-[9px] uppercase font-bold text-slate-400 block">Queue Depth (Processing)</span>
                <span className="text-lg font-bold text-slate-800 mt-1 block">{pipelineTelemetry.queue_depth ?? 0}</span>
              </div>
              <div className="border rounded-md p-3 bg-slate-50/50">
                <span className="text-[9px] uppercase font-bold text-slate-400 block">Total Processed Reports</span>
                <span className="text-lg font-bold text-slate-800 mt-1 block">{pipelineTelemetry.total_processed ?? 0}</span>
              </div>
              <div className="border rounded-md p-3 bg-slate-50/50">
                <span className="text-[9px] uppercase font-bold text-slate-400 block">End-to-End Successes</span>
                <span className="text-lg font-bold text-emerald-600 mt-1 block">{pipelineTelemetry.completed_count ?? 0}</span>
              </div>
              <div className="border rounded-md p-3 bg-slate-50/50">
                <span className="text-[9px] uppercase font-bold text-slate-400 block">Failure Rate %</span>
                <span className="text-lg font-bold text-rose-600 mt-1 block">{pipelineTelemetry.failure_rate_percent ?? 0}%</span>
              </div>
              <div className="border rounded-md p-3 bg-slate-50/50">
                <span className="text-[9px] uppercase font-bold text-slate-400 block">Total Pipeline Retries</span>
                <span className="text-lg font-bold text-teal-600 mt-1 block">{pipelineTelemetry.total_retries ?? 0}</span>
              </div>
            </div>

            {/* Row 2: Average Timings per Stage */}
            <div className="space-y-2.5">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Average Stage Latency Metrics</span>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
                {[
                  { label: 'OCR scan', val: pipelineTelemetry.averages?.avg_ocr_ms },
                  { label: 'Clinical extraction', val: pipelineTelemetry.averages?.avg_extraction_ms },
                  { label: 'Clinical risk engine', val: pipelineTelemetry.averages?.avg_risk_ms },
                  { label: 'AI understanding', val: pipelineTelemetry.averages?.avg_summary_ms },
                  { label: 'DB & Vector Sync', val: pipelineTelemetry.averages?.avg_sync_ms }
                ].map((stage, idx) => (
                  <div key={idx} className="p-3 border rounded bg-white text-center shadow-2xs space-y-1">
                    <span className="text-[9px] font-bold text-slate-400 uppercase block">{stage.label}</span>
                    <strong className="text-slate-800 text-sm block">
                      {stage.val ? `${(stage.val / 1000).toFixed(2)}s` : '0.00s'}
                    </strong>
                  </div>
                ))}
              </div>
            </div>

            {/* Row 3: Common Errors */}
            {pipelineTelemetry.common_errors && pipelineTelemetry.common_errors.length > 0 && (
              <div className="space-y-2 border-t border-slate-100 pt-4">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Most Common Failure Causes</span>
                <div className="space-y-2">
                  {pipelineTelemetry.common_errors.map((err: any, idx: number) => (
                    <div key={idx} className="flex justify-between items-center bg-rose-50/50 p-2.5 rounded border border-rose-100/50 text-[11px] font-mono text-rose-800">
                      <span className="truncate max-w-xl">{err.error}</span>
                      <strong className="shrink-0">Count: {err.count}</strong>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Telemetry Dashboard Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {[
          {
            name: 'OCR Processed Documents',
            val: telemetry?.uploaded_documents ?? 0,
            desc: `Avg latency: ${telemetry?.ocr_latency_average_ms.toFixed(0) ?? 0}ms`,
            icon: FileText
          },
          {
            name: 'Clinical Extractions Run',
            val: extractTelemetry?.total_extractions ?? 0,
            desc: `Success rate: ${(((extractTelemetry?.successful_extractions ?? 0) / Math.max(1, extractTelemetry?.total_extractions ?? 0)) * 100).toFixed(0)}%`,
            icon: Layers
          },
          {
            name: 'Extraction Avg Confidence',
            val: `${((extractTelemetry?.average_extraction_confidence ?? 0.0) * 100).toFixed(1)}%`,
            desc: `Avg execution: ${(extractTelemetry?.average_duration_ms ?? 0.0).toFixed(0)}ms`,
            icon: TrendingUp
          },
          {
            name: 'Clinical Risks Scored',
            val: riskTelemetry?.total_analyses ?? 0,
            desc: `Success rate: ${(((riskTelemetry?.successful_analyses ?? 0) / Math.max(1, riskTelemetry?.total_analyses ?? 0)) * 100).toFixed(0)}%`,
            icon: Shield
          },
          {
            name: 'AI Summaries Generated',
            val: aiTelemetry?.total_generations ?? 0,
            desc: `Avg: ${aiTelemetry?.average_latency_ms ?? 0}ms | Cost: $${(aiTelemetry?.accumulated_cost ?? 0.0).toFixed(4)}`,
            icon: Zap
          }
        ].map((item, idx) => (
          <Card key={idx} className="border border-slate-200 shadow-sm bg-white">
            <CardContent className="pt-4 flex items-center justify-between">
              <div>
                <span className="text-[10px] text-slate-400 block uppercase font-bold">{item.name}</span>
                <span className="text-lg font-bold text-slate-900 mt-0.5 block">{item.val}</span>
                <span className="text-[9px] text-slate-500 block mt-0.5">{item.desc}</span>
              </div>
              <item.icon className="h-7 w-7 text-teal-600/30" />
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Knowledge Synchronization Controls & Stats Card */}
      <Card className="border border-teal-200 shadow-sm bg-white">
        <CardHeader className="pb-3 border-b border-slate-100 bg-teal-50/15 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <CardTitle className="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
              <Cpu className="h-5 w-5 text-teal-600" />
              Knowledge Synchronization & Vector Analytics
            </CardTitle>
            <p className="text-xs text-slate-500 mt-1">
              Synchronize processed summaries to patient_memory (MongoDB) and patient_reports Qdrant vectors.
            </p>
          </div>
          <Button
            size="sm"
            onClick={handleRebuildSync}
            className="bg-teal-600 hover:bg-teal-700 text-white font-semibold flex items-center gap-1.5 h-8 text-xs shrink-0"
            disabled={loadingSync}
          >
            {loadingSync ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
            Rebuild Synchronization Index
          </Button>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-center">
            <div className="border rounded-md p-3 bg-slate-50">
              <span className="text-[9px] uppercase font-bold text-slate-400 block">Total Sync Runs</span>
              <span className="text-lg font-bold text-slate-800 mt-1 block">{syncTelemetry?.total_syncs ?? 0}</span>
            </div>
            <div className="border rounded-md p-3 bg-slate-50">
              <span className="text-[9px] uppercase font-bold text-slate-400 block">Successful Syncs</span>
              <span className="text-lg font-bold text-slate-800 mt-1 block">{syncTelemetry?.successful_syncs ?? 0}</span>
            </div>
            <div className="border rounded-md p-3 bg-slate-50">
              <span className="text-[9px] uppercase font-bold text-slate-400 block">Failed Sync Jobs</span>
              <span className="text-lg font-bold text-rose-600 mt-1 block">{syncTelemetry?.failed_syncs ?? 0}</span>
            </div>
            <div className="border rounded-md p-3 bg-slate-50">
              <span className="text-[9px] uppercase font-bold text-slate-400 block">Duplicates Prevented</span>
              <span className="text-lg font-bold text-teal-600 mt-1 block">{syncTelemetry?.duplicate_chunks_prevented ?? 0}</span>
            </div>
            <div className="border rounded-md p-3 bg-slate-50">
              <span className="text-[9px] uppercase font-bold text-slate-400 block">Avg Sync Latency</span>
              <span className="text-lg font-bold text-slate-800 mt-1 block">{syncTelemetry?.average_latency_ms ?? 0}ms</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Document Queue and Inspect Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Column: Job Queue List */}
        <Card className="border border-slate-200 shadow-sm bg-white h-fit">
          <CardHeader className="pb-3 border-b border-slate-100 bg-slate-50/50 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <CardTitle className="text-sm font-bold text-slate-800 uppercase tracking-wider">
              Document Processing Queue
            </CardTitle>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 font-bold">Filter:</span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="rounded border border-slate-200 px-2 py-1 text-xs bg-white focus:outline-none"
              >
                <option value="all">All Jobs</option>
                <option value="processing">Processing</option>
                <option value="completed">Completed Extract</option>
                <option value="ocr_failed">OCR Failed</option>
                <option value="extract_failed">Extraction Failed</option>
              </select>
            </div>
          </CardHeader>
          <CardContent className="pt-6">
            {loading && reports.length === 0 ? (
              <div className="text-center py-20">
                <RefreshCw className="h-8 w-8 animate-spin text-teal-600 mx-auto mb-2" />
                <p className="text-xs text-slate-500">Fetching document indexes...</p>
              </div>
            ) : filteredReports.length === 0 ? (
              <div className="text-center py-20 text-slate-400 text-xs">
                No reports found matching the selected filters.
              </div>
            ) : (
              <div className="space-y-3">
                {filteredReports.map((report) => (
                  <div
                    key={report.id}
                    className="border border-slate-200 rounded-lg p-3.5 bg-white hover:shadow-xs transition-all flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs"
                  >
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <strong className="text-slate-800 truncate max-w-xs">{report.file_url.split('/').pop()?.substring(14) || 'Medical Report'}</strong>
                        {report.document_type && (
                          <Badge className="bg-teal-50 text-teal-700 border-teal-200 scale-90 rounded">
                            {report.document_type}
                          </Badge>
                        )}
                        {report.overall_risk && (
                          <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase ${getRiskBadgeColor(report.overall_risk)}`}>
                            {report.overall_risk}
                          </span>
                        )}
                      </div>
                      <p className="text-[10px] text-slate-400">ID: {report.id} • Created: {new Date(report.created_at).toLocaleDateString()}</p>
                    </div>

                    <div className="flex items-center gap-2 justify-end w-full sm:w-auto">
                      {/* Extraction retry/trigger options */}
                      {report.ocr_status === 'failed' ? (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRetryOcr(report.id)}
                          className="text-xs text-amber-600 hover:text-amber-700 font-bold bg-amber-50 h-7"
                        >
                          Retry OCR
                        </Button>
                      ) : report.extraction_status === 'pending' || report.extraction_status === 'failed' ? (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleExtract(report.id)}
                          className="text-xs text-teal-600 hover:text-teal-700 font-bold bg-teal-50 h-7"
                        >
                          Run Extract
                        </Button>
                      ) : !report.overall_risk ? (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRunRiskAnalysis(report.id)}
                          className="text-xs text-orange-600 hover:text-orange-700 font-bold bg-orange-50 h-7"
                        >
                          Run Risk
                        </Button>
                      ) : !report.patient_summary ? (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleGenerateSummary(report.id)}
                          className="text-xs text-teal-600 hover:text-teal-700 font-bold bg-teal-50 h-7"
                          disabled={loadingSummary}
                        >
                          Run Summary
                        </Button>
                      ) : !report.is_synchronized ? (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleSingleSync(report.id)}
                          className="text-xs text-indigo-600 hover:text-indigo-700 font-bold bg-indigo-50 h-7"
                          disabled={loadingSync}
                        >
                          Sync Memory
                        </Button>
                      ) : (
                        <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200 py-0.5 rounded">
                          Synchronised
                        </Badge>
                      )}

                      <div className="flex items-center gap-1 pl-2 border-l border-slate-200">
                        <Button variant="ghost" size="sm" onClick={() => handleInspect(report)} className="p-1 h-auto text-slate-400 hover:text-teal-600">
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => handleDelete(report.id)} className="p-1 h-auto text-slate-400 hover:text-rose-600">
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Right Column: Inspector Panel details */}
        {inspectingReport ? (
          <Card className="border-2 border-teal-500 shadow-sm bg-white h-fit">
            <CardHeader className="pb-3 border-b border-slate-100 bg-teal-50/10">
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                    <Database className="h-4 w-4 text-teal-600" />
                    Pipeline Diagnostics
                  </CardTitle>
                  <span className="text-xs text-slate-500 font-mono mt-1 block">
                    Report ID: {inspectingReport.id}
                  </span>
                </div>

                <div className="flex gap-1.5 flex-wrap">
                  {[
                    { id: 'summary_json', name: 'Summary JSON' },
                    { id: 'prompt_debug', name: 'Prompt Debug' },
                    { id: 'sync_validation', name: 'Sync Status' },
                    { id: 'risk', name: 'Risk JSON' },
                    { id: 'json', name: 'Struct JSON' },
                    { id: 'warnings', name: 'Warnings' },
                    { id: 'ocr', name: 'OCR Text' }
                  ].map((tab) => (
                    <Button
                      key={tab.id}
                      variant={inspectTab === tab.id ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setInspectTab(tab.id as any)}
                      className={`h-8 text-xs font-semibold ${inspectTab === tab.id ? 'bg-teal-600 hover:bg-teal-700 text-white' : ''}`}
                    >
                      {tab.name}
                    </Button>
                  ))}
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-6 space-y-6">
              {inspectTab === 'sync_validation' && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Report Synchronization Audit Status</span>
                    {inspectingReport.processing_status === 'completed' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleSingleSync(inspectingReport.id)}
                        className="h-7 text-[10px] text-teal-700 border-teal-200"
                        disabled={loadingSync}
                      >
                        Synchronize Knowledge
                      </Button>
                    )}
                  </div>

                  {loadingSync ? (
                    <div className="text-center py-20 text-slate-500">
                      <RefreshCw className="h-8 w-8 animate-spin text-teal-600 mb-2" />
                      <p className="text-sm">Synchronizing memory documents & vector chunks...</p>
                    </div>
                  ) : reportSyncStatus ? (
                    <div className="space-y-3">
                      <div className="grid grid-cols-2 gap-4 text-xs">
                        <div className="p-3 border rounded bg-slate-50">
                          <span className="text-slate-400 font-bold block">MongoDB Status</span>
                          <span className="text-sm font-bold text-slate-800 mt-1 block">{reportSyncStatus.validation_details?.mongodb_memory_status}</span>
                        </div>
                        <div className="p-3 border rounded bg-slate-50">
                          <span className="text-slate-400 font-bold block">Qdrant status</span>
                          <span className="text-sm font-bold text-slate-800 mt-1 block">{reportSyncStatus.validation_details?.qdrant_points_status}</span>
                        </div>
                      </div>

                      <pre className="bg-slate-950 text-indigo-400 p-4 rounded-lg font-mono text-[11px] overflow-auto max-h-[400px] border border-slate-800 whitespace-pre-wrap">
                        {JSON.stringify(reportSyncStatus, null, 2)}
                      </pre>
                    </div>
                  ) : (
                    <div className="text-center py-20 border border-dashed rounded-lg text-slate-400 bg-slate-50/50">
                      <Cpu className="h-10 w-10 mx-auto text-slate-300 mb-2 stroke-1" />
                      <p className="text-sm">No synchronization logs compiled yet. Click &quot;Synchronize Knowledge&quot; above.</p>
                    </div>
                  )}
                </div>
              )}

              {inspectTab === 'summary_json' && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">AI Summarization Outputs JSON</span>
                    {inspectingReport.overall_risk && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleGenerateSummary(inspectingReport.id)}
                        className="h-7 text-[10px] text-teal-700 border-teal-200"
                        disabled={loadingSummary}
                      >
                        Generate AI Summary
                      </Button>
                    )}
                  </div>

                  {loadingSummary ? (
                    <div className="text-center py-20 text-slate-500">
                      <RefreshCw className="h-8 w-8 animate-spin text-teal-600 mb-2" />
                      <p className="text-sm">Synthesizing clinical insights and descriptions...</p>
                    </div>
                  ) : summaryData ? (
                    <pre className="bg-slate-950 text-emerald-400 p-4 rounded-lg font-mono text-[11px] overflow-auto max-h-[500px] border border-slate-800 whitespace-pre-wrap">
                      {JSON.stringify({ summaryData, insightsData }, null, 2)}
                    </pre>
                  ) : (
                    <div className="text-center py-20 border border-dashed rounded-lg text-slate-400 bg-slate-50/50">
                      <Zap className="h-10 w-10 mx-auto text-slate-300 mb-2 stroke-1" />
                      <p className="text-sm">No summaries compiled yet. Click &quot;Generate AI Summary&quot; above.</p>
                    </div>
                  )}
                </div>
              )}

              {inspectTab === 'prompt_debug' && (
                <div className="space-y-4">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">AI Prompts Template Debugger</span>
                  <div className="space-y-3 font-mono text-[10px]">
                    <div className="border border-slate-800 rounded bg-slate-950 text-cyan-400 p-3 space-y-1">
                      <span className="font-sans text-[10px] font-bold text-slate-400 block border-b border-slate-800 pb-1">report_summary_system.md</span>
                      <pre className="whitespace-pre-wrap leading-relaxed">
{`You are an expert medical AI assistant specialized in clinical summarization and diagnostics interpretations.
Your task is to analyze structured lab parameters and write structured interpretations.
Output structure JSON:
{
  "ai_summary": "Concise overview",
  "patient_summary": "Simple friendly explanation",
  "doctor_summary": "Differential interpretation",
  "key_findings": ["string"],
  "clinical_insights": ["string"],
  "followup_questions": ["string"],
  "confidence": 0.95
}`}
                      </pre>
                    </div>

                    <div className="border border-slate-800 rounded bg-slate-950 text-indigo-300 p-3 space-y-1">
                      <span className="font-sans text-[10px] font-bold text-slate-400 block border-b border-slate-800 pb-1">patient_summary.md & doctor_summary.md</span>
                      <pre className="whitespace-pre-wrap leading-relaxed">
{`Demographics: ${JSON.stringify(structuredData?.patient_information ?? {}, null, 2)}
Lab Results (count: ${structuredData?.laboratory_results?.length ?? 0}): ...
Risk Assessment: ${JSON.stringify(riskData ?? {}, null, 2)}`}
                      </pre>
                    </div>
                  </div>
                </div>
              )}

              {inspectTab === 'risk' && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Calculated Diagnostic Risks Payload</span>
                    {inspectingReport.extraction_status === 'completed' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleRunRiskAnalysis(inspectingReport.id)}
                        className="h-7 text-[10px] text-orange-700 border-orange-200"
                        disabled={loadingRisk}
                      >
                        Calculate Risks
                      </Button>
                    )}
                  </div>

                  {loadingRisk ? (
                    <div className="text-center py-20 text-slate-500">
                      <RefreshCw className="h-8 w-8 animate-spin text-teal-600 mb-2" />
                      <p className="text-sm">Evaluating clinical diagnostic ranges & AI scores...</p>
                    </div>
                  ) : riskData ? (
                    <pre className="bg-slate-950 text-orange-400 p-4 rounded-lg font-mono text-[11px] overflow-auto max-h-[500px] border border-slate-800 whitespace-pre-wrap">
                      {JSON.stringify(riskData, null, 2)}
                    </pre>
                  ) : (
                    <div className="text-center py-20 border border-dashed rounded-lg text-slate-400 bg-slate-50/50">
                      <Shield className="h-10 w-10 mx-auto text-slate-300 mb-2 stroke-1" />
                      <p className="text-sm">No risk data compiled. Click &quot;Calculate Risks&quot; above.</p>
                    </div>
                  )}
                </div>
              )}

              {inspectTab === 'json' && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Clinical JSON Output</span>
                    {inspectingReport.ocr_status === 'completed' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleExtract(inspectingReport.id)}
                        className="h-7 text-[10px] text-teal-700 border-teal-200"
                        disabled={loadingExtraction}
                      >
                        Re-run Extraction
                      </Button>
                    )}
                  </div>

                  {loadingExtraction ? (
                    <div className="text-center py-20 text-slate-500">
                      <RefreshCw className="h-8 w-8 animate-spin text-teal-600 mb-2" />
                      <p className="text-sm">Running structured clinical extractor model...</p>
                    </div>
                  ) : structuredData ? (
                    <pre className="bg-slate-950 text-teal-400 p-4 rounded-lg font-mono text-[11px] overflow-auto max-h-[500px] border border-slate-800 whitespace-pre-wrap">
                      {JSON.stringify(structuredData, null, 2)}
                    </pre>
                  ) : (
                    <div className="text-center py-20 border border-dashed rounded-lg text-slate-400 bg-slate-50/50">
                      <Database className="h-10 w-10 mx-auto text-slate-300 mb-2 stroke-1" />
                      <p className="text-sm">No structured data extracted. Click &quot;Re-run Extraction&quot; above.</p>
                    </div>
                  )}
                </div>
              )}

              {inspectTab === 'warnings' && (
                <div className="space-y-4">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">Pipeline Warnings & Log Stack</span>
                  {structuredData && structuredData.extraction_warnings && structuredData.extraction_warnings.length > 0 ? (
                    <div className="space-y-2">
                      {structuredData.extraction_warnings.map((warn: string, idx: number) => (
                        <div key={idx} className="p-3 bg-amber-50 border border-amber-200 text-amber-800 font-semibold rounded text-xs flex items-start gap-2">
                          <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
                          <span>{warn}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12 border border-dashed rounded-lg text-slate-400 bg-slate-50/50">
                      <CheckCircle className="h-10 w-10 mx-auto text-emerald-500 mb-2 stroke-1" />
                      <p className="text-xs font-semibold text-slate-600">Extraction layout clean!</p>
                      <p className="text-[10px] text-slate-400 mt-1">No clinical validation warning alerts registered.</p>
                    </div>
                  )}
                </div>
              )}

              {inspectTab === 'ocr' && (
                <div className="space-y-6">
                  {loadingOcr ? (
                    <div className="flex flex-col items-center justify-center py-20 text-slate-500">
                      <RefreshCw className="h-8 w-8 animate-spin text-teal-600 mb-2" />
                      <p className="text-sm">Loading layouts...</p>
                    </div>
                  ) : ocrData ? (
                    <div className="space-y-4">
                      {ocrData.ocr_pages && ocrData.ocr_pages.length > 0 && (
                        <div className="space-y-2">
                          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">Pages Confidence Analysis</span>
                          <div className="flex gap-2 flex-wrap">
                            {ocrData.ocr_pages.map((p, idx) => (
                              <Badge key={idx} className="bg-slate-100 hover:bg-slate-100 text-slate-700 py-1">
                                Pg {p.page_number}: {(p.confidence * 100).toFixed(0)}%
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      <pre className="bg-slate-950 text-slate-200 p-4 rounded-lg font-mono text-[11px] overflow-auto max-h-[300px] border border-slate-800 whitespace-pre-wrap">
                        {ocrData.normalized_text}
                      </pre>
                    </div>
                  ) : (
                    <div className="text-center py-20 text-slate-400">
                      No layout data found.
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        ) : (
          <Card className="border border-dashed border-slate-300 rounded-lg bg-slate-50/50 flex flex-col items-center justify-center py-24 text-center">
            <Database className="h-12 w-12 text-slate-300 mb-2 stroke-1" />
            <span className="text-sm font-semibold text-slate-500">Pipeline Inspector Panel</span>
            <p className="text-xs text-slate-400 max-w-xs mt-1">
              Select any report from the queue list to inspect layout text, structured extraction JSON, and calculated clinical risk outcomes.
            </p>
          </Card>
        )}
      </div>

      {/* Admin Clinical Risk Telemetry Section */}
      {riskTelemetry && (
        <Card className="border border-slate-200 shadow-sm bg-white mt-8">
          <CardHeader className="pb-3 border-b border-slate-100 bg-slate-50/50">
            <CardTitle className="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
              <BarChart4 className="h-5 w-5 text-teal-600" />
              Clinical Risk Telemetry Dashboard
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Severity Distribution table */}
              <div className="space-y-3">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">Risk Severity Distribution</span>
                <div className="border rounded overflow-hidden text-xs">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="bg-slate-50 border-b text-slate-500 font-bold">
                        <th className="p-2.5">Severity Category</th>
                        <th className="p-2.5 text-right">Job Count</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {Object.entries(riskTelemetry.severity_distribution || {}).map(([sev, count]: any) => (
                        <tr key={sev} className="hover:bg-slate-50/50">
                          <td className="p-2.5 font-bold uppercase flex items-center gap-1.5">
                            <span className={`w-2.5 h-2.5 rounded-full ${
                              sev === 'CRITICAL' ? 'bg-red-600' :
                              sev === 'HIGH' ? 'bg-orange-500' :
                              sev === 'MEDIUM' ? 'bg-amber-400' :
                              sev === 'LOW' ? 'bg-sky-400' :
                              'bg-emerald-500'
                            }`} />
                            {sev}
                          </td>
                          <td className="p-2.5 text-right font-mono font-bold text-slate-800">{count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Triggered Clinical Flags */}
              <div className="space-y-3">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">Clinical Flags Occurrences</span>
                {Object.keys(riskTelemetry.clinical_flags_triggered || {}).length === 0 ? (
                  <div className="p-6 border border-dashed rounded text-center text-slate-400 text-xs">
                    No clinical risk flags triggered yet.
                  </div>
                ) : (
                  <div className="border rounded overflow-hidden text-xs">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="bg-slate-50 border-b text-slate-500 font-bold">
                          <th className="p-2.5">Flag Name</th>
                          <th className="p-2.5 text-right">Trigger Count</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {Object.entries(riskTelemetry.clinical_flags_triggered || {}).map(([flg, count]: any) => (
                          <tr key={flg} className="hover:bg-slate-50/50">
                            <td className="p-2.5 font-semibold uppercase text-slate-700">{flg.replace('_', ' ')}</td>
                            <td className="p-2.5 text-right font-mono font-bold text-slate-800">{count}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Recommendations Metrics */}
              <div className="space-y-3">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">Actionable Suggestions Distribution</span>
                {Object.keys(riskTelemetry.recommendation_metrics || {}).length === 0 ? (
                  <div className="p-6 border border-dashed rounded text-center text-slate-400 text-xs">
                    No recommendations statistics mapped yet.
                  </div>
                ) : (
                  <div className="border rounded overflow-hidden text-xs">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="bg-slate-50 border-b text-slate-500 font-bold">
                          <th className="p-2.5">Recommendation Type</th>
                          <th className="p-2.5 text-right">Run Count</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {Object.entries(riskTelemetry.recommendation_metrics || {}).map(([type, count]: any) => (
                          <tr key={type} className="hover:bg-slate-50/50">
                            <td className="p-2.5 font-semibold text-slate-700">{type}</td>
                            <td className="p-2.5 text-right font-mono font-bold text-slate-800">{count}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default function AdminReportsDashboardPage() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <AdminReportsDashboardContent />
    </ProtectedRoute>
  )
}
