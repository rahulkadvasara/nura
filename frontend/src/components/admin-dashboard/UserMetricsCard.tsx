'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Users, User, Stethoscope } from 'lucide-react'

interface UserMetricsCardProps {
  totalUsers: number
  totalPatients: number
  totalDoctors: number
}

export function UserMetricsCard({ totalUsers, totalPatients, totalDoctors }: UserMetricsCardProps) {
  const metrics = [
    {
      label: 'Registered Users',
      value: totalUsers,
      icon: Users,
      bgClass: 'bg-slate-50',
      iconClass: 'text-slate-600',
    },
    {
      label: 'Patients',
      value: totalPatients,
      icon: User,
      bgClass: 'bg-teal-50',
      iconClass: 'text-teal-600',
    },
    {
      label: 'Doctors',
      value: totalDoctors,
      icon: Stethoscope,
      bgClass: 'bg-indigo-50',
      iconClass: 'text-indigo-600',
    },
  ]

  return (
    <Card className="border-slate-200 shadow-sm hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-semibold text-slate-900">
          User Directory Overview
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-4">
          {metrics.map((m) => {
            const Icon = m.icon
            return (
              <div key={m.label} className="space-y-3 p-4 rounded-xl border border-slate-100 bg-slate-50/30">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-slate-500">{m.label}</span>
                  <div className={`p-1.5 rounded-lg ${m.bgClass}`}>
                    <Icon className={`h-4 w-4 ${m.iconClass}`} />
                  </div>
                </div>
                <div>
                  <p className="text-2xl font-bold text-slate-900">
                    {m.value === 0 ? '—' : m.value}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
