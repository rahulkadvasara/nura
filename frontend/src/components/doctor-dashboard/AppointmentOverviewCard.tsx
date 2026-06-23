'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Calendar, ArrowRight, Clock, User, CheckCircle, XCircle, Play, FileText, ArrowUpRight } from 'lucide-react'
import { useDoctorAppointments, useApproveAppointment, useRejectAppointment, useStartConsultation } from '@/hooks/use-appointments'
import { toast } from 'sonner'

interface AppointmentOverviewCardProps {
  todaysCount: number
  upcomingCount: number
}

type TabType = 'pending' | 'today' | 'completed'

export function AppointmentOverviewCard({ todaysCount, upcomingCount }: AppointmentOverviewCardProps) {
  const router = useRouter()
  const [activeSubTab, setActiveSubTab] = useState<TabType>('pending')
  const { data: appointments = [], isLoading, isError } = useDoctorAppointments()
  const { mutateAsync: approveAppointment } = useApproveAppointment()
  const { mutateAsync: rejectAppointment } = useRejectAppointment()
  const { mutateAsync: startConsultation } = useStartConsultation()
  const [selectedActionId, setSelectedActionId] = useState<string | null>(null)

  // Get local YYYY-MM-DD
  const today = new Date()
  const year = today.getFullYear()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')
  const todayStr = `${year}-${month}-${day}`

  // Categorize
  const pendingList = appointments.filter(a => a.status === 'pending')
  // Today's Consultations includes approved, in_progress, and completed today
  const todayList = appointments.filter(a => 
    (a.status === 'approved' || a.status === 'in_progress' || a.status === 'completed') && 
    a.appointment_date === todayStr
  )
  const completedList = appointments.filter(a => a.status === 'completed')

  const handleApprove = async (id: string) => {
    try {
      setSelectedActionId(id)
      await approveAppointment(id)
      toast.success('Appointment approved successfully.')
    } catch (err: any) {
      toast.error(err.message || 'Failed to approve appointment')
    } finally {
      setSelectedActionId(null)
    }
  }

  const handleReject = async (id: string) => {
    const reason = window.prompt('Please enter a rejection reason:')
    if (reason === null) return // Cancelled
    if (!reason.trim()) {
      toast.error('Rejection reason is required.')
      return
    }

    try {
      setSelectedActionId(id)
      await rejectAppointment({ appointmentId: id, rejectionReason: reason.trim() })
      toast.success('Appointment rejected successfully.')
    } catch (err: any) {
      toast.error(err.message || 'Failed to reject appointment')
    } finally {
      setSelectedActionId(null)
    }
  }

  const handleStart = async (id: string) => {
    try {
      setSelectedActionId(id)
      await startConsultation(id)
      toast.success('Consultation started successfully.')
      router.push('/dashboard/doctor/consultations')
    } catch (err: any) {
      toast.error(err.message || 'Failed to start consultation')
    } finally {
      setSelectedActionId(null)
    }
  }

  const getActiveList = () => {
    switch (activeSubTab) {
      case 'pending':
        return pendingList.slice(0, 2)
      case 'today':
        return todayList.slice(0, 2)
      case 'completed':
        return completedList.slice(0, 2)
      default:
        return []
    }
  }

  const activeList = getActiveList()
  const totalCount = activeSubTab === 'pending' ? pendingList.length : activeSubTab === 'today' ? todayList.length : completedList.length

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'approved':
        return <Badge className="bg-emerald-50 text-emerald-700 hover:bg-emerald-50 border-emerald-100 text-[10px]">Approved</Badge>
      case 'in_progress':
        return <Badge className="bg-indigo-50 text-indigo-700 hover:bg-indigo-50 border-indigo-100 text-[10px]">In Progress</Badge>
      case 'completed':
        return <Badge className="bg-blue-50 text-blue-700 hover:bg-blue-50 border-blue-100 text-[10px]">Completed</Badge>
      default:
        return <Badge className="text-[10px]">{status}</Badge>
    }
  }

  return (
    <Card className="border-slate-200 shadow-sm h-full flex flex-col justify-between bg-white overflow-hidden">
      <CardHeader className="pb-2 border-b border-slate-50 p-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-bold text-slate-800 flex items-center gap-2">
            <Calendar className="h-5 w-5 text-teal-600" />
            Appointments Overview
          </CardTitle>
          <Link
            href="/dashboard/doctor/appointments"
            className="text-xs font-semibold text-teal-600 hover:text-teal-700 transition-colors flex items-center gap-0.5"
          >
            Manage Queue
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        {/* Small Pill Tabs */}
        <div className="flex gap-1.5 mt-3 bg-slate-50 p-1 rounded-lg border border-slate-100">
          <button
            onClick={() => setActiveSubTab('pending')}
            className={`flex-1 text-center py-1 text-[11px] font-bold rounded-md transition-all ${
              activeSubTab === 'pending'
                ? 'bg-white text-teal-700 shadow-sm'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Pending ({pendingList.length})
          </button>
          <button
            onClick={() => setActiveSubTab('today')}
            className={`flex-1 text-center py-1 text-[11px] font-bold rounded-md transition-all ${
              activeSubTab === 'today'
                ? 'bg-white text-teal-700 shadow-sm'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Today&apos;s Consults ({todayList.length})
          </button>
          <button
            onClick={() => setActiveSubTab('completed')}
            className={`flex-1 text-center py-1 text-[11px] font-bold rounded-md transition-all ${
              activeSubTab === 'completed'
                ? 'bg-white text-teal-700 shadow-sm'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Completed ({completedList.length})
          </button>
        </div>
      </CardHeader>

      <CardContent className="p-4 flex-1 flex flex-col justify-between min-h-[180px]">
        {isLoading && (
          <div className="space-y-3 py-2 flex-1">
            {Array.from({ length: 2 }).map((_, i) => (
              <div key={i} className="h-14 bg-slate-50 border border-slate-100 rounded-xl animate-pulse" />
            ))}
          </div>
        )}

        {!isLoading && (isError || activeList.length === 0) && (
          <div className="flex flex-col items-center justify-center py-6 text-center flex-1">
            <div className="p-3 rounded-full bg-slate-50 border border-slate-100 mb-2.5 text-slate-400">
              <Calendar className="h-5 w-5" />
            </div>
            <p className="text-xs font-bold text-slate-700 mb-0.5">
              No records found
            </p>
            <p className="text-[10px] text-slate-400 max-w-[180px] leading-relaxed">
              {activeSubTab === 'pending'
                ? 'You do not have any pending patient requests.'
                : activeSubTab === 'today'
                ? 'No consultations scheduled for today.'
                : 'No completed consultation files yet.'}
            </p>
          </div>
        )}

        {!isLoading && activeList.length > 0 && (
          <div className="space-y-3 py-1 flex-1 flex flex-col justify-start">
            {activeList.map((appt) => (
              <div
                key={appt.id}
                className="flex items-center justify-between p-3 border border-slate-100 bg-slate-50/50 rounded-xl hover:border-teal-500/20 transition-all duration-200"
              >
                <div className="space-y-1 max-w-[60%]">
                  <div className="flex items-center gap-1.5">
                    <User className="h-3.5 w-3.5 text-teal-600 shrink-0" />
                    <span className="font-bold text-xs text-slate-900 truncate">
                      {appt.patient_name}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 text-[10px] text-slate-400 font-medium">
                    <Clock className="h-3 w-3 shrink-0" />
                    <span className="truncate">{appt.appointment_date} {appt.appointment_time}</span>
                  </div>
                </div>

                {activeSubTab === 'pending' && (
                  <div className="flex gap-1.5 shrink-0">
                    <Button
                      size="icon"
                      onClick={() => handleApprove(appt.id)}
                      disabled={selectedActionId === appt.id}
                      className="bg-teal-600 hover:bg-teal-700 text-white rounded-lg h-7 w-7 flex items-center justify-center"
                      title="Approve"
                    >
                      <CheckCircle className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => handleReject(appt.id)}
                      disabled={selectedActionId === appt.id}
                      className="border-slate-200 text-rose-600 hover:bg-rose-50 rounded-lg h-7 w-7 flex items-center justify-center"
                      title="Reject"
                    >
                      <XCircle className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                )}

                {activeSubTab === 'today' && (
                  <div className="flex items-center gap-1.5 shrink-0">
                    {appt.status === 'approved' && (
                      <Button
                        size="sm"
                        onClick={() => handleStart(appt.id)}
                        disabled={selectedActionId === appt.id}
                        className="bg-indigo-600 hover:bg-indigo-700 text-white h-7 px-2.5 rounded-lg text-[10px] font-bold flex items-center gap-1 shadow-sm"
                      >
                        <Play className="h-2.5 w-2.5 fill-current" />
                        Start
                      </Button>
                    )}
                    {appt.status === 'in_progress' && (
                      <Link href="/dashboard/doctor/consultations">
                        <Button
                          size="sm"
                          className="bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-150 h-7 px-2.5 rounded-lg text-[10px] font-bold flex items-center gap-1"
                        >
                          <ArrowUpRight className="h-2.5 w-2.5" />
                          Resume
                        </Button>
                      </Link>
                    )}
                    {appt.status === 'completed' && getStatusBadge(appt.status)}
                  </div>
                )}

                {activeSubTab === 'completed' && (
                  <div className="shrink-0">
                    {getStatusBadge(appt.status)}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {totalCount > 2 && (
          <div className="text-center pt-2 border-t border-slate-50 mt-2">
            <Link href={activeSubTab === 'completed' ? "/dashboard/doctor/consultations" : "/dashboard/doctor/appointments"}>
              <Button variant="ghost" size="sm" className="text-[11px] font-semibold text-teal-600 hover:text-teal-700 py-1 h-7">
                View remaining {totalCount - 2} records
              </Button>
            </Link>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
