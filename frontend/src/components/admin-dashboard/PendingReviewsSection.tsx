'use client'

import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { usePendingDoctors } from '@/hooks/use-admin-doctor'
import { ClipboardList, ArrowRight, Clock, User, Calendar, Stethoscope, AlertCircle } from 'lucide-react'

export function PendingReviewsSection() {
  const { data: pending, isLoading, isError, error } = usePendingDoctors()

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr)
      return date.toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric'
      })
    } catch {
      return dateStr
    }
  }

  return (
    <Card className="border-slate-200 shadow-sm hover:shadow-md transition-shadow">
      <CardHeader className="pb-3 flex flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <ClipboardList className="h-5 w-5 text-teal-600" />
          <CardTitle className="text-base font-semibold text-slate-900">
            Pending Doctor Applications
          </CardTitle>
        </div>
        <Link
          href="/dashboard/admin/doctors"
          className="text-sm font-medium text-teal-600 hover:text-teal-700 transition-colors flex items-center gap-0.5"
        >
          View Verification Center
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            <div className="h-14 bg-slate-50 border border-slate-100 rounded-lg animate-pulse" />
            <div className="h-14 bg-slate-50 border border-slate-100 rounded-lg animate-pulse" />
          </div>
        ) : isError ? (
          <div className="p-4 rounded-lg bg-rose-50 border border-rose-100 text-rose-700 flex items-center gap-2 text-xs">
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            <span>{(error as Error)?.message || 'Failed to load applications'}</span>
          </div>
        ) : !pending || pending.length === 0 ? (
          <div className="text-center py-8 bg-slate-50 border border-slate-100 rounded-lg">
            <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-teal-50 mb-3">
              <ClipboardList className="h-5 w-5 text-teal-600" />
            </div>
            <h3 className="text-xs font-semibold text-slate-800 mb-1">
              All Caught Up
            </h3>
            <p className="text-[11px] text-slate-400 max-w-[240px] mx-auto leading-normal">
              No new medical applications are currently pending administrative credentials review.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {pending.slice(0, 3).map((applicant) => (
              <div 
                key={applicant.id} 
                className="py-3.5 first:pt-0 last:pb-0 flex items-center justify-between gap-4"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-sm text-slate-800">
                      {applicant.full_name}
                    </span>
                    <Badge variant="outline" className="rounded-full bg-amber-50 text-amber-700 border-amber-200 text-[10px] font-bold px-2 py-0">
                      Pending Check
                    </Badge>
                  </div>
                  <div className="flex flex-wrap gap-x-3 gap-y-1 text-slate-500 text-xs">
                    <span className="flex items-center gap-1">
                      <Stethoscope className="h-3.5 w-3.5 text-slate-400" />
                      {applicant.specialization}
                    </span>
                    <span className="flex items-center gap-1">
                      <Calendar className="h-3.5 w-3.5 text-slate-400" />
                      Applied: {formatDate(applicant.created_at)}
                    </span>
                  </div>
                </div>
                <Link href={`/dashboard/admin/doctors?id=${applicant.id}`}>
                  <Button size="sm" variant="outline" className="border-slate-200 text-slate-700 hover:bg-slate-50 hover:text-slate-900 h-8 rounded-lg text-xs font-medium">
                    Review
                  </Button>
                </Link>
              </div>
            ))}
            {pending.length > 3 && (
              <div className="pt-3 text-center">
                <Link href="/dashboard/admin/doctors">
                  <span className="text-xs font-semibold text-teal-600 hover:text-teal-700 cursor-pointer">
                    + {pending.length - 3} more pending applications
                  </span>
                </Link>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
