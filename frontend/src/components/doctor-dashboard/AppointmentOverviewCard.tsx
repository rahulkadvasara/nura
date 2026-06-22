'use client'

import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Calendar, ArrowRight } from 'lucide-react'

interface AppointmentOverviewCardProps {
  todaysCount: number
  upcomingCount: number
}

export function AppointmentOverviewCard({ todaysCount, upcomingCount }: AppointmentOverviewCardProps) {
  return (
    <Card className="border-slate-200 shadow-sm h-full flex flex-col justify-between">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-semibold text-slate-900">
            Today&apos;s Appointments
          </CardTitle>
          <Link
            href="/dashboard/appointments"
            className="text-sm font-medium text-teal-600 hover:text-teal-700 transition-colors flex items-center gap-0.5"
          >
            View Schedule
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col justify-center py-6">
        {todaysCount === 0 ? (
          <div className="flex flex-col items-center justify-center text-center">
            <div className="p-4 rounded-full bg-slate-100 mb-4">
              <Calendar className="h-6 w-6 text-slate-400" />
            </div>
            <p className="text-sm font-medium text-slate-700 mb-1">
              No appointments scheduled for today
            </p>
            <p className="text-xs text-slate-400 mb-5 max-w-[240px]">
              {upcomingCount > 0 
                ? `You have ${upcomingCount} upcoming appointment${upcomingCount !== 1 ? 's' : ''} scheduled for future dates.`
                : 'Your schedule is currently clear.'
              }
            </p>
            <Link href="/dashboard/appointments">
              <Button
                variant="outline"
                size="sm"
                className="border-slate-200 text-slate-700 hover:bg-slate-50 rounded-lg"
              >
                Go to Schedule
              </Button>
            </Link>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center text-center">
            <div className="p-4 rounded-full bg-teal-50 mb-3">
              <Calendar className="h-6 w-6 text-teal-600" />
            </div>
            <p className="text-3xl font-extrabold text-slate-900 mb-1">
              {todaysCount}
            </p>
            <p className="text-sm font-semibold text-slate-700">
              Appointment{todaysCount !== 1 ? 's' : ''} Today
            </p>
            <p className="text-xs text-slate-400 mt-2 max-w-[260px]">
              You have {todaysCount} session{todaysCount !== 1 ? 's' : ''} scheduled for today. 
              {upcomingCount > 0 && ` Additionally, you have ${upcomingCount} upcoming slot${upcomingCount !== 1 ? 's' : ''} in the future.`}
            </p>
            <Link href="/dashboard/appointments" className="mt-5">
              <Button
                size="sm"
                className="bg-teal-600 hover:bg-teal-700 text-white rounded-lg px-5 shadow-sm"
              >
                View Today&apos;s List
              </Button>
            </Link>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
