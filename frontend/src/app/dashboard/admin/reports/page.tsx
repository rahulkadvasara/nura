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
  Layers
} from 'lucide-react'

function AdminReportsDashboardContent() {
  const [reports, setReports] = useState<ReportResponse[]>([])
  const [telemetry, setTelemetry] = useState<ReportTelemetryStats | null>(null)
  const [extractTelemetry, setExtractTelemetry] = useState<any | null>(null)
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('all')
  
  // Inspecting report details
  const [inspectingReport, setInspectingReport] = useState<ReportResponse | null>(null)
  const [ocrData, setOcrData] = useState<ReportOcrData | null>(null)
  const [structuredData, setStructuredData] = useState<any | null>(null)
  const [loadingOcr, setLoadingOcr] = useState(false)
  const [loadingExtraction, setLoadingExtraction] = useState(false)
  const [inspectTab, setInspectTab] = useState<'ocr' | 'json' | 'warnings'>('json')

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
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
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

  const handleInspect = async (report: ReportResponse) => {
    setInspectingReport(report)
    setOcrData(null)
    setStructuredData(null)
    setInspectTab(report.extraction_status === 'completed' ? 'json' : 'ocr')

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
            <Cpu className="h-8 w-8 text-teal-600 animate-pulse" />
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

      {/* Telemetry Dashboard Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
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
            name: 'Failed Jobs',
            val: (telemetry?.failures ?? 0) + (extractTelemetry?.failed_extractions ?? 0),
            desc: `Extraction failures: ${extractTelemetry?.failed_extractions ?? 0}`,
            icon: AlertTriangle
          }
        ].map((item, idx) => (
          <Card key={idx} className="border border-slate-200 shadow-sm bg-white">
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
              <div className="text-center py-20 text-slate-400">
                <p className="text-sm">No report records matching the selection filter.</p>
              </div>
            ) : (
              <div className="space-y-4 max-h-[600px] overflow-y-auto pr-1">
                {filteredReports.map((report) => (
                  <div
                    key={report.id}
                    className="border border-slate-200 rounded-lg p-4 bg-white hover:bg-slate-50/50 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <strong className="text-xs text-slate-900 font-mono">
                          {report.id.substring(report.id.length - 8)}
                        </strong>
                        {report.document_type ? (
                          <Badge className="bg-teal-50 text-teal-700 text-[9px] hover:bg-teal-50 border border-teal-200 rounded py-0.5">
                            {report.document_type}
                          </Badge>
                        ) : (
                          <span className="text-[10px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded font-mono font-bold uppercase">
                            {report.report_type.replace('_', ' ')}
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] text-slate-400">
                        File: {report.file_url.split('/').pop()?.substring(14) || 'document'}
                      </div>
                      <div className="text-[10px] text-slate-400">
                        Patient: {report.patient_id}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 justify-end">
                      {/* OCR and extraction status badges */}
                      {report.ocr_status !== 'completed' ? (
                        <span className={`text-[9px] font-bold px-2 py-0.5 rounded uppercase ${
                          report.ocr_status === 'failed' ? 'bg-red-50 text-red-700' : 'bg-amber-50 text-amber-700'
                        }`}>
                          OCR {report.ocr_status}
                        </span>
                      ) : (
                        <span className={`text-[9px] font-bold px-2 py-0.5 rounded uppercase ${
                          report.extraction_status === 'completed' ? 'bg-emerald-50 text-emerald-700' :
                          report.extraction_status === 'failed' ? 'bg-rose-50 text-rose-700' :
                          'bg-slate-100 text-slate-600'
                        }`}>
                          Struct {report.extraction_status || 'Pending'}
                        </span>
                      )}

                      <div className="flex items-center gap-1 pl-2 border-l border-slate-200">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleInspect(report)}
                          className="p-1 h-auto text-slate-500 hover:text-teal-600"
                          title="Inspect details"
                        >
                          <Eye className="h-3.5 w-3.5" />
                        </Button>
                        {report.ocr_status === 'completed' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleExtract(report.id)}
                            className="p-1 h-auto text-teal-600 hover:text-teal-700"
                            title="Trigger structured extraction"
                          >
                            <Play className="h-3.5 w-3.5" />
                          </Button>
                        )}
                        {report.ocr_status === 'failed' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRetryOcr(report.id)}
                            className="p-1 h-auto text-amber-500 hover:text-amber-700"
                            title="Retry OCR pipeline"
                          >
                            <RefreshCw className="h-3.5 w-3.5" />
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(report.id)}
                          className="p-1 h-auto text-slate-400 hover:text-red-600"
                          title="Purge record"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Right Column: In-depth OCR Layout & Structured JSON Inspector */}
        <div className="space-y-6">
          {inspectingReport ? (
            <Card className="border-2 border-teal-500 shadow-md bg-white">
              <CardHeader className="pb-3 border-b border-slate-100 bg-teal-50/20 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <CardTitle className="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                    <Database className="h-4 w-4 text-teal-600" />
                    Pipeline Diagnostics
                  </CardTitle>
                  <span className="text-xs text-slate-500 font-mono mt-1 block">
                    Report ID: {inspectingReport.id}
                  </span>
                </div>

                <div className="flex gap-2">
                  <Button
                    variant={inspectTab === 'json' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setInspectTab('json')}
                    className={`h-8 text-xs font-semibold ${inspectTab === 'json' ? 'bg-teal-600 hover:bg-teal-700' : ''}`}
                  >
                    Structured JSON
                  </Button>
                  <Button
                    variant={inspectTab === 'warnings' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setInspectTab('warnings')}
                    className={`h-8 text-xs font-semibold ${inspectTab === 'warnings' ? 'bg-teal-600 hover:bg-teal-700' : ''}`}
                  >
                    Warnings
                  </Button>
                  <Button
                    variant={inspectTab === 'ocr' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setInspectTab('ocr')}
                    className={`h-8 text-xs font-semibold ${inspectTab === 'ocr' ? 'bg-teal-600 hover:bg-teal-700' : ''}`}
                  >
                    OCR Raw Text
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="pt-6 space-y-6">
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
                        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">Normalized OCR Text Layout</span>
                        <pre className="bg-slate-950 text-slate-200 p-4 rounded-lg font-mono text-[11px] overflow-auto max-h-[400px] whitespace-pre-wrap border border-slate-800">
                          {ocrData.normalized_text}
                        </pre>
                      </div>
                    ) : (
                      <div className="text-center py-10 text-slate-400">
                        <p>No OCR layout content found.</p>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ) : (
            <div className="border border-slate-200 rounded-lg p-20 bg-slate-50/50 flex flex-col items-center justify-center text-slate-400 text-center h-full">
              <Eye className="h-10 w-10 mb-2 stroke-1 text-slate-400" />
              <p className="text-sm font-semibold">Inspect diagnostics details</p>
              <p className="text-xs text-slate-400 mt-1 max-w-xs">
                Select a document from the queue list to inspect parsed layout raw texts, structured JSON payloads, and warnings log lists.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function AdminReportsPage() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <AdminReportsDashboardContent />
    </ProtectedRoute>
  )
}
