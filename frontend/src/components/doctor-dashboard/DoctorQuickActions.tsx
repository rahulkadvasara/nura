'use client'

import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Calendar, Clock, Users } from 'lucide-react'

const actions = [
  {
    label: 'View Schedule',
    href: '/dashboard/appointments',
    icon: Calendar,
    primary: true,
  },
  {
    label: 'Manage Availability',
    href: '/dashboard/availability',
    icon: Clock,
    primary: false,
  },
  {
    label: 'View Patients',
    href: '/dashboard/patients',
    icon: Users,
    primary: false,
  },
]

export function DoctorQuickActions() {
  return (
    <Card className="border-slate-200 shadow-sm">
      <CardHeader className="pb-4">
        <CardTitle className="text-base font-semibold text-slate-900">
          Quick Actions
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-3">
          {actions.map((action) => (
            <Link key={action.label} href={action.href}>
              <Button
                variant={action.primary ? 'default' : 'outline'}
                className={`
                  flex flex-col items-center gap-2 h-auto py-4 px-6 rounded-xl min-w-[140px]
                  ${action.primary
                    ? 'bg-teal-600 hover:bg-teal-700 text-white shadow-md'
                    : 'border-slate-200 text-slate-700 hover:bg-slate-50 hover:border-slate-300'
                  }
                `}
              >
                <action.icon className="h-5 w-5" />
                <span className="text-xs font-medium whitespace-nowrap">{action.label}</span>
              </Button>
            </Link>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
