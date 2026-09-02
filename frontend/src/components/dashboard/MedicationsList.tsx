'use client'

import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Pill, Plus, Clock, RefreshCw } from 'lucide-react'
import { usePatientReminders } from '@/hooks/use-reminder'

export function MedicationsList() {
  const { data: reminders, isLoading } = usePatientReminders()

  const format12HourDisplay = (timeStr: string) => {
    if (!timeStr) return ''
    const parts = timeStr.split(':')
    if (parts.length < 2) return timeStr
    let hour = parseInt(parts[0], 10)
    const minute = parts[1].padStart(2, '0')
    if (isNaN(hour)) return timeStr
    const period = hour >= 12 ? 'PM' : 'AM'
    hour = hour % 12 || 12
    return `${hour}:${minute} ${period}`
  }

  return (
    <Card className="border-slate-200 shadow-sm h-full flex flex-col">
      <CardHeader className="pb-3 border-b border-slate-100 bg-slate-50/50">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-semibold text-slate-900 flex items-center gap-2">
            <Pill className="h-5 w-5 text-teal-600" />
            Today&apos;s Medications & Reminders
          </CardTitle>
          <Link
            href="/dashboard/reminders"
            className="text-xs font-bold text-teal-700 hover:text-teal-800 transition-colors bg-teal-50 px-2.5 py-1 rounded-md border border-teal-200"
          >
            Manage All
          </Link>
        </div>
      </CardHeader>
      <CardContent className="p-4 flex-1">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-8">
            <RefreshCw className="h-6 w-6 animate-spin text-teal-600 mb-2" />
            <span className="text-xs text-slate-400 font-medium">Loading reminders...</span>
          </div>
        ) : reminders && reminders.length > 0 ? (
          <div className="space-y-2.5">
            {reminders.map((rem: any) => (
              <div
                key={rem.id}
                className="border border-slate-200 rounded-lg p-3 bg-white flex items-center justify-between gap-3 hover:border-teal-200 hover:shadow-2xs transition-all"
              >
                <div className="space-y-1 min-w-0 flex-1">
                  <span className="text-xs font-bold text-slate-900 truncate block">
                    {rem.title}
                  </span>
                  <div className="flex items-center gap-2 text-[10px] text-slate-500 font-semibold">
                    <span className="bg-teal-50 text-teal-750 px-1.5 py-0.5 rounded font-bold uppercase border border-teal-100">
                      {rem.reminder_type}
                    </span>
                    <span>•</span>
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3 text-slate-400" />
                      {format12HourDisplay(rem.scheduled_time)}
                    </span>
                  </div>
                </div>
                <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200 capitalize">
                  {rem.status}
                </span>
              </div>
            ))}
            <div className="pt-2">
              <Link href="/dashboard/reminders">
                <Button
                  size="sm"
                  variant="outline"
                  className="w-full text-xs font-semibold border-slate-200 hover:bg-slate-50 text-teal-700"
                >
                  <Plus className="h-3.5 w-3.5 mr-1" />
                  Add New Medication Reminder
                </Button>
              </Link>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <div className="p-4 rounded-full bg-slate-100 mb-4">
              <Pill className="h-6 w-6 text-slate-400" />
            </div>
            <p className="text-sm font-medium text-slate-700 mb-1">
              No medications added
            </p>
            <p className="text-xs text-slate-400 mb-5 max-w-[240px]">
              Add your prescriptions to track doses and get reminders.
            </p>
            <Link href="/dashboard/reminders">
              <Button
                size="sm"
                className="bg-teal-600 hover:bg-teal-700 text-white rounded-lg"
              >
                <Plus className="h-4 w-4 mr-1" />
                Add Medication
              </Button>
            </Link>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
