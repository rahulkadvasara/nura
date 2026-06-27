'use client'

import { useState, useEffect } from 'react'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { reportService, ReportResponse, ReportTelemetryStats, ReportOcrData } from '@/services/report.service'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
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
  Cpu
} from 'lucide-react'

function AdminReportsDashboardContent() {
  const [reports, setReports] = useState<ReportResponse[]>([])
  const [telemetry, setTelemetry] = useState<ReportTelemetryStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('all')
  
  // Inspecting report details
  const [inspectingReport, setInspectingReport] = useState<ReportResponse | null>(null)
  const [ocrData, setOcrData] = useState<ReportOcrData | null>(null)
  const [loadingOcr, setLoadingOcr] = useState(false)

  const fetchData = async () => {
    try {
      setLoading(true)
      const list = await reportService.getReports()
      setReports(list.reverse())
      
      const stats = await reportService.getProcessingTelemetry()
      setTelemetry(stats)
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

  const handleRetry = async (reportId: string) => {
    try {
      await reportService.processReport(reportId)
      fetchData()
    } catch (e) {
      console.error(e)
    }
  }

  const handleInspect = async (report: ReportResponse) => {
    setInspectingReport(report)
    setOcrData(null)
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
  }

  const filteredReports = statusFilter === 'all'
    ? reports
    : reports.filter(r => r.ocr_status === statusFilter)

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-4 md:p-6 bg-slate-50 min-h-screen">
      {/* Header section */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Cpu className="h-8 w-8 text-teal-600 animate-pulse" />
            OCR Document Pipeline
          </h1>
          <p className="text-slate-500 mt-1">
            System queue tracker, page details validation, and OCR telemetry dashboards.
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
      {telemetry && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[
            { name: 'Uploaded Documents', val: telemetry.uploaded_documents, desc: 'Total database reports', icon: FileText },
            { name: 'Processed Pages', val: telemetry.processed_pages, desc: `Average: ${(telemetry.average_processing_time_ms / 1000.0).toFixed(1)}s per doc`, icon: Activity },
            { name: 'Average Confidence', val: `${(telemetry.average_confidence * 100).toFixed(1)}%`, desc: `Average OCR latency: ${telemetry.ocr_latency_average_ms.toFixed(0)}ms`, icon: TrendingUp },
            { name: 'Pipeline Failures', val: telemetry.failures, desc: `Total job retries: ${telemetry.retries}`, icon: AlertTriangle }
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
      )}

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
                <option value="pending">Pending</option>
                <option value="processing">Processing</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
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
                        <span className="text-[10px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded font-mono font-bold uppercase">
                          {report.report_type.replace('_', ' ')}
                        </span>
                      </div>
                      <div className="text-[10px] text-slate-400">
                        File: {report.file_url.split('/').pop()?.substring(14) || 'document'}
                      </div>
                      <div className="text-[10px] text-slate-400">
                        Patient: {report.patient_id}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 justify-end">
                      {/* OCR Status tag */}
                      {report.ocr_status === 'pending' && (
                        <span className="text-[10px] font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded flex items-center gap-1">
                          <Clock className="h-3 w-3" /> PENDING
                        </span>
                      )}
                      {report.ocr_status === 'processing' && (
                        <span className="text-[10px] font-bold text-amber-600 bg-amber-50 px-2 py-0.5 rounded flex items-center gap-1">
                          <RefreshCw className="h-3 w-3 animate-spin" /> PROCESSING
                        </span>
                      )}
                      {report.ocr_status === 'completed' && (
                        <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded flex items-center gap-1">
                          <CheckCircle className="h-3 w-3" /> COMPLETED
                        </span>
                      )}
                      {report.ocr_status === 'failed' && (
                        <span className="text-[10px] font-bold text-red-600 bg-red-50 px-2 py-0.5 rounded flex items-center gap-1">
                          <AlertCircle className="h-3 w-3" /> FAILED
                        </span>
                      )}

                      <div className="flex items-center gap-1 pl-2 border-l border-slate-200">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleInspect(report)}
                          className="p-1 h-auto text-slate-500 hover:text-teal-600"
                          title="Inspect OCR results"
                        >
                          <Eye className="h-3.5 w-3.5" />
                        </Button>
                        {report.ocr_status === 'failed' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRetry(report.id)}
                            className="p-1 h-auto text-amber-500 hover:text-amber-700"
                            title="Retry OCR pipeline"
                          >
                            <Play className="h-3.5 w-3.5" />
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

        {/* Right Column: In-depth OCR Layout Inspector */}
        <div className="space-y-6">
          {inspectingReport ? (
            <Card className="border-2 border-teal-500 shadow-md bg-white">
              <CardHeader className="pb-3 border-b border-slate-100 bg-teal-50/20 flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                    <Eye className="h-4 w-4 text-teal-600" />
                    OCR Page Breakdown & Logs
                  </CardTitle>
                  <span className="text-xs text-slate-500 font-mono mt-1 block">
                    Report Reference: {inspectingReport.id}
                  </span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setInspectingReport(null)}
                  className="text-slate-400 hover:text-slate-800"
                >
                  Clear Inspect
                </Button>
              </CardHeader>
              <CardContent className="pt-6 space-y-6">
                {inspectingReport.ocr_status === 'failed' && (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <h4 className="text-xs font-bold text-red-800 uppercase flex items-center gap-1.5 mb-2">
                      <AlertCircle className="h-4 w-4 text-red-600" />
                      Pipeline Processing Exceptions Logs
                    </h4>
                    <pre className="text-xs font-mono text-red-800 bg-white/50 p-2 rounded overflow-auto max-h-36 whitespace-pre-wrap">
                      {inspectingReport.processing_errors && inspectingReport.processing_errors.length > 0
                        ? inspectingReport.processing_errors.join('\n')
                        : 'Unknown poppler/tesseract exception occurred.'}
                    </pre>
                  </div>
                )}

                {loadingOcr ? (
                  <div className="flex flex-col items-center justify-center py-20 text-slate-500">
                    <RefreshCw className="h-8 w-8 animate-spin text-teal-600 mb-2" />
                    <p className="text-sm">Fetching document breakdown layout...</p>
                  </div>
                ) : ocrData ? (
                  <div className="space-y-6">
                    {/* Telemetry info */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-slate-50 border border-slate-200 rounded-lg text-xs">
                      <div>
                        <span className="text-slate-400 block uppercase font-semibold">Method</span>
                        <strong className="text-slate-800 font-mono mt-0.5 block uppercase">{ocrData.metadata.ocr_method}</strong>
                      </div>
                      <div>
                        <span className="text-slate-400 block uppercase font-semibold">Duration</span>
                        <strong className="text-slate-800 mt-0.5 block">{(inspectingReport.ocr_duration_ms ?? 0.0).toFixed(0)} ms</strong>
                      </div>
                      <div>
                        <span className="text-slate-400 block uppercase font-semibold">Pages</span>
                        <strong className="text-slate-800 mt-0.5 block">{ocrData.metadata.page_count}</strong>
                      </div>
                      <div>
                        <span className="text-slate-400 block uppercase font-semibold">Confidence</span>
                        <strong className="text-slate-800 mt-0.5 block">{(ocrData.metadata.ocr_average_confidence * 100).toFixed(1)}%</strong>
                      </div>
                    </div>

                    {/* Page breakdown timeline */}
                    {ocrData.ocr_pages && ocrData.ocr_pages.length > 0 && (
                      <div className="space-y-4">
                        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">Individual Pages Data</span>
                        <div className="space-y-3">
                          {ocrData.ocr_pages.map((page, idx) => (
                            <div key={idx} className="border border-slate-200 rounded-md p-4 bg-white text-xs space-y-3">
                              <div className="flex justify-between items-center border-b border-slate-100 pb-2">
                                <span className="font-bold text-slate-700">Page {page.page_number}</span>
                                <div className="flex items-center gap-3 text-[10px] text-slate-500">
                                  <span>Confidence: {(page.confidence * 100).toFixed(0)}%</span>
                                  <span>•</span>
                                  <span>Latency: {page.processing_time.toFixed(0)} ms</span>
                                  <span>•</span>
                                  <span>Words: {page.word_count}</span>
                                </div>
                              </div>
                              <pre className="bg-slate-900 text-teal-400 p-3 rounded font-mono text-[11px] overflow-x-auto whitespace-pre-wrap max-h-36 border border-slate-800">
                                {page.normalized_text}
                              </pre>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Full debug JSON view */}
                    <div className="space-y-2">
                      <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">Full Document Layout Output</span>
                      <pre className="bg-slate-950 text-slate-200 p-4 rounded-lg font-mono text-[11px] overflow-auto max-h-72 whitespace-pre-wrap border border-slate-800">
                        {ocrData.normalized_text}
                      </pre>
                    </div>
                  </div>
                ) : (
                  inspectingReport.ocr_status === 'processing' && (
                    <div className="text-center py-20 text-slate-500">
                      <RefreshCw className="h-8 w-8 animate-spin text-teal-600 mx-auto mb-2" />
                      <p className="text-sm">Running Document Parser OCR Pipeline...</p>
                    </div>
                  )
                )}
              </CardContent>
            </Card>
          ) : (
            <div className="border border-slate-200 rounded-lg p-20 bg-slate-50/50 flex flex-col items-center justify-center text-slate-400 text-center h-full">
              <Eye className="h-10 w-10 mb-2 stroke-1 text-slate-400" />
              <p className="text-sm font-semibold">Inspect OCR results</p>
              <p className="text-xs text-slate-400 mt-1 max-w-xs">
                Select a document from the queue list to inspect extracted text layout breakdowns, confidence scores, and processing logs.
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
