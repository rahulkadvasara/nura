'use client'

import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ShieldCheck, IndianRupee, Users } from 'lucide-react'

const actions = [
  {
    label: 'Review Doctors',
    href: '/dashboard/admin/verify',
    icon: ShieldCheck,
    primary: true,
  },
  {
    label: 'View Revenue',
    href: '/dashboard/admin/revenue',
    icon: IndianRupee,
    primary: false,
  },
  {
    label: 'Manage Users',
    href: '/dashboard/admin/users',
    icon: Users,
    primary: false,
  },
]

export function AdminQuickActions() {
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
