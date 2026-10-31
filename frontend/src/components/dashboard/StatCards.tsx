'use client'

import { Card, CardContent } from '@/components/ui/card'
import { FileText, Bell, Calendar, ShieldCheck } from 'lucide-react'
import { PatientDashboardData } from '@/types'

interface StatCardsProps {
  data: PatientDashboardData
}

const stats = [
  {
    key: 'reports_count' as const,
    label: 'Total Reports',
    subtitle: (v: number) => v === 0 ? 'No reports uploaded yet' : `${v} report${v !== 1 ? 's' : ''} on file`,
    icon: FileText,
    iconBg: 'bg-teal-50',
    iconColor: 'text-teal-600',
  },
  {
    key: 'active_reminders_count' as const,
    label: 'Active Reminders',
    subtitle: (v: number) => v === 0 ? 'Set up your first reminder' : `${v} active reminder${v !== 1 ? 's' : ''}`,
    icon: Bell,
    iconBg: 'bg-amber-50',
    iconColor: 'text-amber-600',
  },
  {
    key: 'upcoming_appointments_count' as const,
    label: 'Upcoming Appointments',
    subtitle: (v: number) => v === 0 ? 'Nothing scheduled' : `${v} upcoming`,
    icon: Calendar,
    iconBg: 'bg-sky-50',
    iconColor: 'text-sky-600',
  },
]

export function StatCards({ data }: StatCardsProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-3 gap-4">
      {stats.map((stat) => {
        const value = data[stat.key] ?? 0
        return (
          <Card key={stat.key} className="border-slate-200 shadow-sm hover:shadow-md transition-shadow">
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div className="space-y-2">
                  <p className="text-sm font-medium text-slate-500">{stat.label}</p>
                  <p className="text-3xl font-bold text-slate-900">
                    {value}
                  </p>
                  <p className="text-xs text-slate-400">{stat.subtitle(value)}</p>
                </div>
                <div className={`p-2.5 rounded-xl ${stat.iconBg}`}>
                  <stat.icon className={`h-5 w-5 ${stat.iconColor}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
