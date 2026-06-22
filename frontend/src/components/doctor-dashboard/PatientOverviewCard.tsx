'use client'

import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Users, ArrowRight } from 'lucide-react'

interface PatientOverviewCardProps {
  count: number
}

export function PatientOverviewCard({ count }: PatientOverviewCardProps) {
  return (
    <Card className="border-slate-200 shadow-sm h-full flex flex-col justify-between">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-semibold text-slate-900">
            Patients Overview
          </CardTitle>
          <Link
            href="/dashboard/patients"
            className="text-sm font-medium text-teal-600 hover:text-teal-700 transition-colors flex items-center gap-0.5"
          >
            View Patients
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col justify-center py-6">
        {count === 0 ? (
          <div className="flex flex-col items-center justify-center text-center">
            <div className="p-4 rounded-full bg-slate-100 mb-4">
              <Users className="h-6 w-6 text-slate-400" />
            </div>
            <p className="text-sm font-medium text-slate-700 mb-1">
              No patients registered
            </p>
            <p className="text-xs text-slate-400 mb-5 max-w-[220px]">
              When patients book appointments with you, they will appear here in your roster.
            </p>
            <Link href="/dashboard/patients">
              <Button
                variant="outline"
                size="sm"
                className="border-slate-200 text-slate-700 hover:bg-slate-50 rounded-lg"
              >
                Go to Patient Roster
              </Button>
            </Link>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center text-center">
            <div className="p-4 rounded-full bg-indigo-50 mb-3">
              <Users className="h-6 w-6 text-indigo-600" />
            </div>
            <p className="text-3xl font-extrabold text-slate-900 mb-1">
              {count}
            </p>
            <p className="text-sm font-semibold text-slate-700">
              Total Patient{count !== 1 ? 's' : ''}
            </p>
            <p className="text-xs text-slate-400 mt-2 max-w-[240px]">
              You have {count} unique patient{count !== 1 ? 's' : ''} associated with your medical practice.
            </p>
            <Link href="/dashboard/patients" className="mt-5">
              <Button
                size="sm"
                className="bg-teal-600 hover:bg-teal-700 text-white rounded-lg px-5 shadow-sm"
              >
                Manage Patients
              </Button>
            </Link>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
