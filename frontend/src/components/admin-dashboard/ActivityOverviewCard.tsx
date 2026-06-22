'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Calendar, ClipboardList, FileText, Bell, MessageSquare } from 'lucide-react'

interface ActivityOverviewCardProps {
  appointmentsCount: number
  consultationsCount: number
  reportsCount: number
  remindersCount: number
  chatsCount: number
}

export function ActivityOverviewCard({
  appointmentsCount,
  consultationsCount,
  reportsCount,
  remindersCount,
  chatsCount,
}: ActivityOverviewCardProps) {
  const activities = [
    {
      label: 'Total Appointments Booked',
      value: appointmentsCount,
      icon: Calendar,
      color: 'text-sky-600',
      bg: 'bg-sky-50',
    },
    {
      label: 'Consultation Records',
      value: consultationsCount,
      icon: ClipboardList,
      color: 'text-indigo-600',
      bg: 'bg-indigo-50',
    },
    {
      label: 'Medical Reports Uploaded',
      value: reportsCount,
      icon: FileText,
      color: 'text-teal-600',
      bg: 'bg-teal-50',
    },
    {
      label: 'Active Health Reminders',
      value: remindersCount,
      icon: Bell,
      color: 'text-amber-600',
      bg: 'bg-amber-50',
    },
    {
      label: 'Active AI/Doctor Chat Sessions',
      value: chatsCount,
      icon: MessageSquare,
      color: 'text-emerald-600',
      bg: 'bg-emerald-50',
    },
  ]

  return (
    <Card className="border-slate-200 shadow-sm hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-semibold text-slate-900">
          Platform Activity & Usage
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3.5">
          {activities.map((act) => {
            const Icon = act.icon
            return (
              <div key={act.label} className="flex items-center justify-between py-1.5 first:pt-0 last:pb-0">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-xl ${act.bg}`}>
                    <Icon className={`h-4 w-4 ${act.color}`} />
                  </div>
                  <span className="text-xs font-semibold text-slate-700">{act.label}</span>
                </div>
                <span className="text-sm font-bold text-slate-900">
                  {act.value === 0 ? '—' : act.value}
                </span>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
