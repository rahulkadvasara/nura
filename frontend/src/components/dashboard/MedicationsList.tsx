'use client'

import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Pill, Plus } from 'lucide-react'

export function MedicationsList() {
  // Medications data is not part of the patient dashboard API response.
  // This widget always shows the empty state for now; it will be connected
  // once the medications/reminders list API is implemented.
  return (
    <Card className="border-slate-200 shadow-sm h-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-semibold text-slate-900">
            Today&apos;s Medications
          </CardTitle>
          <Link
            href="/dashboard/reminders"
            className="text-sm font-medium text-teal-600 hover:text-teal-700 transition-colors"
          >
            Manage
          </Link>
        </div>
      </CardHeader>
      <CardContent>
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
      </CardContent>
    </Card>
  )
}
