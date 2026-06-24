'use client'

import { Card, CardContent } from '@/components/ui/card'
import { Calendar, CalendarCheck, Users, Clock, Pill } from 'lucide-react'
import { DoctorDashboardData } from '@/types'

interface DoctorStatCardsProps {
  data: DoctorDashboardData
}

export function DoctorStatCards({ data }: DoctorStatCardsProps) {
  const stats = [
    {
      label: "Today's Appointments",
      value: data.todays_appointments_count,
      subtitle: data.todays_appointments_count === 0 ? 'No appointments today' : `${data.todays_appointments_count} scheduled today`,
      icon: Calendar,
      iconBg: 'bg-teal-50',
      iconColor: 'text-teal-600',
    },
    {
      label: 'Upcoming Appointments',
      value: data.upcoming_appointments_count,
      subtitle: data.upcoming_appointments_count === 0 ? 'No upcoming slots' : `${data.upcoming_appointments_count} upcoming bookings`,
      icon: CalendarCheck,
      iconBg: 'bg-sky-50',
      iconColor: 'text-sky-600',
    },
    {
      label: 'Total Patients',
      value: data.total_patients_count,
      subtitle: data.total_patients_count === 0 ? 'No patients yet' : `${data.total_patients_count} unique patient${data.total_patients_count !== 1 ? 's' : ''}`,
      icon: Users,
      iconBg: 'bg-indigo-50',
      iconColor: 'text-indigo-600',
    },
    {
      label: 'Pending Approvals',
      value: data.pending_approvals_count,
      subtitle: data.pending_approvals_count === 0 ? 'All caught up' : `${data.pending_approvals_count} require approval`,
      icon: Clock,
      iconBg: 'bg-amber-50',
      iconColor: 'text-amber-600',
    },
    {
      label: 'Prescriptions Written',
      value: data.prescriptions_written_count ?? 0,
      subtitle: (data.prescriptions_written_count ?? 0) === 0 ? 'No prescriptions yet' : `${data.prescriptions_written_count} prescriptions issued`,
      icon: Pill,
      iconBg: 'bg-emerald-50',
      iconColor: 'text-emerald-600',
    },
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
      {stats.map((stat) => {
        const Icon = stat.icon
        return (
          <Card key={stat.label} className="border-slate-200 shadow-sm hover:shadow-md transition-shadow">
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div className="space-y-2">
                  <p className="text-sm font-medium text-slate-500">{stat.label}</p>
                  <p className="text-3xl font-bold text-slate-900">
                    {stat.value === 0 ? '—' : stat.value}
                  </p>
                  <p className="text-xs text-slate-400">{stat.subtitle}</p>
                </div>
                <div className={`p-2.5 rounded-xl ${stat.iconBg}`}>
                  <Icon className={`h-5 w-5 ${stat.iconColor}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
