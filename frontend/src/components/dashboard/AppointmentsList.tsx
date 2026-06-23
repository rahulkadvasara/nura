'use client'

import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Calendar, Plus, Clock, Stethoscope } from 'lucide-react'
import { useAppointments } from '@/hooks/use-appointments'

interface AppointmentsListProps {
  count?: number // keep count as optional prop for backward compatibility
}

export function AppointmentsList({ count }: AppointmentsListProps) {
  const { data: appointments = [], isLoading, isError } = useAppointments()

  // Filter for upcoming (pending or approved) appointments
  const upcomingAppointments = appointments.filter(
    (appt) => appt.status === 'pending' || appt.status === 'approved'
  )

  // Show up to 3 upcoming/pending items
  const displayList = upcomingAppointments.slice(0, 3)

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'bg-emerald-50 text-emerald-700 hover:bg-emerald-50 border-emerald-100'
      case 'pending':
        return 'bg-amber-50 text-amber-700 hover:bg-amber-50 border-amber-100'
      default:
        return ''
    }
  }

  return (
    <Card className="border-slate-200 shadow-sm h-full flex flex-col justify-between bg-white overflow-hidden">
      <CardHeader className="pb-3 border-b border-slate-50 p-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-bold text-slate-800 flex items-center gap-2">
            <Calendar className="h-5 w-5 text-teal-600" />
            Upcoming Appointments
          </CardTitle>
          {upcomingAppointments.length > 0 && (
            <Link
              href="/dashboard/appointments"
              className="text-xs font-semibold text-teal-600 hover:text-teal-700 transition-colors"
            >
              View all ({upcomingAppointments.length})
            </Link>
          )}
        </div>
      </CardHeader>
      <CardContent className="p-4 flex-1">
        {isLoading && (
          <div className="space-y-3 py-2">
            {Array.from({ length: 2 }).map((_, i) => (
              <div key={i} className="h-14 bg-slate-50 border border-slate-100 rounded-lg animate-pulse" />
            ))}
          </div>
        )}

        {!isLoading && (isError || upcomingAppointments.length === 0) && (
          <div className="flex flex-col items-center justify-center py-6 text-center">
            <div className="p-3.5 rounded-full bg-slate-50 border border-slate-100 mb-3 text-slate-400">
              <Calendar className="h-6 w-6" />
            </div>
            <p className="text-sm font-bold text-slate-700 mb-1">
              No appointments scheduled
            </p>
            <p className="text-xs text-slate-400 mb-4 max-w-[200px] leading-relaxed">
              Book a visit with a doctor to begin your consultation.
            </p>
            <Link href="/dashboard/doctors">
              <Button
                size="sm"
                className="bg-teal-600 hover:bg-teal-700 text-white text-xs px-4 rounded-lg flex items-center gap-1"
              >
                <Plus className="h-4 w-4" />
                Book Appointment
              </Button>
            </Link>
          </div>
        )}

        {!isLoading && upcomingAppointments.length > 0 && (
          <div className="space-y-3 py-1">
            {displayList.map((appt) => (
              <div 
                key={appt.id} 
                className="flex items-center justify-between p-3 border border-slate-100 hover:border-teal-500/20 bg-slate-50/50 hover:bg-teal-50/5 rounded-xl transition-all duration-200"
              >
                <div className="space-y-1 max-w-[70%]">
                  <div className="flex items-center gap-1.5">
                    <Stethoscope className="h-3.5 w-3.5 text-teal-600" />
                    <span className="font-bold text-xs text-slate-900 truncate">
                      {appt.doctor_name.toLowerCase().startsWith('dr.') ? appt.doctor_name : `Dr. ${appt.doctor_name}`}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-[10px] text-slate-400 font-medium">
                    <span className="truncate max-w-[100px]">{appt.specialization}</span>
                    <span>•</span>
                    <span className="flex items-center gap-0.5 shrink-0">
                      <Clock className="h-3 w-3" />
                      {appt.appointment_date} {appt.appointment_time}
                    </span>
                  </div>
                </div>
                <Badge className={`text-[10px] font-bold py-0.5 px-2 rounded-md ${getStatusColor(appt.status)}`}>
                  {appt.status === 'pending' ? 'Pending' : 'Approved'}
                </Badge>
              </div>
            ))}
            {upcomingAppointments.length > 3 && (
              <div className="text-center pt-2">
                <Link href="/dashboard/appointments">
                  <Button variant="ghost" size="sm" className="text-xs font-semibold text-teal-600 hover:text-teal-700 py-1.5 h-8">
                    View remaining {upcomingAppointments.length - 3} requests
                  </Button>
                </Link>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
