'use client'

import { useState } from 'react'
import { Calendar, Clock, User, AlertCircle, CheckCircle, FileText, Activity } from 'lucide-react'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { useDoctorAppointments, useDoctorConsultations, useCompleteConsultation } from '@/hooks/use-appointments'
import { toast } from 'sonner'

type TabType = 'in_progress' | 'completed'

function DoctorConsultationsContent() {
  const [activeTab, setActiveTab] = useState<TabType>('in_progress')
  
  // Fetch in-progress from appointments list
  const { data: appointments = [], isLoading: loadingAppts, isError: errorAppts, refetch: refetchAppts } = useDoctorAppointments()
  const inProgressList = appointments.filter(a => a.status === 'in_progress')

  // Fetch completed from consultations list
  const { data: consultations = [], isLoading: loadingConsults, isError: errorConsults, refetch: refetchConsults } = useDoctorConsultations()

  const { mutateAsync: completeConsultation, isPending: isCompleting } = useCompleteConsultation()

  // Form State
  const [selectedApptId, setSelectedApptId] = useState<string | null>(null)
  const [selectedPatientName, setSelectedPatientName] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [diagnosis, setDiagnosis] = useState('')
  const [notes, setNotes] = useState('')
  const [followUpRequired, setFollowUpRequired] = useState(false)
  const [followUpDate, setFollowUpDate] = useState('')

  const handleOpenCompleteModal = (appointmentId: string, patientName: string) => {
    setSelectedApptId(appointmentId)
    setSelectedPatientName(patientName)
    setDiagnosis('')
    setNotes('')
    setFollowUpRequired(false)
    setFollowUpDate('')
    setShowModal(true)
  }

  const handleCompleteSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!diagnosis.trim() || !notes.trim()) {
      toast.error('Diagnosis and Notes are required.')
      return
    }
    if (followUpRequired && !followUpDate) {
      toast.error('Please specify a follow-up date.')
      return
    }
    if (!selectedApptId) return

    try {
      const payload = {
        diagnosis: diagnosis.trim(),
        notes: notes.trim(),
        follow_up_required: followUpRequired,
        follow_up_date: followUpRequired ? new Date(followUpDate).toISOString() : null,
      }
      await completeConsultation({ appointmentId: selectedApptId, payload })
      toast.success('Consultation completed and saved.')
      setShowModal(false)
      refetchAppts()
      refetchConsults()
    } catch (err: any) {
      toast.error(err.message || 'Failed to complete consultation')
    }
  }

  const isLoading = activeTab === 'in_progress' ? loadingAppts : loadingConsults
  const isError = activeTab === 'in_progress' ? errorAppts : errorConsults
  const refetch = activeTab === 'in_progress' ? refetchAppts : refetchConsults

  return (
    <div className="space-y-6 max-w-4xl relative">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Practice Consultations</h1>
        <p className="text-slate-500 mt-1">Start, resume, and review your patient clinical consultation files.</p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200">
        <button
          onClick={() => setActiveTab('in_progress')}
          className={`pb-3 px-4 text-sm font-semibold border-b-2 transition-all ${
            activeTab === 'in_progress'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Active / In Progress ({inProgressList.length})
        </button>
        <button
          onClick={() => setActiveTab('completed')}
          className={`pb-3 px-4 text-sm font-semibold border-b-2 transition-all ${
            activeTab === 'completed'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Completed Records ({consultations.length})
        </button>
      </div>

      {isLoading && (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-28 bg-white border border-slate-200 rounded-xl animate-pulse" />
          ))}
        </div>
      )}

      {isError && (
        <div className="flex flex-col items-center justify-center py-12 text-center bg-white border rounded-xl">
          <div className="p-3 rounded-full bg-rose-50 mb-3">
            <AlertCircle className="h-6 w-6 text-rose-500" />
          </div>
          <h3 className="text-base font-semibold text-slate-800 mb-1">Failed to load consultations</h3>
          <p className="text-xs text-slate-500 mb-4 max-w-sm">
            Something went wrong while fetching consultation lists.
          </p>
          <Button onClick={() => refetch()} variant="outline" size="sm">
            Retry
          </Button>
        </div>
      )}

      {!isLoading && !isError && activeTab === 'in_progress' && inProgressList.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 text-center bg-white border border-dashed rounded-xl p-6">
          <div className="p-3 rounded-full bg-slate-50 mb-3 text-slate-400">
            <Activity className="h-6 w-6" />
          </div>
          <h3 className="text-base font-semibold text-slate-800 mb-1">No consultations in progress</h3>
          <p className="text-xs text-slate-500 max-w-sm">
            Go to the Appointments page and click &quot;Start Consultation&quot; on any approved slot to begin.
          </p>
        </div>
      )}

      {!isLoading && !isError && activeTab === 'completed' && consultations.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 text-center bg-white border border-dashed rounded-xl p-6">
          <div className="p-3 rounded-full bg-slate-50 mb-3 text-slate-400">
            <FileText className="h-6 w-6" />
          </div>
          <h3 className="text-base font-semibold text-slate-800 mb-1">No completed records found</h3>
          <p className="text-xs text-slate-500 max-w-sm">
            Once you complete active consultations, their records will appear here.
          </p>
        </div>
      )}

      {/* In Progress List */}
      {!isLoading && !isError && activeTab === 'in_progress' && inProgressList.length > 0 && (
        <div className="space-y-4">
          {inProgressList.map((appt) => (
            <Card key={appt.id} className="border-slate-200 hover:shadow-sm transition-shadow bg-white overflow-hidden">
              <CardContent className="p-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4 text-indigo-600 shrink-0" />
                    <h3 className="font-bold text-slate-900">{appt.patient_name}</h3>
                    <Badge className="bg-indigo-50 text-indigo-700 border-indigo-100">In Progress</Badge>
                  </div>
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-slate-500 font-medium">
                    <div className="flex items-center gap-1">
                      <Calendar className="h-3.5 w-3.5 text-slate-400" />
                      <span>{appt.appointment_date}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="h-3.5 w-3.5 text-slate-400" />
                      <span>{appt.appointment_time}</span>
                    </div>
                  </div>
                  {appt.reason && (
                    <p className="text-xs text-slate-600 bg-slate-50 border border-slate-100 rounded px-2.5 py-1.5 leading-relaxed max-w-2xl">
                      <span className="font-semibold text-slate-850">Chief Complaint:</span> {appt.reason}
                    </p>
                  )}
                </div>
                <Button
                  size="sm"
                  onClick={() => handleOpenCompleteModal(appt.id, appt.patient_name)}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs h-9 px-3 rounded-lg flex items-center gap-1 shrink-0 self-end sm:self-center shadow-sm"
                >
                  <CheckCircle className="h-3.5 w-3.5" />
                  Complete Consultation
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Completed List */}
      {!isLoading && !isError && activeTab === 'completed' && consultations.length > 0 && (
        <div className="space-y-4">
          {consultations.map((consult) => (
            <Card key={consult.id} className="border-slate-200 hover:shadow-sm transition-shadow bg-white overflow-hidden">
              <CardContent className="p-5 space-y-3">
                <div className="flex justify-between items-start">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <User className="h-4 w-4 text-emerald-600 shrink-0" />
                      <h3 className="font-bold text-slate-900">{consult.patient_name}</h3>
                      <Badge className="bg-emerald-50 text-emerald-700 border-emerald-100">Completed</Badge>
                    </div>
                    <div className="text-[10px] text-slate-400 font-semibold flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      <span>Completed on {new Date(consult.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 bg-slate-50/50 border border-slate-100 rounded-xl space-y-1">
                    <span className="font-bold text-slate-800 text-[11px] block">Diagnosis</span>
                    <p className="text-slate-600 leading-relaxed">{consult.diagnosis}</p>
                  </div>
                  <div className="p-3 bg-slate-50/50 border border-slate-100 rounded-xl space-y-1">
                    <span className="font-bold text-slate-800 text-[11px] block">Clinical Notes</span>
                    <p className="text-slate-600 leading-relaxed">{consult.consultation_notes}</p>
                  </div>
                </div>

                {consult.follow_up_required && consult.follow_up_date && (
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-teal-600 bg-teal-50/40 border border-teal-100 rounded-lg px-2.5 py-1.5 w-fit">
                    <Calendar className="h-3.5 w-3.5 text-teal-500" />
                    <span>Follow-up Scheduled: {new Date(consult.follow_up_date).toLocaleDateString()}</span>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Complete Consultation Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm transition-opacity duration-300">
          <Card className="w-full max-w-lg bg-white/95 border border-slate-200/50 shadow-2xl rounded-2xl overflow-hidden p-6 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-start justify-between border-b pb-3 mb-4">
              <div className="flex items-center gap-2 text-indigo-600">
                <CheckCircle className="h-5 w-5" />
                <h3 className="text-lg font-bold text-slate-900">Complete Consultation</h3>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <XCircle className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={handleCompleteSubmit} className="space-y-4">
              <div>
                <span className="text-xs font-semibold text-slate-500 block">Patient File</span>
                <span className="text-sm font-bold text-slate-800">{selectedPatientName}</span>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-bold text-slate-700">Diagnosis *</label>
                <textarea
                  required
                  placeholder="Enter medical diagnosis..."
                  value={diagnosis}
                  onChange={(e) => setDiagnosis(e.target.value)}
                  className="w-full min-h-[70px] text-sm p-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-slate-50/50 resize-none"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-bold text-slate-700">Clinical Notes *</label>
                <textarea
                  required
                  placeholder="Enter treatment plans, consultation notes, symptoms..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full min-h-[100px] text-sm p-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-slate-50/50 resize-none"
                />
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="followUp"
                    checked={followUpRequired}
                    onChange={(e) => setFollowUpRequired(e.target.checked)}
                    className="h-4 w-4 rounded border-slate-350 text-indigo-600 focus:ring-indigo-500"
                  />
                  <label htmlFor="followUp" className="text-xs font-bold text-slate-700 cursor-pointer select-none">
                    Schedule a follow-up consultation?
                  </label>
                </div>

                {followUpRequired && (
                  <div className="space-y-1 animate-in slide-in-from-top-2 duration-150">
                    <label className="text-xs font-bold text-slate-700 block">Follow-up Date *</label>
                    <input
                      required={followUpRequired}
                      type="date"
                      value={followUpDate}
                      onChange={(e) => setFollowUpDate(e.target.value)}
                      min={new Date().toISOString().split('T')[0]}
                      className="text-sm p-2.5 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-slate-50/50 w-full"
                    />
                  </div>
                )}
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowModal(false)}
                  className="border-slate-200 text-slate-600 rounded-lg text-xs"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isCompleting}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs flex items-center gap-1 shadow-sm"
                >
                  {isCompleting ? 'Completing...' : 'Save & Complete'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  )
}

function XCircle({ className }: { className?: string }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
      <path strokeLinecap="round" strokeLinejoin="round" d="m9.75 9.75 4.5 4.5m0-4.5-4.5 4.5M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
    </svg>
  )
}

export default function DoctorConsultationsPage() {
  return (
    <ProtectedRoute allowedRoles={['doctor']}>
      <DoctorConsultationsContent />
    </ProtectedRoute>
  )
}
