'use client'

import { useState } from 'react'
import { Calendar, Clock, User, AlertCircle, CheckCircle, XCircle, FileText, Stethoscope } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { useDoctorAppointments, useApproveAppointment, useRejectAppointment, useStartConsultation } from '@/hooks/use-appointments'
import { toast } from 'sonner'

type TabType = 'pending' | 'approved' | 'rejected'

function DoctorAppointmentsContent() {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<TabType>('pending')
  const { data: appointments = [], isLoading, isError, error, refetch } = useDoctorAppointments()
  const { mutateAsync: approveAppointment, isPending: isApproving } = useApproveAppointment()
  const { mutateAsync: rejectAppointment, isPending: isRejecting } = useRejectAppointment()
  const { mutateAsync: startConsultation, isPending: isStarting } = useStartConsultation()

  const [selectedApptId, setSelectedApptId] = useState<string | null>(null)
  const [showRejectModal, setShowRejectModal] = useState(false)
  const [rejectionReason, setRejectionReason] = useState('')

  const handleApprove = async (id: string) => {
    try {
      setSelectedApptId(id)
      await approveAppointment(id)
      toast.success('Appointment approved successfully.')
    } catch (err: any) {
      toast.error(err.message || 'Failed to approve appointment')
    } finally {
      setSelectedApptId(null)
    }
  }

  const handleStartConsultation = async (id: string) => {
    try {
      setSelectedApptId(id)
      await startConsultation(id)
      toast.success('Consultation started successfully.')
      router.push('/dashboard/doctor/consultations')
    } catch (err: any) {
      toast.error(err.message || 'Failed to start consultation')
    } finally {
      setSelectedApptId(null)
    }
  }

  const openRejectModal = (id: string) => {
    setSelectedApptId(id)
    setRejectionReason('')
    setShowRejectModal(true)
  }

  const handleRejectSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!rejectionReason.trim()) {
      toast.error('Rejection reason is required.')
      return
    }
    if (!selectedApptId) return

    try {
      await rejectAppointment({ appointmentId: selectedApptId, rejectionReason: rejectionReason.trim() })
      toast.success('Appointment rejected successfully.')
      setShowRejectModal(false)
    } catch (err: any) {
      toast.error(err.message || 'Failed to reject appointment')
    } finally {
      setSelectedApptId(null)
    }
  }

  // Segment appointments
  const pendingRequests = appointments.filter(a => a.status === 'pending')
  const approvedAppointments = appointments.filter(a => a.status === 'approved' || a.status === 'in_progress' || a.status === 'completed')
  const rejectedHistory = appointments.filter(a => a.status === 'rejected' || a.status === 'cancelled')

  const getActiveList = () => {
    switch (activeTab) {
      case 'pending':
        return pendingRequests
      case 'approved':
        return approvedAppointments
      case 'rejected':
        return rejectedHistory
      default:
        return []
    }
  }

  const activeList = getActiveList()

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'approved':
        return <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200">Approved</Badge>
      case 'in_progress':
        return <Badge className="bg-indigo-50 text-indigo-700 border-indigo-200">In Progress</Badge>
      case 'completed':
        return <Badge className="bg-blue-50 text-blue-700 border-blue-200">Completed</Badge>
      case 'pending':
        return <Badge className="bg-amber-50 text-amber-700 border-amber-200">Pending</Badge>
      case 'cancelled':
        return <Badge className="bg-slate-50 text-slate-600 border-slate-200">Cancelled by Patient</Badge>
      case 'rejected':
        return <Badge className="bg-rose-50 text-rose-700 border-rose-200">Rejected</Badge>
      default:
        return <Badge>{status}</Badge>
    }
  }

  return (
    <div className="space-y-6 max-w-4xl relative">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Manage Appointments</h1>
        <p className="text-slate-500 mt-1">Review, approve, or reject incoming patient appointment requests.</p>
      </div>

      {/* Tabs list */}
      <div className="flex border-b border-slate-200">
        <button
          onClick={() => setActiveTab('pending')}
          className={`pb-3 px-4 text-sm font-semibold border-b-2 transition-all ${
            activeTab === 'pending'
              ? 'border-teal-600 text-teal-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Pending Requests ({pendingRequests.length})
        </button>
        <button
          onClick={() => setActiveTab('approved')}
          className={`pb-3 px-4 text-sm font-semibold border-b-2 transition-all ${
            activeTab === 'approved'
              ? 'border-teal-600 text-teal-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Approved & Upcoming ({approvedAppointments.length})
        </button>
        <button
          onClick={() => setActiveTab('rejected')}
          className={`pb-3 px-4 text-sm font-semibold border-b-2 transition-all ${
            activeTab === 'rejected'
              ? 'border-teal-600 text-teal-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Rejected / Cancelled ({rejectedHistory.length})
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
          <h3 className="text-base font-semibold text-slate-800 mb-1">Failed to load appointments</h3>
          <p className="text-xs text-slate-500 mb-4 max-w-sm">
            {error?.message || 'Something went wrong while retrieving your appointment queue.'}
          </p>
          <Button onClick={() => refetch()} variant="outline" size="sm">
            Retry
          </Button>
        </div>
      )}

      {!isLoading && !isError && activeList.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 text-center bg-white border border-dashed rounded-xl p-6">
          <div className="p-3 rounded-full bg-slate-50 mb-3 text-slate-400">
            <Calendar className="h-6 w-6" />
          </div>
          <h3 className="text-base font-semibold text-slate-800 mb-1">No appointments found</h3>
          <p className="text-xs text-slate-500 max-w-sm">
            {activeTab === 'pending'
              ? 'You do not have any pending appointment requests right now.'
              : activeTab === 'approved'
              ? 'You do not have any upcoming approved consultations scheduled.'
              : 'No rejected or cancelled appointment history was found.'}
          </p>
        </div>
      )}

      {!isLoading && !isError && activeList.length > 0 && (
        <div className="space-y-4">
          {activeList.map((appt) => (
            <Card key={appt.id} className="border-slate-200 hover:shadow-sm transition-shadow bg-white overflow-hidden">
              <CardContent className="p-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4 text-teal-600 shrink-0" />
                    <h3 className="font-bold text-slate-900">{appt.patient_name}</h3>
                    {getStatusBadge(appt.status)}
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
                      <span className="font-semibold text-slate-850">Reason:</span> {appt.reason}
                    </p>
                  )}

                  {appt.rejection_reason && (
                    <p className="text-xs text-rose-600 bg-rose-50/30 border border-rose-100/50 rounded px-2.5 py-1.5 leading-relaxed max-w-2xl">
                      <span className="font-semibold text-rose-700">Rejection Reason:</span> {appt.rejection_reason}
                    </p>
                  )}
                </div>

                {appt.status === 'pending' && (
                  <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                    <Button
                      size="sm"
                      onClick={() => handleApprove(appt.id)}
                      disabled={isApproving && selectedApptId === appt.id}
                      className="bg-teal-600 hover:bg-teal-700 text-white text-xs h-9 px-3 rounded-lg flex items-center gap-1"
                    >
                      <CheckCircle className="h-3.5 w-3.5" />
                      {isApproving && selectedApptId === appt.id ? 'Approving...' : 'Approve'}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => openRejectModal(appt.id)}
                      className="border-slate-200 text-rose-600 hover:bg-rose-50 hover:text-rose-700 hover:border-rose-300 text-xs h-9 px-3 rounded-lg flex items-center gap-1"
                    >
                      <XCircle className="h-3.5 w-3.5" />
                      Reject
                    </Button>
                  </div>
                )}

                {appt.status === 'approved' && (
                  <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                    <Button
                      size="sm"
                      onClick={() => handleStartConsultation(appt.id)}
                      disabled={isStarting && selectedApptId === appt.id}
                      className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs h-9 px-3 rounded-lg flex items-center gap-1"
                    >
                      <Stethoscope className="h-3.5 w-3.5" />
                      {isStarting && selectedApptId === appt.id ? 'Starting...' : 'Start Consultation'}
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Glassmorphic Rejection Reason Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm transition-opacity duration-300">
          <Card className="w-full max-w-md bg-white/95 border border-slate-200/50 shadow-2xl rounded-2xl overflow-hidden p-6 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-start justify-between border-b pb-3 mb-4">
              <div className="flex items-center gap-2 text-rose-600">
                <XCircle className="h-5 w-5" />
                <h3 className="text-lg font-bold text-slate-900">Reject Appointment</h3>
              </div>
              <button
                onClick={() => setShowRejectModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <XCircle className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={handleRejectSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-700">Reason for Rejection</label>
                <textarea
                  required
                  placeholder="Please state why this appointment is being rejected (e.g. Schedule conflict, out of office...)"
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  className="w-full min-h-[100px] text-sm p-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 bg-slate-50/50 resize-none"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2 border-t">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowRejectModal(false)}
                  className="border-slate-200 text-slate-600 rounded-lg text-xs"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isRejecting}
                  className="bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs flex items-center gap-1"
                >
                  {isRejecting ? 'Rejecting...' : 'Confirm Rejection'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  )
}

export default function DoctorAppointmentsPage() {
  return (
    <ProtectedRoute allowedRoles={['doctor']}>
      <DoctorAppointmentsContent />
    </ProtectedRoute>
  )
}
