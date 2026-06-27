'use client'

import { useState, useEffect } from 'react'
import { useAuthStore } from '@/stores/auth'
import { reportService, ReportResponse, ReportOcrData } from '@/services/report.service'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  FileText,
  Upload,
  Trash2,
  RefreshCw,
  Clock,
  CheckCircle,
  AlertCircle,
  Eye,
  Settings,
  AlertTriangle,
  FolderOpen
} from 'lucide-react'

export default function PatientRecordsPage() {
  const { user } = useAuthStore()
  const [reports, setReports] = useState<ReportResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [reportType, setReportType] = useState('other')
  
  // Inspection Modal States
  const [inspectingReport, setInspectingReport] = useState<ReportResponse | null>(null)
  const [ocrData, setOcrData] = useState<ReportOcrData | null>(null)
  const [loadingOcr, setLoadingOcr] = useState(false)

  const fetchReports = async () => {
    try {
      setLoading(true)
      const data = await reportService.getReports(user?.id)
      setReports(data.reverse())
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (user?.id) {
      fetchReports()
    }
  }, [user?.id])

  // Poll status for processing reports periodically
  useEffect(() => {
    const processingReports = reports.filter(r => r.ocr_status === 'processing' || r.ocr_status === 'pending')
    if (processingReports.length === 0) return

    const interval = setInterval(async () => {
      let updated = false
      const copy = [...reports]
      for (let i = 0; i < copy.length; i++) {
        const r = copy[i]
        if (r.ocr_status === 'processing' || r.ocr_status === 'pending') {
          try {
            const statusData = await reportService.getProcessingStatus(r.id)
            if (statusData.ocr_status !== r.ocr_status) {
              // Reload whole list to get updated texts
              updated = true
            }
          } catch (e) {
            console.error(e)
          }
        }
      }
      if (updated) {
        fetchReports()
      }
    }, 4000)

    return () => clearInterval(interval)
  }, [reports])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0])
    }
  }

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedFile || !user?.id) return

    try {
      setUploading(true)
      await reportService.uploadReport(user.id, reportType, selectedFile)
      setSelectedFile(null)
      fetchReports()
    } catch (e: any) {
      alert(`Upload failed: ${e.response?.data?.message || e.message}`)
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (reportId: string) => {
    if (!confirm('Are you sure you want to delete this report record?')) return
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

  const handleRetry = async (reportId: string) => {
    try {
      await reportService.processReport(reportId)
      fetchReports()
    } catch (e) {
      console.error(e)
    }
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-4 md:p-6 bg-slate-50 min-h-screen">
      {/* Header section */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
          <FileText className="h-8 w-8 text-teal-600" />
          My Medical Reports
        </h1>
        <p className="text-slate-500 mt-1">
          Upload and review medical laboratory tests, scans, or prescriptions.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Upload New File */}
        <div className="space-y-6 lg:col-span-1">
          <Card className="border border-slate-200 shadow-sm bg-white">
            <CardHeader className="pb-3 border-b border-slate-100 bg-slate-50/50">
              <CardTitle className="text-sm font-bold text-slate-800 uppercase tracking-wider">
                Upload New Report
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <form onSubmit={handleUpload} className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-slate-500 block uppercase mb-2">
                    Report Type / Category
                  </label>
                  <select
                    value={reportType}
                    onChange={(e) => setReportType(e.target.value)}
                    className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                  >
                    <option value="blood_test">Blood Test Result</option>
                    <option value="prescription">Prescription Document</option>
                    <option value="imaging">Imaging (X-Ray/MRI/CT)</option>
                    <option value="discharge_summary">Discharge Summary</option>
                    <option value="other">Other Medical Document</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-500 block uppercase mb-2">
                    File Attachment (PDF, PNG, JPG, JPEG)
                  </label>
                  <div className="border-2 border-dashed border-slate-200 rounded-lg p-6 flex flex-col items-center justify-center bg-slate-50 hover:bg-slate-100/50 transition-colors cursor-pointer relative">
                    <Input
                      type="file"
                      accept=".pdf,.png,.jpg,.jpeg"
                      onChange={handleFileChange}
                      className="absolute inset-0 opacity-0 cursor-pointer"
                    />
                    <Upload className="h-8 w-8 text-slate-400 mb-2" />
                    <span className="text-xs font-bold text-slate-600">
                      {selectedFile ? selectedFile.name : 'Click to select or drag file here'}
                    </span>
                    <span className="text-[10px] text-slate-400 mt-1">
                      Max file size: 10MB
                    </span>
                  </div>
                </div>

                <Button
                  type="submit"
                  disabled={!selectedFile || uploading}
                  className="w-full bg-teal-600 hover:bg-teal-700 text-white font-semibold flex items-center justify-center gap-2 shadow-sm"
                >
                  {uploading ? (
                    <>
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      Uploading Document...
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4" />
                      Submit to Processing Queue
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Reports List */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="border border-slate-200 shadow-sm bg-white">
            <CardHeader className="pb-3 border-b border-slate-100 bg-slate-50/50 flex flex-row items-center justify-between">
              <CardTitle className="text-sm font-bold text-slate-800 uppercase tracking-wider">
                My Ingested Documents
              </CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={fetchReports}
                className="text-slate-500 hover:text-slate-800"
              >
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              </Button>
            </CardHeader>
            <CardContent className="pt-6">
              {loading ? (
                <div className="flex flex-col items-center justify-center py-20 text-slate-500">
                  <RefreshCw className="h-8 w-8 animate-spin text-teal-600 mb-2" />
                  <p className="text-sm font-semibold">Loading documents list...</p>
                </div>
              ) : reports.length === 0 ? (
                <div className="text-center py-20 text-slate-400">
                  <FolderOpen className="h-12 w-12 mx-auto mb-2 stroke-1 text-slate-400" />
                  <p className="text-sm">No medical reports found. Upload your first document above.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {reports.map((report) => (
                    <div
                      key={report.id}
                      className="border border-slate-200 rounded-lg p-4 bg-white hover:shadow-sm transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
                    >
                      <div className="space-y-1.5">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-bold text-slate-900">
                            {report.file_url.split('/').pop()?.split('_').pop() || 'Medical Report'}
                          </span>
                          <span className="text-[10px] font-mono font-bold bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded uppercase">
                            {report.report_type.replace('_', ' ')}
                          </span>
                        </div>
                        <div className="text-xs text-slate-500 flex flex-wrap gap-x-4 gap-y-1">
                          <span>Uploaded: {new Date(report.created_at).toLocaleDateString()}</span>
                          {report.page_count && <span>Pages: {report.page_count}</span>}
                          {report.ocr_average_confidence && (
                            <span>Confidence: {(report.ocr_average_confidence * 100).toFixed(0)}%</span>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-3 justify-end">
                        {/* Process status badges */}
                        {report.ocr_status === 'pending' && (
                          <span className="text-xs font-semibold text-slate-500 flex items-center gap-1 bg-slate-100 px-2 py-1 rounded">
                            <Clock className="h-3.5 w-3.5 animate-pulse" /> Pending
                          </span>
                        )}
                        {report.ocr_status === 'processing' && (
                          <span className="text-xs font-semibold text-amber-600 flex items-center gap-1 bg-amber-50 px-2 py-1 rounded">
                            <RefreshCw className="h-3.5 w-3.5 animate-spin" /> Processing
                          </span>
                        )}
                        {report.ocr_status === 'completed' && (
                          <span className="text-xs font-semibold text-emerald-600 flex items-center gap-1 bg-emerald-50 px-2 py-1 rounded">
                            <CheckCircle className="h-3.5 w-3.5" /> Ready
                          </span>
                        )}
                        {report.ocr_status === 'failed' && (
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-semibold text-red-600 flex items-center gap-1 bg-red-50 px-2 py-1 rounded">
                              <AlertCircle className="h-3.5 w-3.5" /> Failed
                            </span>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleRetry(report.id)}
                              className="px-2 py-1 h-auto text-[10px] text-teal-700 hover:bg-teal-50 border-teal-200"
                            >
                              Retry
                            </Button>
                          </div>
                        )}

                        <div className="flex items-center gap-1 border-l border-slate-200 pl-3">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleInspect(report)}
                            className="p-1 h-auto text-slate-500 hover:text-teal-600"
                            title="Inspect OCR results"
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(report.id)}
                            className="p-1 h-auto text-slate-400 hover:text-red-600"
                            title="Delete report"
                          >
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

          {/* Modal / Section: Document Inspection */}
          {inspectingReport && (
            <Card className="border-2 border-teal-500 shadow-md bg-white">
              <CardHeader className="pb-3 border-b border-slate-100 bg-teal-50/20 flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                    <Eye className="h-4 w-4 text-teal-600" />
                    Inspect OCR Details
                  </CardTitle>
                  <span className="text-xs text-slate-500 mt-1 block">
                    ID: {inspectingReport.id} | Status: {inspectingReport.ocr_status?.toUpperCase()}
                  </span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setInspectingReport(null)}
                  className="text-slate-400 hover:text-slate-800"
                >
                  Close Inspection
                </Button>
              </CardHeader>
              <CardContent className="pt-6 space-y-6">
                {inspectingReport.ocr_status === 'failed' && (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <h4 className="text-xs font-bold text-red-800 uppercase flex items-center gap-1.5 mb-2">
                      <AlertTriangle className="h-4 w-4 text-red-600" />
                      Document Pipeline Failure Logs
                    </h4>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-red-800 font-semibold">
                      {inspectingReport.processing_errors && inspectingReport.processing_errors.length > 0 ? (
                        inspectingReport.processing_errors.map((e, idx) => <li key={idx}>{e}</li>)
                      ) : (
                        <li>An unknown error occurred during PDF parsing.</li>
                      )}
                    </ul>
                  </div>
                )}

                {loadingOcr ? (
                  <div className="flex flex-col items-center justify-center py-10 text-slate-500">
                    <RefreshCw className="h-6 w-6 animate-spin text-teal-600 mb-2" />
                    <p className="text-xs">Fetching OCR layout content...</p>
                  </div>
                ) : ocrData ? (
                  <div className="space-y-6">
                    {/* Pipeline Telemetry Card */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-slate-50 rounded-lg border border-slate-200 text-xs">
                      <div>
                        <span className="text-slate-400 block uppercase font-semibold">Extraction Method</span>
                        <strong className="text-slate-800 font-mono mt-0.5 block uppercase">{ocrData.metadata.ocr_method}</strong>
                      </div>
                      <div>
                        <span className="text-slate-400 block uppercase font-semibold">Page Count</span>
                        <strong className="text-slate-800 mt-0.5 block">{ocrData.metadata.page_count} pages</strong>
                      </div>
                      <div>
                        <span className="text-slate-400 block uppercase font-semibold">Average Confidence</span>
                        <strong className="text-slate-800 mt-0.5 block">{(ocrData.metadata.ocr_average_confidence * 100).toFixed(1)}%</strong>
                      </div>
                      <div>
                        <span className="text-slate-400 block uppercase font-semibold">OCR Version</span>
                        <strong className="text-slate-800 font-mono mt-0.5 block">{ocrData.metadata.ocr_version}</strong>
                      </div>
                    </div>

                    {/* Page breakdown timeline */}
                    {ocrData.ocr_pages && ocrData.ocr_pages.length > 0 && (
                      <div className="space-y-3">
                        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">Page Breakdown Breakdown</span>
                        <div className="space-y-3">
                          {ocrData.ocr_pages.map((page, idx) => (
                            <div key={idx} className="border border-slate-200 rounded-md p-4 bg-white text-xs space-y-3 shadow-xs">
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
                              <pre className="bg-slate-900 text-teal-400 p-3 rounded font-mono text-[11px] overflow-x-auto whitespace-pre-wrap max-h-36">
                                {page.normalized_text}
                              </pre>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Full layout parsed view */}
                    <div className="space-y-2">
                      <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">Full Extracted Text (Normalized)</span>
                      <pre className="bg-slate-950 text-slate-200 p-4 rounded-lg font-mono text-[11px] overflow-auto max-h-72 whitespace-pre-wrap border border-slate-800">
                        {ocrData.normalized_text}
                      </pre>
                    </div>
                  </div>
                ) : (
                  inspectingReport.ocr_status === 'processing' && (
                    <div className="text-center py-8 text-slate-500">
                      <RefreshCw className="h-6 w-6 animate-spin text-teal-600 mx-auto mb-2" />
                      <p className="text-xs">Document parser is currently running. Results will display here automatically.</p>
                    </div>
                  )
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
