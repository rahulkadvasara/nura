'use client'

import { useState } from 'react'
import Link from 'next/link'
import {
  Search,
  ArrowUpDown,
  User as UserIcon,
  Stethoscope,
  Calendar,
  ChevronRight,
  Clipboard,
  X,
  Activity,
  Clock,
  Pill,
  AlertCircle,
  MessageSquare,
  FileText,
  UserCheck,
  RefreshCw,
  Shield
} from 'lucide-react'

import { useDoctorPatients, useDoctorPatient } from '@/hooks/use-doctor-patient'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import { reportService } from '@/services/report.service'

export default function DoctorPatientsPage() {
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState('-latest_visit')
  const [limit] = useState(20)
  const [skip, setSkip] = useState(0)
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'insights' | 'history' | 'records'>('insights')
  
  // Reports inspection states
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null)
  const [structuredReport, setStructuredReport] = useState<any>(null)
  const [reportEntities, setReportEntities] = useState<any[] | null>(null)
  const [reportRiskDetails, setReportRiskDetails] = useState<any>(null)
  const [reportSummary, setReportSummary] = useState<any>(null)
  const [reportInsights, setReportInsights] = useState<any>(null)
  const [loadingReportDetails, setLoadingReportDetails] = useState(false)

  const { data: listData, isLoading, isError, error, refetch } = useDoctorPatients({
    search: search || undefined,
    sort_by: sortBy,
    limit,
    skip
  })

  const { data: detailData, isLoading: isDetailLoading, isError: isDetailError } = useDoctorPatient(
    selectedPatientId || ''
  )

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

  const handleOpenDetail = (patientId: string) => {
    setSelectedPatientId(patientId)
    setActiveTab('insights')
    handleCloseReportDetails()
  }

  const handleCloseDetail = () => {
    setSelectedPatientId(null)
    handleCloseReportDetails()
  }

  const handleOpenReportDetails = async (reportId: string) => {
    try {
      setSelectedReportId(reportId)
      setStructuredReport(null)
      setReportEntities(null)
      setReportRiskDetails(null)
      setReportSummary(null)
      setReportInsights(null)
      setLoadingReportDetails(true)
      
      const struct = await reportService.getStructuredData(reportId)
      setStructuredReport(struct)
      
      const ents = await reportService.getEntities(reportId)
      setReportEntities(ents.entities)

      try {
        const risk = await reportService.getReportRisks(reportId)
        setReportRiskDetails(risk)
      } catch (err) {
        console.warn("No report risk details found for this report yet", err)
      }

      try {
        const summary = await reportService.getReportSummary(reportId)
        setReportSummary(summary)
        const insights = await reportService.getReportInsights(reportId)
        setReportInsights(insights)
      } catch (err) {
        console.warn("No AI summary generated for this report yet", err)
      }
    } catch (e) {
      console.error(e)
    } finally {
      setLoadingReportDetails(false)
    }
  }

  const handleCloseReportDetails = () => {
    setSelectedReportId(null)
    setStructuredReport(null)
    setReportEntities(null)
    setReportRiskDetails(null)
    setReportSummary(null)
    setReportInsights(null)
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 relative">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Patients Directory</h1>
          <p className="text-slate-500 mt-1">Manage and view the health profiles and history of patients you have treated.</p>
        </div>
      </div>

      {/* Filters Toolbar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Search patients by name or email..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setSkip(0)
            }}
            className="pl-10 bg-white border-slate-200 focus:border-teal-500 focus:ring-teal-500"
          />
        </div>

        {/* Sorting Dropdown */}
        <div className="flex items-center gap-2">
          <ArrowUpDown className="h-4 w-4 text-slate-500" />
          <select
            value={sortBy}
            onChange={(e) => {
              setSortBy(e.target.value)
              setSkip(0)
            }}
            className="bg-white border border-slate-200 text-slate-700 rounded-md text-sm py-2 pl-3 pr-8 focus:outline-none focus:border-teal-500 focus:ring-teal-500 cursor-pointer"
          >
            <option value="-latest_visit">Sort by: Recent Appointment</option>
            <option value="latest_visit">Sort by: Oldest Appointment</option>
            <option value="name">Sort by: Name (A-Z)</option>
            <option value="-name">Sort by: Name (Z-A)</option>
          </select>
        </div>
      </div>

      {/* Patients Grid / Loading / Error State */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} className="p-6 border border-slate-100 bg-white shadow-sm rounded-xl space-y-4 animate-pulse">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-full bg-slate-200" />
                <div className="space-y-2 flex-1">
                  <div className="h-4 w-28 bg-slate-200 rounded" />
                  <div className="h-3 w-40 bg-slate-100 rounded" />
                </div>
              </div>
              <div className="h-1 bg-slate-100 rounded" />
              <div className="grid grid-cols-3 gap-2">
                <div className="h-8 bg-slate-100 rounded" />
                <div className="h-8 bg-slate-100 rounded" />
                <div className="h-8 bg-slate-100 rounded" />
              </div>
            </Card>
          ))}
        </div>
      ) : isError ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="p-3 rounded-full bg-rose-50 text-rose-500 mb-4">
            <AlertCircle className="h-6 w-6" />
          </div>
          <h3 className="text-lg font-semibold text-slate-800">Failed to load directory</h3>
          <p className="text-sm text-slate-500 mt-1 max-w-sm">
            {error?.message || 'Something went wrong while loading patients directory.'}
          </p>
          <Button onClick={() => refetch()} variant="outline" className="mt-4 border-slate-200">
            Try Again
          </Button>
        </div>
      ) : !listData || listData.patients.length === 0 ? (
        <div className="bg-white border border-slate-100 rounded-xl p-12 text-center shadow-sm">
          <div className="p-3 rounded-full bg-slate-50 text-slate-400 w-fit mx-auto mb-4">
            <UserIcon className="h-6 w-6" />
          </div>
          <h3 className="text-lg font-semibold text-slate-800">No patients found</h3>
          <p className="text-sm text-slate-500 mt-1 max-w-md mx-auto">
            {search ? "No patients in your directory match the search query." : "You have not treated any patients yet."}
          </p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {listData.patients.map((patient) => (
              <Card
                key={patient.patient_id}
                onClick={() => handleOpenDetail(patient.patient_id)}
                className="p-6 border border-slate-200 bg-white hover:border-teal-300 hover:shadow-md transition-all rounded-xl cursor-pointer shadow-sm relative group flex flex-col justify-between"
              >
                <div className="space-y-4">
                  {/* Card Header Profile */}
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-4">
                      {patient.profile_picture ? (
                        <img
                          src={patient.profile_picture}
                          alt={patient.name}
                          className="h-12 w-12 rounded-full object-cover border border-slate-100"
                        />
                      ) : (
                        <div className="h-12 w-12 rounded-full bg-teal-50 text-teal-700 flex items-center justify-center font-bold text-lg border border-teal-100">
                          {patient.name.split(' ').map((n) => n[0]).join('').substring(0, 2).toUpperCase()}
                        </div>
                      )}
                      <div>
                        <h3 className="font-semibold text-slate-900 leading-tight group-hover:text-teal-700 transition-colors">
                          {patient.name}
                        </h3>
                        {patient.latest_appointment?.slot_date && (
                          <p className="text-xs text-slate-400 mt-0.5">
                            Last visit: {new Date(patient.latest_appointment.slot_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Risk Badge */}
                    {patient.health_risk_level && (
                      <Badge variant="outline" className={`capitalize border ${getRiskBadgeColor(patient.health_risk_level)}`}>
                        {patient.health_risk_level} Risk
                      </Badge>
                    )}
                  </div>

                  {/* Summary Counts bar */}
                  <div className="grid grid-cols-3 gap-2 bg-slate-50 p-2.5 rounded-lg border border-slate-100 text-center text-xs">
                    <div>
                      <p className="text-slate-400 font-medium">Appointments</p>
                      <p className="font-semibold text-slate-800 mt-0.5">{patient.total_appointments}</p>
                    </div>
                    <div>
                      <p className="text-slate-400 font-medium">Consultations</p>
                      <p className="font-semibold text-slate-800 mt-0.5">{patient.total_consultations}</p>
                    </div>
                    <div>
                      <p className="text-slate-400 font-medium">Reports</p>
                      <p className="font-semibold text-slate-800 mt-0.5">{patient.total_reports}</p>
                    </div>
                  </div>
                </div>

                {/* Card Action footer link */}
                <div className="mt-4 flex items-center justify-end text-xs font-semibold text-teal-600 group-hover:text-teal-700">
                  <span>View Full Profile</span>
                  <ChevronRight className="h-3.5 w-3.5 ml-1 transition-transform group-hover:translate-x-0.5" />
                </div>
              </Card>
            ))}
          </div>

          {/* Simple Pagination */}
          {listData.total > limit && (
            <div className="flex items-center justify-between border-t border-slate-200 pt-6 mt-6">
              <p className="text-sm text-slate-600">
                Showing <span className="font-semibold">{skip + 1}</span> to{' '}
                <span className="font-semibold">{Math.min(skip + limit, listData.total)}</span> of{' '}
                <span className="font-semibold">{listData.total}</span> patients
              </p>
              <div className="flex gap-2">
                <Button
                  onClick={() => setSkip(Math.max(0, skip - limit))}
                  disabled={skip === 0}
                  variant="outline"
                  size="sm"
                  className="border-slate-200"
                >
                  Previous
                </Button>
                <Button
                  onClick={() => setSkip(skip + limit)}
                  disabled={skip + limit >= listData.total}
                  variant="outline"
                  size="sm"
                  className="border-slate-200"
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Patient details slide-over panel */}
      {selectedPatientId && (
        <div className="fixed inset-0 z-50 overflow-hidden" aria-labelledby="slide-over-title" role="dialog" aria-modal="true">
          <div className="absolute inset-0 overflow-hidden">
            {/* Background Overlay */}
            <div
              onClick={handleCloseDetail}
              className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity duration-300"
            />

            <div className="pointer-events-none fixed inset-y-0 right-0 flex max-w-full pl-10">
              <div className="pointer-events-auto w-screen max-w-2xl transform transition-transform duration-300 ease-in-out translate-x-0 bg-white shadow-2xl flex flex-col h-full border-l border-slate-100">
                
                {/* Header */}
                <div className="px-6 py-5 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <UserCheck className="h-5 w-5 text-teal-600" />
                    <h2 className="text-lg font-bold text-slate-800" id="slide-over-title">
                      Patient Medical Record
                    </h2>
                  </div>
                  <button
                    onClick={handleCloseDetail}
                    className="rounded-md text-slate-400 hover:text-slate-500 focus:outline-none hover:bg-slate-100 p-1"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>

                {/* Slide-over Body */}
                <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
                  {isDetailLoading ? (
                    <div className="space-y-6 animate-pulse">
                      <div className="flex items-center gap-4">
                        <div className="h-16 w-16 bg-slate-200 rounded-full" />
                        <div className="space-y-2 flex-1">
                          <div className="h-5 w-32 bg-slate-200 rounded" />
                          <div className="h-4 w-48 bg-slate-100 rounded" />
                        </div>
                      </div>
                      <div className="h-px bg-slate-100" />
                      <div className="h-8 bg-slate-100 rounded w-64" />
                      <div className="h-40 bg-slate-100 rounded" />
                    </div>
                  ) : isDetailError || !detailData ? (
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                      <div className="p-3 rounded-full bg-rose-50 text-rose-500 mb-4">
                        <AlertCircle className="h-6 w-6" />
                      </div>
                      <h3 className="text-lg font-semibold text-slate-800">Failed to load details</h3>
                      <p className="text-sm text-slate-500 mt-1 max-w-sm">
                        Unable to aggregate complete profile details for this patient.
                      </p>
                    </div>
                  ) : (
                    <>
                      {/* Profile Card */}
                      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 border border-slate-200 rounded-xl bg-slate-50">
                        <div className="flex items-center gap-4">
                          {detailData.profile.profile_picture ? (
                            <img
                              src={detailData.profile.profile_picture}
                              alt={detailData.profile.full_name}
                              className="h-16 w-16 rounded-full object-cover border border-slate-200 shadow-sm"
                            />
                          ) : (
                            <div className="h-16 w-16 rounded-full bg-teal-600 text-white flex items-center justify-center font-bold text-xl shadow-sm">
                              {detailData.profile.full_name.split(' ').map((n) => n[0]).join('').substring(0, 2).toUpperCase()}
                            </div>
                          )}
                          <div>
                            <h3 className="text-xl font-bold text-slate-900">{detailData.profile.full_name}</h3>
                            <p className="text-sm text-slate-500">{detailData.profile.email}</p>
                            <p className="text-xs text-slate-400 mt-0.5">Patient ID: {detailData.profile.id}</p>
                          </div>
                        </div>
                      </div>

                      {/* Detail navigation tabs */}
                      <div className="flex border-b border-slate-200">
                        <button
                          onClick={() => setActiveTab('insights')}
                          className={`flex-1 py-3 text-center text-sm font-semibold border-b-2 transition-all ${
                            activeTab === 'insights'
                              ? 'border-teal-600 text-teal-600'
                              : 'border-transparent text-slate-500 hover:text-slate-800'
                          }`}
                        >
                          Insights & Reminders
                        </button>
                        <button
                          onClick={() => setActiveTab('history')}
                          className={`flex-1 py-3 text-center text-sm font-semibold border-b-2 transition-all ${
                            activeTab === 'history'
                              ? 'border-teal-600 text-teal-600'
                              : 'border-transparent text-slate-500 hover:text-slate-800'
                          }`}
                        >
                          History
                        </button>
                        <button
                          onClick={() => setActiveTab('records')}
                          className={`flex-1 py-3 text-center text-sm font-semibold border-b-2 transition-all ${
                            activeTab === 'records'
                              ? 'border-teal-600 text-teal-600'
                              : 'border-transparent text-slate-500 hover:text-slate-800'
                          }`}
                        >
                          Reports & Prescriptions
                        </button>
                      </div>

                      {/* Tab content panels */}
                      <div className="pt-2">
                        {/* Tab 1: Insights & Reminders */}
                        {activeTab === 'insights' && (
                          <div className="space-y-6 text-xs text-slate-700">
                            {/* Patient Longitudinal Health Memory */}
                            {detailData.patient_memory ? (
                              <div className="space-y-6">
                                {/* Summary Card */}
                                <Card className="border border-teal-200 bg-gradient-to-r from-teal-50/50 to-cyan-50/50 p-4 shadow-sm space-y-3">
                                  <div className="flex justify-between items-center flex-wrap gap-2">
                                    <div className="flex items-center gap-1.5">
                                      <span className="text-[10px] font-bold text-teal-800 uppercase tracking-wider bg-teal-100 px-2 py-0.5 rounded">
                                        Patient Longitudinal Profile
                                      </span>
                                    </div>
                                    {detailData.patient_memory.report_summaries && detailData.patient_memory.report_summaries.length > 0 && (
                                      <Badge className="bg-teal-100 text-teal-800 border border-teal-200 hover:bg-teal-100 text-[9px] rounded font-semibold">
                                        Latest Report Confidence: {(detailData.patient_memory.report_summaries[detailData.patient_memory.report_summaries.length - 1].summary_confidence * 100).toFixed(0)}%
                                      </Badge>
                                    )}
                                  </div>
                                  
                                  <div className="space-y-2">
                                    <h4 className="font-bold text-slate-800 text-sm">Longitudinal Clinical Summary</h4>
                                    <p className="text-slate-700 leading-relaxed font-medium">
                                      {detailData.patient_memory.longitudinal_summary || detailData.patient_memory.ai_summary}
                                    </p>
                                  </div>

                                  {detailData.patient_memory.latest_report_summary && (
                                    <div className="border-t border-teal-100 pt-3 mt-1 space-y-1">
                                      <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wide">Latest Report Executive Summary</h4>
                                      <p className="text-slate-600 leading-relaxed font-medium">
                                        {detailData.patient_memory.latest_report_summary}
                                      </p>
                                    </div>
                                  )}

                                  {detailData.patient_memory.latest_risk && (
                                    <div className="border-t border-teal-100 pt-3 mt-1 flex justify-between items-center">
                                      <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Abnormal Findings/Risk</span>
                                      <Badge className="bg-rose-50 text-rose-700 border-rose-200 hover:bg-rose-50 font-bold py-0.5">
                                        {detailData.patient_memory.latest_risk}
                                      </Badge>
                                    </div>
                                  )}
                                </Card>

                                {/* Diagnostics, Trends & Timeline Grid */}
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                  {/* Lab Trends & History */}
                                  <div className="space-y-4">
                                    {/* Lab Trends */}
                                    <Card className="border border-slate-200 shadow-sm p-4 bg-white space-y-3">
                                      <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wide flex items-center gap-1.5">
                                        <Activity className="h-4 w-4 text-teal-600 animate-pulse" />
                                        Laboratory Parameters Trends
                                      </h4>
                                      <p className="text-slate-600 leading-relaxed font-medium">
                                        {detailData.patient_memory.laboratory_trends || "No lab trends identified."}
                                      </p>
                                    </Card>

                                    {/* Diagnosis History */}
                                    <Card className="border border-slate-200 shadow-sm p-4 bg-white space-y-3">
                                      <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wide flex items-center gap-1.5">
                                        <Stethoscope className="h-4 w-4 text-teal-600" />
                                        Diagnosis History
                                      </h4>
                                      {detailData.patient_memory.diagnosis_history && detailData.patient_memory.diagnosis_history.length > 0 ? (
                                        <div className="flex flex-wrap gap-2">
                                          {detailData.patient_memory.diagnosis_history.map((diag: any, idx: number) => (
                                            <Badge key={idx} className="bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-50 font-semibold text-[10px] rounded">
                                              {diag.diagnosis} ({new Date(diag.report_date).toLocaleDateString()})
                                            </Badge>
                                          ))}
                                        </div>
                                      ) : (
                                        <p className="text-slate-400 italic">No diagnoses listed.</p>
                                      )}
                                    </Card>

                                    {/* Medication History */}
                                    <Card className="border border-slate-200 shadow-sm p-4 bg-white space-y-3">
                                      <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wide flex items-center gap-1.5">
                                        <Pill className="h-4 w-4 text-teal-600" />
                                        Medications History Log
                                      </h4>
                                      {detailData.patient_memory.medication_history && detailData.patient_memory.medication_history.length > 0 ? (
                                        <div className="space-y-2">
                                          {detailData.patient_memory.medication_history.map((med: any, idx: number) => (
                                            <div key={idx} className="flex justify-between items-center border-b pb-1">
                                              <div>
                                                <strong className="text-slate-800">{med.medicine}</strong>
                                                <span className="text-[10px] text-slate-400 block">{med.dosage} - {med.frequency}</span>
                                              </div>
                                              <span className="text-[10px] text-slate-500 font-mono">Date: {med.report_date ? med.report_date.split('T')[0] : 'N/A'}</span>
                                            </div>
                                          ))}
                                        </div>
                                      ) : (
                                        <p className="text-slate-400 italic">No medications history listed.</p>
                                      )}
                                    </Card>
                                  </div>

                                  {/* Timeline Visualizer */}
                                  <Card className="border border-slate-200 shadow-sm p-4 bg-white space-y-3">
                                    <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wide flex items-center gap-1.5">
                                      <Clock className="h-4 w-4 text-teal-600" />
                                      Chronological Medical Timeline
                                    </h4>
                                    {detailData.patient_memory.timeline && detailData.patient_memory.timeline.length > 0 ? (
                                      <div className="relative border-l border-slate-100 pl-4 ml-2 space-y-4">
                                        {detailData.patient_memory.timeline.map((event: any, idx: number) => (
                                          <div key={idx} className="relative">
                                            <span className="absolute -left-[21px] top-1.5 h-1.5 w-1.5 rounded-full bg-teal-500 border border-white" />
                                            <div>
                                              <span className="text-[9px] font-mono text-slate-400 font-bold block">
                                                {event.timestamp ? event.timestamp.substring(0, 7) : 'N/A'}
                                              </span>
                                              <strong className="text-slate-850 text-[11px] block mt-0.5">{event.description}</strong>
                                            </div>
                                          </div>
                                        ))}
                                      </div>
                                    ) : (
                                      <p className="text-slate-400 italic">No medical timeline logged.</p>
                                    )}
                                  </Card>
                                </div>

                                {/* Actionable Clinical Recommendations */}
                                {detailData.patient_memory.latest_recommendations && detailData.patient_memory.latest_recommendations.length > 0 && (
                                  <Card className="border border-slate-200 shadow-sm p-4 bg-white space-y-3">
                                    <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wide flex items-center gap-1.5">
                                      <Clipboard className="h-4 w-4 text-teal-600" />
                                      Latest Actionable Recommendations
                                    </h4>
                                    <div className="space-y-3">
                                      {detailData.patient_memory.latest_recommendations.map((rec: any, idx: number) => (
                                        <div key={idx} className="p-3 border rounded bg-white shadow-2xs border-l-4 border-l-teal-500 space-y-1">
                                          <div className="flex justify-between items-center text-[10px] font-bold text-slate-900 border-b pb-1">
                                            <span>{rec.recommendation_type}</span>
                                            <span className={`px-1.5 py-0.5 rounded text-[8px] border font-bold ${
                                              rec.urgency === 'IMMEDIATE' ? 'bg-red-50 text-red-700 border-red-200' :
                                              rec.urgency === 'SOON' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                                              'bg-slate-50 text-slate-500'
                                            }`}>
                                              {rec.urgency}
                                            </span>
                                          </div>
                                          <p className="text-[11px] text-slate-600 leading-normal">{rec.description}</p>
                                        </div>
                                      ))}
                                    </div>
                                  </Card>
                                )}
                              </div>
                            ) : (
                              <p className="text-slate-400 italic">No health memory logged for this patient.</p>
                            )}

                            {/* AI Health Insights */}
                            <div className="space-y-3">
                              <h4 className="font-bold text-slate-800 text-sm tracking-wide uppercase flex items-center gap-2">
                                <Activity className="h-4 w-4 text-teal-600" />
                                AI Generated Health Insights
                              </h4>
                              {detailData.health_insights.length === 0 ? (
                                <p className="text-sm text-slate-400 bg-slate-50 p-4 rounded-lg border border-dashed border-slate-200">
                                  No AI health insights generated yet for this patient.
                                </p>
                              ) : (
                                <div className="space-y-3">
                                  {detailData.health_insights.map((insight) => (
                                    <div
                                      key={insight.id}
                                      className="p-4 border border-slate-200 rounded-lg space-y-2 hover:border-slate-300 transition-colors bg-white shadow-sm"
                                    >
                                      <div className="flex items-center justify-between">
                                        <h5 className="font-semibold text-slate-800">{insight.title}</h5>
                                        <Badge
                                          className={`capitalize font-semibold border ${
                                            insight.severity === 'high'
                                              ? 'bg-rose-50 text-rose-700 border-rose-200'
                                              : insight.severity === 'medium'
                                              ? 'bg-amber-50 text-amber-700 border-amber-200'
                                              : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                          }`}
                                          variant="outline"
                                        >
                                          {insight.severity} Severity
                                        </Badge>
                                      </div>
                                      <p className="text-xs text-slate-500 font-medium">
                                        Date: {new Date(insight.created_at).toLocaleDateString()}
                                      </p>
                                      <p className="text-sm text-slate-600 leading-relaxed">{insight.summary}</p>
                                      {insight.recommendations && insight.recommendations.length > 0 && (
                                        <div className="pt-2">
                                          <p className="text-xs font-semibold text-slate-700">Recommendations:</p>
                                          <ul className="list-disc pl-5 text-xs text-slate-600 mt-1 space-y-1">
                                            {insight.recommendations.map((rec, idx) => (
                                              <li key={idx}>{rec}</li>
                                            ))}
                                          </ul>
                                        </div>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>

                            {/* Active Reminders */}
                            <div className="space-y-3">
                              <h4 className="font-bold text-slate-800 text-sm tracking-wide uppercase flex items-center gap-2">
                                <Clock className="h-4 w-4 text-teal-600" />
                                Active Patient Reminders
                              </h4>
                              {detailData.current_reminders.length === 0 ? (
                                <p className="text-sm text-slate-400 bg-slate-50 p-4 rounded-lg border border-dashed border-slate-200">
                                  No active reminders set for this patient.
                                </p>
                              ) : (
                                <div className="space-y-2">
                                  {detailData.current_reminders.map((reminder) => (
                                    <div
                                      key={reminder.id}
                                      className="flex items-start justify-between p-3 border border-slate-200 bg-white rounded-lg shadow-sm text-sm"
                                    >
                                      <div>
                                        <p className="font-semibold text-slate-800">{reminder.title}</p>
                                        {reminder.description && (
                                          <p className="text-xs text-slate-500 mt-0.5">{reminder.description}</p>
                                        )}
                                        <div className="flex items-center gap-3 mt-1.5 text-xs text-slate-400">
                                          <span>Time: {reminder.time}</span>
                                          <span>•</span>
                                          <span className="capitalize">Freq: {reminder.frequency}</span>
                                        </div>
                                      </div>
                                      <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200 font-semibold uppercase text-[10px]">
                                        Active
                                      </Badge>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Tab 2: History (Appointments & Consultations) */}
                        {activeTab === 'history' && (
                          <div className="space-y-6">
                            {/* AI Patient Health Timeline */}
                            {detailData.patient_memory?.timeline && detailData.patient_memory.timeline.length > 0 && (
                              <div className="space-y-3 bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
                                <h4 className="font-bold text-slate-800 text-sm tracking-wide uppercase flex items-center gap-2">
                                  <Clock className="h-4 w-4 text-teal-600" />
                                  Longitudinal Medical Timeline
                                </h4>
                                <div className="relative border-l-2 border-teal-100 pl-4 ml-2 space-y-4 pt-2">
                                  {detailData.patient_memory.timeline.slice(0, 10).map((event: any, idx: number) => (
                                    <div key={idx} className="relative">
                                      <div className="absolute -left-[22px] top-1.5 h-2.5 w-2.5 rounded-full bg-teal-500 border border-white" />
                                      <div className="space-y-0.5 text-xs">
                                        <span className="text-[10px] font-bold text-slate-450">
                                          {event.timestamp ? new Date(event.timestamp).toLocaleDateString() : 'Historical'}
                                        </span>
                                        <p className="text-slate-700 font-semibold leading-relaxed">
                                          {event.description}
                                        </p>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Consultation Summary Log */}
                            <div className="space-y-3">
                              <h4 className="font-bold text-slate-800 text-sm tracking-wide uppercase flex items-center gap-2">
                                <Stethoscope className="h-4 w-4 text-teal-600" />
                                Consultations Record
                              </h4>
                              {detailData.consultation_history.length === 0 ? (
                                <p className="text-sm text-slate-400 bg-slate-50 p-4 rounded-lg border border-dashed border-slate-200">
                                  No consultation logs recorded yet.
                                </p>
                              ) : (
                                <div className="space-y-3">
                                  {detailData.consultation_history.map((consultation) => (
                                    <div
                                      key={consultation.id}
                                      className="p-4 border border-slate-200 bg-white rounded-lg shadow-sm space-y-2.5"
                                    >
                                      <div className="flex items-center justify-between border-b pb-2">
                                        <div>
                                          <p className="text-xs text-slate-400 font-medium">
                                            Consulted on: {new Date(consultation.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                                          </p>
                                        </div>
                                        {consultation.follow_up_required && (
                                          <Badge className="bg-blue-50 text-blue-700 border-blue-200 font-semibold">
                                            Follow-up Required
                                          </Badge>
                                        )}
                                      </div>
                                      <div>
                                        <p className="text-xs font-semibold text-slate-500">Diagnosis</p>
                                        <p className="text-sm font-semibold text-slate-800 mt-0.5">{consultation.diagnosis}</p>
                                      </div>
                                      <div>
                                        <p className="text-xs font-semibold text-slate-500">Notes & Recommendations</p>
                                        <p className="text-sm text-slate-600 mt-0.5 whitespace-pre-line leading-relaxed">
                                          {consultation.consultation_notes}
                                        </p>
                                      </div>
                                      {consultation.follow_up_date && (
                                        <p className="text-xs font-medium text-amber-600 bg-amber-50/50 px-2 py-1 rounded w-fit">
                                          Recommended Follow-up: {new Date(consultation.follow_up_date).toLocaleDateString()}
                                        </p>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>

                            {/* Appointments Timeline */}
                            <div className="space-y-3">
                              <h4 className="font-bold text-slate-800 text-sm tracking-wide uppercase flex items-center gap-2">
                                <Calendar className="h-4 w-4 text-teal-600" />
                                Appointments Timeline
                              </h4>
                              {detailData.appointment_history.length === 0 ? (
                                <p className="text-sm text-slate-400 bg-slate-50 p-4 rounded-lg border border-dashed border-slate-200">
                                  No appointment history recorded.
                                </p>
                              ) : (
                                <div className="relative border-l-2 border-slate-100 pl-4 ml-2 space-y-4">
                                  {detailData.appointment_history.map((appointment) => (
                                    <div key={appointment.id} className="relative group">
                                      {/* Timeline dot */}
                                      <div className="absolute -left-[23px] top-1.5 h-2.5 w-2.5 rounded-full bg-slate-300 group-hover:bg-teal-500 transition-colors border border-white" />
                                      <div>
                                        <div className="flex items-center gap-2.5">
                                          <p className="text-sm font-semibold text-slate-800">
                                            {new Date(appointment.slot_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })} at {appointment.slot_time}
                                          </p>
                                          <Badge className="capitalize font-semibold text-[10px] scale-95 border bg-white border-slate-200 text-slate-700">
                                            {appointment.status}
                                          </Badge>
                                        </div>
                                        <p className="text-xs text-slate-500 mt-0.5">Reason: {appointment.reason || 'General Checkup'}</p>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Tab 3: Records (Reports & Prescriptions) */}
                        {activeTab === 'records' && (
                          <div className="space-y-6">
                            {/* Health Reports */}
                            <div className="space-y-3">
                              <h4 className="font-bold text-slate-800 text-sm tracking-wide uppercase flex items-center gap-2">
                                <FileText className="h-4 w-4 text-teal-600" />
                                Patient Uploaded Reports
                              </h4>
                              {detailData.reports.length === 0 ? (
                                <p className="text-sm text-slate-400 bg-slate-50 p-4 rounded-lg border border-dashed border-slate-200">
                                  No medical reports uploaded by patient.
                                </p>
                              ) : (
                                <div className="space-y-2">
                                  {detailData.reports.map((report) => (
                                    <div
                                      key={report.id}
                                      className="flex items-center justify-between p-3.5 border border-slate-200 bg-white rounded-lg shadow-sm"
                                    >
                                      <div className="space-y-0.5">
                                        <p className="text-sm font-semibold text-slate-800 truncate max-w-sm">{report.filename}</p>
                                        <div className="flex items-center gap-3 text-xs text-slate-400">
                                          <span>Uploaded: {new Date(report.created_at).toLocaleDateString()}</span>
                                          <span>•</span>
                                          <span className="capitalize">{report.processing_status}</span>
                                        </div>
                                      </div>
                                      <div className="flex items-center gap-3">
                                        {report.risk_level && (
                                          <Badge className={`capitalize text-[10px] font-semibold border ${getRiskBadgeColor(report.risk_level)}`}>
                                            {report.risk_level} Risk
                                          </Badge>
                                        )}
                                        <button
                                          onClick={() => handleOpenReportDetails(report.id)}
                                          className="text-xs font-semibold text-teal-600 hover:text-teal-700 hover:underline mr-3"
                                        >
                                          Inspect
                                        </button>
                                        <a
                                          href={report.file_url}
                                          target="_blank"
                                          rel="noreferrer"
                                          className="text-xs font-semibold text-slate-400 hover:text-slate-600 hover:underline"
                                        >
                                          View File
                                        </a>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>

                            {/* Reports Sub-Inspector */}
                            {selectedReportId && (
                              <Card className="border-2 border-teal-500 bg-white p-4 space-y-4">
                                <div className="flex justify-between items-center border-b pb-2">
                                  <div>
                                    <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Structured Report Inspection</h4>
                                    <span className="text-[10px] text-slate-400 font-mono">ID: {selectedReportId}</span>
                                  </div>
                                  <Button variant="ghost" size="sm" onClick={handleCloseReportDetails} className="text-xs text-slate-400 hover:text-slate-700">
                                    Close Details
                                  </Button>
                                </div>

                                {loadingReportDetails ? (
                                  <div className="text-center py-6">
                                    <RefreshCw className="h-5 w-5 animate-spin text-teal-600 mx-auto mb-2" />
                                    <p className="text-[10px] text-slate-500">Loading clinical results...</p>
                                  </div>
                                ) : structuredReport ? (
                                  <div className="space-y-4 text-xs">
                                    {/* Warnings */}
                                    {structuredReport.extraction_warnings && structuredReport.extraction_warnings.length > 0 && (
                                      <div className="p-3 bg-amber-50 border border-amber-200 rounded text-amber-800 font-semibold leading-relaxed">
                                        Warnings: {structuredReport.extraction_warnings.join(' | ')}
                                      </div>
                                    )}

                                    {/* Lab Results Table */}
                                    {structuredReport.laboratory_results && structuredReport.laboratory_results.length > 0 && (
                                      <div className="space-y-2">
                                        <span className="font-bold text-slate-500 uppercase block text-[10px]">Extracted Laboratory Results</span>
                                        <div className="border rounded overflow-hidden">
                                          <table className="w-full text-left border-collapse">
                                            <thead>
                                              <tr className="bg-slate-50 border-b text-slate-500 font-bold text-[10px]">
                                                <th className="p-2">Test Name</th>
                                                <th className="p-2">Value</th>
                                                <th className="p-2">Unit</th>
                                                <th className="p-2">Ref Range</th>
                                                <th className="p-2 text-right">Status</th>
                                              </tr>
                                            </thead>
                                            <tbody className="divide-y divide-slate-100">
                                              {structuredReport.laboratory_results.map((lab: any, idx: number) => (
                                                <tr key={idx}>
                                                  <td className="p-2 font-semibold text-slate-900">{lab.test_name}</td>
                                                  <td className="p-2 font-mono font-bold">{lab.value}</td>
                                                  <td className="p-2 text-slate-500">{lab.unit}</td>
                                                  <td className="p-2 font-mono text-slate-500">{lab.reference_range}</td>
                                                  <td className="p-2 text-right">
                                                    <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold border ${
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
                                      </div>
                                    )}

                                    {/* Medications */}
                                    {structuredReport.medications && structuredReport.medications.length > 0 && (
                                      <div className="space-y-2">
                                        <span className="font-bold text-slate-500 uppercase block text-[10px]">Extracted Medications</span>
                                        <div className="border rounded overflow-hidden">
                                          <table className="w-full text-left border-collapse">
                                            <thead>
                                              <tr className="bg-slate-50 border-b text-slate-500 font-bold text-[10px]">
                                                <th className="p-2">Medicine</th>
                                                <th className="p-2">Dosage</th>
                                                <th className="p-2">Frequency</th>
                                                <th className="p-2">Duration</th>
                                                <th className="p-2 text-right">Route</th>
                                              </tr>
                                            </thead>
                                            <tbody className="divide-y divide-slate-100">
                                              {structuredReport.medications.map((med: any, idx: number) => (
                                                <tr key={idx}>
                                                  <td className="p-2 font-semibold text-slate-900">{med.medicine}</td>
                                                  <td className="p-2 font-bold">{med.dosage}</td>
                                                  <td className="p-2 text-slate-500">{med.frequency}</td>
                                                  <td className="p-2 text-slate-500">{med.duration}</td>
                                                  <td className="p-2 text-right text-slate-500">{med.route}</td>
                                                </tr>
                                              ))}
                                            </tbody>
                                          </table>
                                        </div>
                                      </div>
                                    )}

                                    {/* AI Doctor Summary & Insights */}
                                    {reportSummary && (
                                      <div className="space-y-4 p-4 border border-teal-100 bg-teal-50/10 rounded-lg shadow-xs">
                                        <div className="flex justify-between items-center border-b border-teal-100 pb-2">
                                          <span className="font-bold text-teal-800 uppercase text-[10px] flex items-center gap-1.5">
                                            <Shield className="h-3.5 w-3.5" />
                                            AI Clinical Interpretation
                                          </span>
                                          <Badge className="bg-teal-100 text-teal-800 hover:bg-teal-100 border border-teal-200 text-[9px] rounded font-semibold">
                                            Confidence: {(reportSummary.summary_confidence * 100).toFixed(0)}%
                                          </Badge>
                                        </div>
                                        <div className="space-y-2">
                                          <span className="font-bold text-slate-700 block text-[10px]">DOCTOR SUMMARY REPORT</span>
                                          <p className="text-[11px] leading-relaxed text-slate-600 whitespace-pre-line">
                                            {reportSummary.doctor_summary}
                                          </p>
                                        </div>

                                        {reportInsights && reportInsights.clinical_insights && reportInsights.clinical_insights.length > 0 && (
                                          <div className="space-y-2 border-t border-slate-100 pt-3">
                                            <span className="font-bold text-slate-700 block text-[10px] uppercase">Differential Trends & Insights</span>
                                            <div className="space-y-1.5">
                                              {reportInsights.clinical_insights.map((insight: string, idx: number) => (
                                                <div key={idx} className="flex gap-1.5 items-start">
                                                  <span className="h-1.5 w-1.5 bg-teal-500 rounded-full mt-1.5 shrink-0" />
                                                  <span className="text-[10px] text-slate-600 leading-relaxed">{insight}</span>
                                                </div>
                                              ))}
                                            </div>
                                          </div>
                                        )}
                                      </div>
                                    )}

                                    {/* Clinical Risk Summary */}
                                    {reportRiskDetails && (
                                      <div className="space-y-3 bg-slate-50 p-3 rounded-lg border">
                                        <div className="flex justify-between items-center pb-2 border-b">
                                          <span className="font-bold text-slate-800 uppercase text-[10px] flex items-center gap-1">
                                            <Activity className="h-3.5 w-3.5 text-teal-600 animate-pulse" />
                                            Clinical Risk Summary
                                          </span>
                                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase tracking-wider ${
                                            reportRiskDetails.overall_risk === 'CRITICAL' ? 'bg-red-600 text-white border-red-700 font-extrabold' :
                                            reportRiskDetails.overall_risk === 'HIGH' ? 'bg-rose-50 border-rose-200 text-rose-700' :
                                            reportRiskDetails.overall_risk === 'MEDIUM' ? 'bg-amber-50 border-amber-200 text-amber-700' :
                                            'bg-emerald-50 border-emerald-200 text-emerald-700'
                                          }`}>
                                            {reportRiskDetails.overall_risk} RISK ({reportRiskDetails.risk_score?.toFixed(0)}/100)
                                          </span>
                                        </div>

                                        {reportRiskDetails.clinical_flags && reportRiskDetails.clinical_flags.length > 0 && (
                                          <div className="flex flex-wrap gap-1">
                                            {reportRiskDetails.clinical_flags.map((flg: string, idx: number) => (
                                              <span key={idx} className="bg-rose-50 text-rose-700 border border-rose-200 px-1.5 py-0.5 rounded text-[8px] font-bold uppercase">
                                                {flg.replace('_', ' ')}
                                              </span>
                                            ))}
                                          </div>
                                        )}

                                        {reportRiskDetails.risk_findings && reportRiskDetails.risk_findings.length > 0 && (
                                          <div className="space-y-2 mt-2">
                                            {reportRiskDetails.risk_findings.map((f: any, idx: number) => (
                                              <div key={idx} className="p-2 border rounded bg-white shadow-2xs space-y-1">
                                                <div className="flex justify-between items-center text-[10px] font-semibold text-slate-900 border-b pb-0.5">
                                                  <span>{f.finding_name}</span>
                                                  <span className="text-slate-400 font-normal">{f.severity}</span>
                                                </div>
                                                <p className="text-[10px] text-slate-600 leading-normal">{f.explanation}</p>
                                              </div>
                                            ))}
                                          </div>
                                        )}
                                      </div>
                                    )}

                                    {/* Entity list */}
                                    {reportEntities && reportEntities.length > 0 && (
                                      <div className="space-y-2">
                                        <span className="font-bold text-slate-500 uppercase block text-[10px]">Extracted Medical Entities</span>
                                        <div className="flex flex-wrap gap-1.5">
                                          {reportEntities.map((ent: any, idx: number) => (
                                            <span key={idx} className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded text-[10px] font-medium border border-slate-200">
                                              {ent.text} ({ent.category})
                                            </span>
                                          ))}
                                        </div>
                                      </div>
                                    )}
                                  </div>
                                ) : (
                                  <div className="text-center py-4 text-slate-400">
                                    Structured clinical data extraction is not completed for this report.
                                  </div>
                                )}
                              </Card>
                            )}

                            {/* Prescriptions issued */}
                            <div className="space-y-3">
                              <h4 className="font-bold text-slate-800 text-sm tracking-wide uppercase flex items-center gap-2">
                                <Pill className="h-4 w-4 text-teal-600" />
                                Prescriptions Issued
                              </h4>
                              {detailData.prescriptions.length === 0 ? (
                                <p className="text-sm text-slate-400 bg-slate-50 p-4 rounded-lg border border-dashed border-slate-200">
                                  No prescriptions issued to this patient yet.
                                </p>
                              ) : (
                                <div className="space-y-3">
                                  {detailData.prescriptions.map((prescription) => (
                                    <div
                                      key={prescription.id}
                                      className="p-4 border border-slate-200 bg-white rounded-lg shadow-sm space-y-3"
                                    >
                                      <div className="flex justify-between items-center border-b pb-2">
                                        <p className="text-xs text-slate-400 font-semibold">
                                          Prescribed: {new Date(prescription.created_at).toLocaleDateString()}
                                        </p>
                                      </div>

                                      {/* Medications List */}
                                      <div className="space-y-2">
                                        {prescription.medications.map((med, idx) => (
                                          <div key={idx} className="text-sm flex justify-between items-start border-b border-slate-50 pb-1.5 last:border-0 last:pb-0">
                                            <div>
                                              <p className="font-semibold text-slate-800">{med.drug_name}</p>
                                              {med.instructions && (
                                                <p className="text-xs text-slate-500 italic mt-0.5">{med.instructions}</p>
                                              )}
                                            </div>
                                            <div className="text-right text-xs text-slate-500">
                                              <p className="font-medium">{med.dosage}</p>
                                              <p className="mt-0.5">{med.frequency} • {med.duration}</p>
                                            </div>
                                          </div>
                                        ))}
                                      </div>

                                      {prescription.notes && (
                                        <div className="pt-1.5 border-t border-slate-100">
                                          <p className="text-xs font-semibold text-slate-500">Notes:</p>
                                          <p className="text-xs text-slate-600 mt-0.5 leading-relaxed">{prescription.notes}</p>
                                        </div>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>

                {/* Footer Actions */}
                <div className="px-6 py-4 border-t border-slate-200 bg-slate-50 flex flex-col sm:flex-row gap-3">
                  <Link
                    href={`/dashboard/doctor/chat?patient=${selectedPatientId}`}
                    className="flex-1"
                    onClick={handleCloseDetail}
                  >
                    <Button className="w-full bg-teal-600 hover:bg-teal-700 text-white flex items-center justify-center gap-2">
                      <MessageSquare className="h-4 w-4" />
                      Open Chat Channel
                    </Button>
                  </Link>

                  <Button
                    onClick={handleCloseDetail}
                    variant="outline"
                    className="border-slate-200 hover:bg-slate-100 text-slate-700"
                  >
                    Dismiss
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
