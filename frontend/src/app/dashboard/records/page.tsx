'use client'

import { useState, useEffect } from 'react'
import { useAuthStore } from '@/stores/auth'
import { reportService, ReportResponse, ReportOcrData } from '@/services/report.service'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  FileText,
  Upload,
  Trash2,
  RefreshCw,
  Clock,
  CheckCircle,
  AlertCircle,
  Eye,
  AlertTriangle,
  FolderOpen,
  Cpu,
  User,
  Activity,
  Heart,
  Shield,
  Layers,
  Zap,
  CheckSquare,
  HelpCircle
} from 'lucide-react'

export default function PatientRecordsPage() {
  const { user } = useAuthStore()
  const [reports, setReports] = useState<ReportResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [reportType, setReportType] = useState('other')
  
  // Inspection Panel States
  const [inspectingReport, setInspectingReport] = useState<ReportResponse | null>(null)
  const [ocrData, setOcrData] = useState<ReportOcrData | null>(null)
  const [structuredData, setStructuredData] = useState<any>(null)
  const [riskData, setRiskData] = useState<any>(null)
  const [summaryData, setSummaryData] = useState<any>(null)
  const [insightsData, setInsightsData] = useState<any>(null)
  const [patientMemory, setPatientMemory] = useState<any | null>(null)
  const [reportSyncStatus, setReportSyncStatus] = useState<any | null>(null)
  const [loadingOcr, setLoadingOcr] = useState(false)
  const [loadingExtraction, setLoadingExtraction] = useState(false)
  const [loadingRisk, setLoadingRisk] = useState(false)
  const [loadingSummary, setLoadingSummary] = useState(false)
  const [loadingSync, setLoadingSync] = useState(false)
  const [inspectTab, setInspectTab] = useState<'structured' | 'ocr' | 'labs' | 'meds' | 'risk' | 'summary'>('summary')

  const fetchReports = async () => {
    try {
      setLoading(true)
      const data = await reportService.getReports(user?.id)
      setReports(data.reverse())
      try {
        const mem = await reportService.getPatientMemory()
        setPatientMemory(mem)
      } catch (err) {
        console.error('Failed to load patient memory profile', err)
      }
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
    const processing = reports.filter(
      r => r.ocr_status === 'processing' || 
           r.ocr_status === 'pending' || 
           r.extraction_status === 'processing' ||
           r.processing_status === 'processing'
    )
    if (processing.length === 0) return

    const interval = setInterval(async () => {
      let updated = false
      const copy = [...reports]
      for (let i = 0; i < copy.length; i++) {
        const r = copy[i]
        if (r.ocr_status === 'processing' || r.ocr_status === 'pending' || r.extraction_status === 'processing' || r.processing_status === 'processing') {
          try {
            const statusData = await reportService.getProcessingStatus(r.id)
            const structData = await reportService.getStructuredData(r.id)
            if (statusData.ocr_status !== r.ocr_status || structData.extraction_status !== r.extraction_status || structData.processing_status !== r.processing_status) {
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
    setStructuredData(null)
    setRiskData(null)
    setSummaryData(null)
    setInsightsData(null)
    setInspectTab(report.patient_summary || report.ai_summary ? 'summary' : report.overall_risk ? 'risk' : report.extraction_status === 'completed' ? 'structured' : 'ocr')

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
        const rDetails = await reportService.getReportRisks(report.id)
        setRiskData(rDetails)
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
          console.error("Failed to load sync status", syncErr)
        }
      } catch (e) {
        console.error(e)
      } finally {
        setLoadingSummary(false)
      }
    }
  }

  const handleSynchronizeReport = async (reportId: string) => {
    try {
      setLoadingSync(true)
      await reportService.synchronizeReport(reportId)
      const sync = await reportService.getReportSyncStatus(reportId)
      setReportSyncStatus(sync)
      
      const mem = await reportService.getPatientMemory()
      setPatientMemory(mem)
    } catch (err) {
      console.error(err)
    } finally {
      setLoadingSync(false)
    }
  }

  const handleGenerateSummary = async (reportId: string) => {
    try {
      setLoadingSummary(true)
      await reportService.summarizeReport(reportId)
      fetchReports()
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

  const handleExtract = async (reportId: string) => {
    try {
      setLoadingExtraction(true)
      await reportService.extractReport(reportId)
      fetchReports()
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
      fetchReports()
      setTimeout(async () => {
        const struct = await reportService.getStructuredData(reportId)
        setStructuredData(struct)
        const rDetails = await reportService.getReportRisks(reportId)
        setRiskData(rDetails)
      }, 2000)
    } catch (e) {
      console.error(e)
    } finally {
      setLoadingRisk(false)
    }
  }

  const handleRetryOcr = async (reportId: string) => {
    try {
      await reportService.processReport(reportId)
      fetchReports()
    } catch (e) {
      console.error(e)
    }
  }

  // Risk Color Class Mapper
  const getRiskHeaderColor = (risk: string) => {
    const r = risk?.toUpperCase()
    if (r === 'CRITICAL') return 'bg-red-600 border-red-700 text-white'
    if (r === 'HIGH') return 'bg-orange-500 border-orange-600 text-white'
    if (r === 'MEDIUM') return 'bg-amber-400 border-amber-500 text-slate-900'
    if (r === 'LOW') return 'bg-sky-500 border-sky-600 text-white'
    return 'bg-emerald-600 border-emerald-700 text-white'
  }

  const getRiskBadgeColor = (risk: string) => {
    const r = risk?.toUpperCase()
    if (r === 'CRITICAL') return 'bg-red-50 text-red-700 border border-red-200'
    if (r === 'HIGH') return 'bg-orange-50 text-orange-700 border border-orange-200'
    if (r === 'MEDIUM') return 'bg-amber-50 text-amber-700 border border-amber-200'
    if (r === 'LOW') return 'bg-sky-50 text-sky-700 border border-sky-200'
    return 'bg-emerald-50 text-emerald-700 border border-emerald-200'
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-4 md:p-6 bg-slate-50 min-h-screen">
      {/* Header section */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
          <FileText className="h-8 w-8 text-teal-600" />
          My Medical Records & Diagnostics
        </h1>
      </div>

      {patientMemory && (
        <Card className="border border-teal-200 bg-gradient-to-r from-teal-50/40 to-cyan-50/40 shadow-xs">
          <CardContent className="p-5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-[10px] font-bold text-teal-800 uppercase tracking-wider bg-teal-100/80 px-2 py-0.5 rounded">
                  AI Patient Health Memory
                </span>
                <span className="text-slate-400 text-xs font-semibold">•</span>
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                  Sync Status: Synchronized (v{patientMemory.summary_version})
                </span>
              </div>
              <h3 className="font-bold text-slate-800 text-sm">Longitudinal Health Summary</h3>
              <p className="text-xs text-slate-600 leading-relaxed max-w-4xl">
                {patientMemory.longitudinal_summary || patientMemory.ai_summary || 'Aggregating patient medical data...'}
              </p>
            </div>
            <div className="flex flex-col text-right items-end text-xs text-slate-400 font-medium space-y-1 bg-white/70 border border-slate-100 rounded-lg p-3 w-full md:w-auto shrink-0">
              <div>Last Synced: {patientMemory.last_updated ? new Date(patientMemory.last_updated).toLocaleString() : 'N/A'}</div>
              <div>Report summaries: {patientMemory.report_summaries?.length ?? 0} • Diagnoses: {patientMemory.diagnoses?.length ?? 0}</div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Upload */}
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
                  <p className="text-sm">No medical records found. Upload a report file to start.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {reports.map((report) => (
                    <div
                      key={report.id}
                      className="border border-slate-200 rounded-lg p-4 bg-white hover:shadow-sm transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-bold text-slate-900">
                            {report.file_url.split('/').pop()?.split('_').pop() || 'Medical Report'}
                          </span>
                          {report.document_type && (
                            <Badge className="bg-teal-50 text-teal-700 border border-teal-200 hover:bg-teal-50 rounded">
                              {report.document_type}
                            </Badge>
                          )}
                          {report.overall_risk && (
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${getRiskBadgeColor(report.overall_risk)}`}>
                              Risk: {report.overall_risk}
                            </span>
                          )}
                        </div>
                        <div className="text-[11px] text-slate-500 flex flex-wrap gap-x-4">
                          <span>Uploaded: {new Date(report.created_at).toLocaleDateString()}</span>
                          {report.page_count && <span>Pages: {report.page_count}</span>}
                          {report.extraction_confidence && (
                            <span>Confidence: {(report.extraction_confidence * 100).toFixed(0)}%</span>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-3 justify-end">
                        {/* Status badges */}
                        {report.ocr_status !== 'completed' ? (
                          <span className="text-xs font-semibold text-slate-500 flex items-center gap-1 bg-slate-100 px-2 py-1 rounded">
                            <Clock className="h-3.5 w-3.5 animate-pulse" /> OCR Pending
                          </span>
                        ) : report.extraction_status !== 'completed' ? (
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-bold text-slate-500 bg-slate-100 px-2 py-1 rounded flex items-center gap-1">
                              <Clock className="h-3 w-3" /> Struct Pending
                            </span>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleExtract(report.id)}
                              className="px-2 py-1 h-auto text-[10px] text-teal-700 hover:bg-teal-50 border-teal-200"
                            >
                              Extract
                            </Button>
                          </div>
                        ) : !report.overall_risk ? (
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-bold text-slate-500 bg-slate-100 px-2 py-1 rounded flex items-center gap-1">
                              <Clock className="h-3 w-3" /> Risk Pending
                            </span>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleRunRiskAnalysis(report.id)}
                              className="px-2 py-1 h-auto text-[10px] text-orange-700 hover:bg-orange-50 border-orange-200"
                            >
                              Analyze Risk
                            </Button>
                          </div>
                        ) : (
                          <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded flex items-center gap-1">
                            <CheckCircle className="h-3 w-3" /> Risk Checked
                          </span>
                        )}

                        <div className="flex items-center gap-1 border-l border-slate-200 pl-3">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleInspect(report)}
                            className="p-1 h-auto text-slate-500 hover:text-teal-600"
                            title="Inspect Details"
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(report.id)}
                            className="p-1 h-auto text-slate-400 hover:text-red-600"
                            title="Delete"
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

          {/* Detailed Document Inspection Panel */}
          {inspectingReport && (
            <Card className="border-2 border-teal-500 shadow-md bg-white">
              <CardHeader className="pb-3 border-b border-slate-100 bg-teal-50/20 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <CardTitle className="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                    <Layers className="h-4 w-4 text-teal-600" />
                    Structured Clinical Inspector
                  </CardTitle>
                  <span className="text-xs text-slate-500 mt-1 block">
                    File: {inspectingReport.file_url.split('/').pop()?.substring(14) || 'record'}
                  </span>
                </div>

                <div className="flex flex-wrap gap-2">
                  {[
                    { id: 'summary', name: 'AI Summary' },
                    { id: 'risk', name: 'Clinical Risk' },
                    { id: 'structured', name: 'Profile Summary' },
                    { id: 'labs', name: 'Lab Results' },
                    { id: 'meds', name: 'Prescribed Drugs' },
                    { id: 'ocr', name: 'Raw OCR Text' }
                  ].map((tab) => (
                    <Button
                      key={tab.id}
                      variant={inspectTab === tab.id ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setInspectTab(tab.id as any)}
                      className={`h-8 text-xs font-semibold ${
                        inspectTab === tab.id ? 'bg-teal-600 hover:bg-teal-700 text-white' : ''
                      }`}
                    >
                      {tab.name}
                    </Button>
                  ))}
                </div>
              </CardHeader>

              <CardContent className="pt-6">
                {/* AI Summary Tab */}
                {inspectTab === 'summary' && (
                  <div className="space-y-6">
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">AI Report Summarization</span>
                      {inspectingReport.overall_risk && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleGenerateSummary(inspectingReport.id)}
                          className="h-7 text-[10px] text-teal-700 border-teal-200"
                          disabled={loadingSummary}
                        >
                          {summaryData ? 'Re-run Summarization' : 'Generate AI Summary'}
                        </Button>
                      )}
                    </div>

                    {loadingSummary ? (
                      <div className="text-center py-10 bg-white border border-slate-200 rounded-lg shadow-sm">
                        <RefreshCw className="h-6 w-6 animate-spin text-teal-600 mx-auto mb-2" />
                        <p className="text-xs text-slate-500 font-medium">Synthesizing clinical observations & patient explanations...</p>
                      </div>
                    ) : summaryData ? (
                      <div className="space-y-6 text-xs text-slate-700">
                        {/* Executive AI Summary Card */}
                        <div className="p-5 rounded-lg border border-teal-100 bg-gradient-to-r from-teal-50/50 to-cyan-50/50 shadow-xs space-y-2">
                          <div className="flex justify-between items-start">
                            <div>
                              <span className="text-[9px] uppercase font-bold text-teal-800 tracking-wider">Executive Overview</span>
                              <h4 className="text-sm font-bold text-slate-800 mt-0.5">Clinical Analysis Summary</h4>
                            </div>
                            <Badge className="bg-teal-100 text-teal-800 border-teal-200 rounded hover:bg-teal-100 font-semibold text-[9px]">
                              Confidence: {(summaryData.summary_confidence * 100).toFixed(0)}%
                            </Badge>
                          </div>
                          <p className="text-slate-700 text-xs leading-relaxed font-medium mt-1">
                            {summaryData.ai_summary}
                          </p>
                          <div className="text-[9px] text-slate-400 mt-2 flex justify-between">
                            <span>Template version: {summaryData.summary_version}</span>
                            {summaryData.summary_generated_at && (
                              <span>Generated: {new Date(summaryData.summary_generated_at).toLocaleString()}</span>
                            )}
                          </div>
                        </div>

                        {/* Synchronization Status Details */}
                        <Card className="border border-slate-200 shadow-xs bg-white">
                          <CardHeader className="py-2.5 bg-slate-50/50 border-b border-slate-100 flex flex-row items-center justify-between">
                            <CardTitle className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                              <Cpu className="h-3.5 w-3.5 text-teal-600" />
                              Knowledge Synchronization Status
                            </CardTitle>
                            {reportSyncStatus?.in_sync ? (
                              <Badge className="bg-emerald-50 text-emerald-800 border-emerald-200">Synchronized</Badge>
                            ) : (
                              <Badge className="bg-amber-50 text-amber-800 border-amber-200">Out of Sync</Badge>
                            )}
                          </CardHeader>
                          <CardContent className="pt-3 pb-3 space-y-2">
                            <p className="text-xs text-slate-500 leading-relaxed">
                              Synchronize this processed report&apos;s summaries and structured parameters with the longitudinal AI Patient Memory and Qdrant semantic vector index.
                            </p>
                            {reportSyncStatus?.validation_details && (
                              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 bg-slate-50 p-2.5 rounded border border-slate-100 text-[10px] font-mono">
                                <div>Memory: <span className="font-bold text-slate-700">{reportSyncStatus.validation_details.mongodb_memory_status}</span></div>
                                <div>Indexed chunks: <span className="font-bold text-slate-700">{reportSyncStatus.validation_details.qdrant_points_status}</span></div>
                                <div>Compatible: <span className="font-bold text-slate-700">{reportSyncStatus.validation_details.version_synchronized ? 'Yes' : 'No'}</span></div>
                              </div>
                            )}
                            <div className="flex gap-2">
                              <Button
                                size="sm"
                                onClick={() => handleSynchronizeReport(inspectingReport.id)}
                                className="bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold h-8"
                                disabled={loadingSync}
                              >
                                {loadingSync ? 'Synchronizing...' : 'Synchronize Now'}
                              </Button>
                            </div>
                          </CardContent>
                        </Card>

                        {/* Patient Explanation */}
                        <Card className="border border-slate-100 shadow-xs">
                          <CardHeader className="py-3 bg-slate-50/50 border-b border-slate-100">
                            <CardTitle className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                              <Heart className="h-3.5 w-3.5 text-rose-500" />
                              Patient-Friendly Explanation
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="pt-4 pb-4">
                            <p className="text-xs leading-relaxed text-slate-600 whitespace-pre-line">
                              {summaryData.patient_summary}
                            </p>
                          </CardContent>
                        </Card>

                        {/* Key Findings & Follow-up Questions Grid */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                          {/* Key Findings */}
                          <div className="space-y-3">
                            <span className="font-bold uppercase text-slate-500 tracking-wider text-[10px] flex items-center gap-1.5">
                              <CheckSquare className="h-3.5 w-3.5 text-teal-600" />
                              Important Observations & Findings
                            </span>
                            {insightsData && insightsData.key_findings && insightsData.key_findings.length > 0 ? (
                              <div className="space-y-2">
                                {insightsData.key_findings.map((finding: string, idx: number) => (
                                  <div key={idx} className="flex items-start gap-2 p-2 border border-slate-100 bg-white rounded shadow-2xs">
                                    <div className="h-4 w-4 bg-teal-50 text-teal-600 rounded flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5">✓</div>
                                    <span className="text-slate-600 text-xs leading-relaxed">{finding}</span>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="p-4 border border-dashed rounded text-center text-slate-400 bg-slate-50">
                                No key findings generated.
                              </div>
                            )}
                          </div>

                          {/* Suggested questions */}
                          <div className="space-y-3">
                            <span className="font-bold uppercase text-slate-500 tracking-wider text-[10px] flex items-center gap-1.5">
                              <HelpCircle className="h-3.5 w-3.5 text-teal-600" />
                              Suggested Doctor Questions
                            </span>
                            {insightsData && insightsData.followup_questions && insightsData.followup_questions.length > 0 ? (
                              <div className="space-y-2">
                                {insightsData.followup_questions.map((q: string, idx: number) => (
                                  <div key={idx} className="p-3 border border-indigo-50 bg-indigo-50/10 rounded-lg flex items-start gap-2 shadow-2xs">
                                    <HelpCircle className="h-4 w-4 text-indigo-500 shrink-0 mt-0.5" />
                                    <span className="text-slate-700 font-medium text-[11px] leading-relaxed">{q}</span>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="p-4 border border-dashed rounded text-center text-slate-400 bg-slate-50">
                                No suggested questions available.
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="p-8 border border-dashed rounded-lg text-center text-slate-500 bg-slate-50 space-y-3">
                        <Zap className="h-8 w-8 text-amber-500 mx-auto" />
                        <h4 className="font-bold text-sm text-slate-800">AI Summary Not Generated Yet</h4>
                        <p className="text-xs text-slate-400 max-w-sm mx-auto leading-relaxed">
                          This report has not been summarised using AI. Clinically analyze the report inputs to synthesize patient and doctor descriptions.
                        </p>
                        {inspectingReport.overall_risk ? (
                          <Button
                            variant="default"
                            size="sm"
                            onClick={() => handleGenerateSummary(inspectingReport.id)}
                            className="bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs mt-2"
                          >
                            Generate AI Summary
                          </Button>
                        ) : (
                          <div className="text-[10px] text-amber-600 font-bold bg-amber-50 rounded p-2 inline-block">
                            Please calculate Clinical Risk under the &quot;Clinical Risk&quot; tab first.
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Clinical Risk Tab */}
                {inspectTab === 'risk' && (
                  <div className="space-y-6">
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Clinical Risk Diagnostics</span>
                      {inspectingReport.extraction_status === 'completed' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleRunRiskAnalysis(inspectingReport.id)}
                          className="h-7 text-[10px] text-orange-700 border-orange-200"
                          disabled={loadingRisk}
                        >
                          Run Risk Analysis
                        </Button>
                      )}
                    </div>

                    {loadingRisk ? (
                      <div className="text-center py-10">
                        <RefreshCw className="h-6 w-6 animate-spin text-teal-600 mx-auto mb-2" />
                        <p className="text-xs text-slate-500">Calculating clinical risks & scoring models...</p>
                      </div>
                    ) : riskData ? (
                      <div className="space-y-6 text-xs text-slate-700">
                        {/* Overall Risk Card Banner */}
                        <div className={`p-5 rounded-lg border flex flex-col md:flex-row justify-between items-start md:items-center gap-4 ${getRiskHeaderColor(riskData.overall_risk)}`}>
                          <div>
                            <span className="text-[10px] uppercase font-bold tracking-wider opacity-85">Aggregate Severity Status</span>
                            <h3 className="text-2xl font-black tracking-wide mt-1 uppercase flex items-center gap-2">
                              <Shield className="h-6 w-6 shrink-0" />
                              {riskData.overall_risk} RISK
                            </h3>
                          </div>
                          <div className="bg-white/15 px-4 py-2.5 rounded border border-white/10 text-right">
                            <span className="text-[9px] uppercase font-bold tracking-wider block opacity-80">Risk Score Metric</span>
                            <span className="text-2xl font-black block mt-0.5">{riskData.risk_score.toFixed(0)} / 100</span>
                          </div>
                        </div>

                        {/* Triggered clinical flags list */}
                        {riskData.clinical_flags && riskData.clinical_flags.length > 0 && (
                          <div className="space-y-2">
                            <span className="font-bold uppercase text-slate-500 tracking-wider text-[10px] block">Triggered Risk Flags Badges</span>
                            <div className="flex flex-wrap gap-2">
                              {riskData.clinical_flags.map((flg: string, idx: number) => (
                                <Badge key={idx} className="bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-50 font-bold uppercase rounded py-1">
                                  <AlertCircle className="h-3 w-3 mr-1" />
                                  {flg.replace('_', ' ')}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}

                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                          {/* Identified Specific Findings */}
                          <div className="space-y-3">
                            <span className="font-bold uppercase text-slate-500 tracking-wider text-[10px] flex items-center gap-1">
                              <Activity className="h-3.5 w-3.5 text-teal-600 animate-pulse" />
                              Key Findings Identified
                            </span>
                            {riskData.risk_findings && riskData.risk_findings.length > 0 ? (
                              <div className="space-y-3">
                                {riskData.risk_findings.map((f: any, idx: number) => (
                                  <div key={idx} className="p-3 border rounded bg-white shadow-xs space-y-2">
                                    <div className="flex justify-between items-center border-b pb-1.5">
                                      <strong className="text-slate-900">{f.finding_name}</strong>
                                      <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${getRiskBadgeColor(f.severity)}`}>
                                        {f.severity}
                                      </span>
                                    </div>
                                    <p className="text-slate-600 text-[11px] leading-relaxed">{f.explanation}</p>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="p-4 border border-dashed rounded text-center text-slate-400 bg-slate-50">
                                No diagnostic rule findings matches. All parameter values are within standard thresholds.
                              </div>
                            )}
                          </div>

                          {/* Actionable Recommendations List */}
                          <div className="space-y-3">
                            <span className="font-bold uppercase text-slate-500 tracking-wider text-[10px] flex items-center gap-1">
                              <CheckSquare className="h-3.5 w-3.5 text-teal-600" />
                              Actionable Suggestions
                            </span>
                            {riskData.recommendations && riskData.recommendations.length > 0 ? (
                              <div className="space-y-3">
                                {riskData.recommendations.map((rec: any, idx: number) => (
                                  <div key={idx} className="p-3 border rounded bg-white shadow-xs space-y-2 border-l-4 border-l-teal-500">
                                    <div className="flex justify-between items-center border-b pb-1.5">
                                      <strong className="text-slate-900 uppercase text-[10px]">{rec.recommendation_type}</strong>
                                      <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                                        rec.urgency === 'IMMEDIATE' ? 'bg-red-50 text-red-700 border border-red-200' :
                                        rec.urgency === 'SOON' ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                                        'bg-slate-50 text-slate-600 border border-slate-200'
                                      }`}>
                                        {rec.urgency}
                                      </span>
                                    </div>
                                    <p className="text-slate-600 text-[11px] leading-relaxed font-medium">{rec.description}</p>
                                    <p className="text-[9px] text-slate-400 italic font-mono pt-1 border-t border-slate-100">{rec.disclaimer}</p>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="p-4 border border-dashed rounded text-center text-slate-400 bg-slate-50">
                                No recommendations generated.
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-20 border border-dashed rounded-lg text-slate-400 bg-slate-50/50">
                        <Shield className="h-10 w-10 mx-auto text-slate-300 mb-2 stroke-1" />
                        <p className="text-sm">No clinical risk calculations compiled yet.</p>
                      </div>
                    )}
                  </div>
                )}

                {/* Structured Overview Tab */}
                {inspectTab === 'structured' && (
                  <div className="space-y-6">
                    {loadingExtraction ? (
                      <div className="text-center py-10">
                        <RefreshCw className="h-6 w-6 animate-spin text-teal-600 mx-auto mb-2" />
                        <p className="text-xs text-slate-500">Loading structured clinical metadata...</p>
                      </div>
                    ) : structuredData ? (
                      <div className="space-y-6 text-xs text-slate-700">
                        {/* Warnings banner */}
                        {structuredData.extraction_warnings && structuredData.extraction_warnings.length > 0 && (
                          <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                            <h4 className="font-bold text-amber-800 uppercase flex items-center gap-1.5 mb-2">
                              <AlertTriangle className="h-4 w-4 text-amber-600" />
                              Validation Alerts ({structuredData.extraction_warnings.length})
                            </h4>
                            <ul className="list-disc pl-4 space-y-1 text-amber-800 font-semibold leading-relaxed">
                              {structuredData.extraction_warnings.map((w: string, idx: number) => (
                                <li key={idx}>{w}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          {/* Patient demographic details */}
                          <Card className="border border-slate-200 shadow-none bg-slate-50/50">
                            <CardHeader className="py-2.5 border-b bg-slate-100/35">
                              <span className="font-bold uppercase text-slate-600 flex items-center gap-1.5">
                                <User className="h-3.5 w-3.5 text-teal-600" />
                                Patient Information
                              </span>
                            </CardHeader>
                            <CardContent className="py-3 space-y-2">
                              <div className="flex justify-between border-b border-slate-200/50 pb-1.5">
                                <span className="text-slate-400">Name</span>
                                <strong className="text-slate-800">{structuredData.patient_information?.patient_name || 'N/A'}</strong>
                              </div>
                              <div className="flex justify-between border-b border-slate-200/50 pb-1.5">
                                <span className="text-slate-400">Age</span>
                                <strong className="text-slate-800">{structuredData.patient_information?.age || 'N/A'}</strong>
                              </div>
                              <div className="flex justify-between border-b border-slate-200/50 pb-1.5">
                                <span className="text-slate-400">Gender</span>
                                <strong className="text-slate-800">{structuredData.patient_information?.gender || 'N/A'}</strong>
                              </div>
                              <div className="flex justify-between pb-0">
                                <span className="text-slate-400">Date of Birth</span>
                                <strong className="text-slate-800">{structuredData.patient_information?.date_of_birth || 'N/A'}</strong>
                              </div>
                            </CardContent>
                          </Card>

                          {/* Clinic hospital records details */}
                          <Card className="border border-slate-200 shadow-none bg-slate-50/50">
                            <CardHeader className="py-2.5 border-b bg-slate-100/35">
                              <span className="font-bold uppercase text-slate-600 flex items-center gap-1.5">
                                <FolderOpen className="h-3.5 w-3.5 text-teal-600" />
                                Facility & Clinic Record
                              </span>
                            </CardHeader>
                            <CardContent className="py-3 space-y-2">
                              <div className="flex justify-between border-b border-slate-200/50 pb-1.5">
                                <span className="text-slate-400">Hospital / Lab</span>
                                <strong className="text-slate-800">
                                  {structuredData.hospital_information?.hospital || structuredData.hospital_information?.laboratory || 'N/A'}
                                </strong>
                              </div>
                              <div className="flex justify-between border-b border-slate-200/50 pb-1.5">
                                <span className="text-slate-400">Consultant Doctor</span>
                                <strong className="text-slate-800">{structuredData.hospital_information?.doctor || 'N/A'}</strong>
                              </div>
                              <div className="flex justify-between border-b border-slate-200/50 pb-1.5">
                                <span className="text-slate-400">Department</span>
                                <strong className="text-slate-800">{structuredData.hospital_information?.department || 'N/A'}</strong>
                              </div>
                              <div className="flex justify-between pb-0">
                                <span className="text-slate-400">Report Date</span>
                                <strong className="text-slate-800">{structuredData.hospital_information?.report_date || 'N/A'}</strong>
                              </div>
                            </CardContent>
                          </Card>
                        </div>

                        {/* Diagnoses and Allergies lists */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <div className="space-y-2">
                            <span className="font-bold uppercase text-slate-500 tracking-wide block">Extracted Diagnoses</span>
                            {structuredData.diagnoses && structuredData.diagnoses.length > 0 ? (
                              <div className="flex flex-wrap gap-2">
                                {structuredData.diagnoses.map((d: string, idx: number) => (
                                  <Badge key={idx} className="bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-50 py-1">
                                    {d}
                                  </Badge>
                                ))}
                              </div>
                            ) : (
                              <span className="text-slate-400 italic">No diagnoses entries extracted.</span>
                            )}
                          </div>

                          <div className="space-y-2">
                            <span className="font-bold uppercase text-slate-500 tracking-wide block">Extracted Allergies</span>
                            {structuredData.allergies && structuredData.allergies.length > 0 ? (
                              <div className="flex flex-wrap gap-2">
                                {structuredData.allergies.map((a: string, idx: number) => (
                                  <Badge key={idx} className="bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-50 py-1">
                                    {a}
                                  </Badge>
                                ))}
                              </div>
                            ) : (
                              <span className="text-slate-400 italic">No allergies entries extracted.</span>
                            )}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-10 text-slate-400">
                        <AlertCircle className="h-8 w-8 mx-auto text-slate-400 mb-2" />
                        <p>No structured medical profile available for this document.</p>
                      </div>
                    )}
                  </div>
                )}

                {/* Laboratory Results Table Tab */}
                {inspectTab === 'labs' && (
                  <div className="space-y-4">
                    {loadingExtraction ? (
                      <div className="text-center py-10">
                        <RefreshCw className="h-6 w-6 animate-spin text-teal-600 mx-auto mb-2" />
                        <p className="text-xs text-slate-500">Retrieving laboratory parameters table...</p>
                      </div>
                    ) : structuredData && structuredData.laboratory_results && structuredData.laboratory_results.length > 0 ? (
                      <div className="border border-slate-200 rounded-lg overflow-hidden bg-white text-xs shadow-xs">
                        <table className="w-full text-left border-collapse">
                          <thead>
                            <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold">
                              <th className="p-3">Investigation Parameter</th>
                              <th className="p-3">Result Value</th>
                              <th className="p-3">Standard Units</th>
                              <th className="p-3">Reference Range</th>
                              <th className="p-3 text-right">Status Alerts</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100 text-slate-700">
                            {structuredData.laboratory_results.map((lab: any, idx: number) => (
                              <tr key={idx} className="hover:bg-slate-50/40 transition-colors">
                                <td className="p-3 font-semibold text-slate-900">{lab.test_name}</td>
                                <td className="p-3 font-mono font-bold text-slate-800">{lab.value}</td>
                                <td className="p-3 font-medium text-slate-500">{lab.unit || '-'}</td>
                                <td className="p-3 font-mono text-slate-500">{lab.reference_range || '-'}</td>
                                <td className="p-3 text-right">
                                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase tracking-wider ${
                                    lab.status === 'CRITICAL_HIGH' || lab.status === 'CRITICAL_LOW' ? 'bg-rose-600 text-white border-rose-700 font-extrabold' :
                                    lab.status === 'HIGH' ? 'bg-red-50 border-red-200 text-red-700' :
                                    lab.status === 'LOW' ? 'bg-amber-50 border-amber-200 text-amber-700' :
                                    'bg-emerald-50 border-emerald-200 text-emerald-700'
                                  }`}>
                                    {lab.status}
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <div className="text-center py-20 border border-dashed rounded-lg text-slate-400 bg-slate-50/50">
                        <Activity className="h-10 w-10 mx-auto text-slate-300 mb-2 stroke-1" />
                        <p className="text-sm">No structured laboratory parameter rows extracted from this document.</p>
                      </div>
                    )}
                  </div>
                )}

                {/* Medication Details Tab */}
                {inspectTab === 'meds' && (
                  <div className="space-y-4">
                    {loadingExtraction ? (
                      <div className="text-center py-10">
                        <RefreshCw className="h-6 w-6 animate-spin text-teal-600 mx-auto mb-2" />
                        <p className="text-xs text-slate-500">Retrieving prescription medications list...</p>
                      </div>
                    ) : structuredData && structuredData.medications && structuredData.medications.length > 0 ? (
                      <div className="border border-slate-200 rounded-lg overflow-hidden bg-white text-xs shadow-xs">
                        <table className="w-full text-left border-collapse">
                          <thead>
                            <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold">
                              <th className="p-3">Drug / Medicine Name</th>
                              <th className="p-3">Dosage Strength</th>
                              <th className="p-3">Administration Frequency</th>
                              <th className="p-3">Treatment Duration</th>
                              <th className="p-3 text-right">Intake Route</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100 text-slate-700">
                            {structuredData.medications.map((med: any, idx: number) => (
                              <tr key={idx} className="hover:bg-slate-50/40 transition-colors">
                                <td className="p-3 font-semibold text-slate-900">{med.medicine}</td>
                                <td className="p-3 font-bold text-slate-800">{med.dosage || '-'}</td>
                                <td className="p-3 font-medium text-slate-500">{med.frequency || '-'}</td>
                                <td className="p-3 text-slate-500">{med.duration || '-'}</td>
                                <td className="p-3 text-right text-slate-500 font-medium">{med.route || 'Oral'}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <div className="text-center py-20 border border-dashed rounded-lg text-slate-400 bg-slate-50/50">
                        <Heart className="h-10 w-10 mx-auto text-slate-300 mb-2 stroke-1" />
                        <p className="text-sm">No structured medication records extracted from this document.</p>
                      </div>
                    )}
                  </div>
                )}

                {/* OCR Raw Text tab */}
                {inspectTab === 'ocr' && (
                  <div className="space-y-6">
                    {loadingOcr ? (
                      <div className="flex flex-col items-center justify-center py-10 text-slate-500">
                        <RefreshCw className="h-6 w-6 animate-spin text-teal-600 mb-2" />
                        <p className="text-xs">Fetching OCR layouts...</p>
                      </div>
                    ) : ocrData ? (
                      <div className="space-y-6">
                        {/* Page list preview */}
                        {ocrData.ocr_pages && ocrData.ocr_pages.length > 0 && (
                          <div className="space-y-3">
                            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">Individual Pages Breakdown</span>
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

                        <div className="space-y-2">
                          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">Full Extracted Text Layout</span>
                          <pre className="bg-slate-950 text-slate-200 p-4 rounded-lg font-mono text-[11px] overflow-auto max-h-72 whitespace-pre-wrap border border-slate-800">
                            {ocrData.normalized_text}
                          </pre>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-10 text-slate-400">
                        <AlertCircle className="h-8 w-8 mx-auto text-slate-400 mb-2" />
                        <p>No OCR layout content found.</p>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
