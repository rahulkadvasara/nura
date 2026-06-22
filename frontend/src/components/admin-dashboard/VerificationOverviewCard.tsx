'use client'

import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ShieldCheck, Clock, ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface VerificationOverviewCardProps {
  pendingCount: number
  verifiedCount: number
}

export function VerificationOverviewCard({ pendingCount, verifiedCount }: VerificationOverviewCardProps) {
  return (
    <Card className="border-slate-200 shadow-sm hover:shadow-md transition-shadow">
      <CardHeader className="pb-3 flex flex-row items-center justify-between">
        <CardTitle className="text-base font-semibold text-slate-900">
          Doctor Credentials Review
        </CardTitle>
        <Link
          href="/dashboard/admin/verify"
          className="text-sm font-medium text-teal-600 hover:text-teal-700 transition-colors flex items-center gap-0.5"
        >
          Review Verification
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Verification banner alert */}
        {pendingCount > 0 ? (
          <div className="p-3 rounded-lg border border-amber-100 bg-amber-50/50 text-amber-800 text-xs leading-relaxed flex items-start gap-2">
            <Clock className="h-4 w-4 text-amber-500 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold">Action Required:</span> {pendingCount} doctor profile{pendingCount !== 1 ? 's' : ''} awaiting license and document check.
            </div>
          </div>
        ) : (
          <div className="p-3 rounded-lg border border-emerald-100 bg-emerald-50/50 text-emerald-800 text-xs leading-relaxed flex items-start gap-2">
            <ShieldCheck className="h-4 w-4 text-emerald-500 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold">All Caught Up:</span> No doctor profiles currently pending administrative verification.
            </div>
          </div>
        )}

        {/* Breakdown Row 1: Pending */}
        <div className="flex items-center justify-between py-2 border-b border-slate-100">
          <div className="space-y-0.5">
            <p className="text-xs font-semibold text-slate-700">Pending Review</p>
            <p className="text-[10px] text-slate-400">Doctors waiting to onboard</p>
          </div>
          <Badge variant="outline" className={`rounded-full px-2.5 py-0.5 font-bold text-xs ${
            pendingCount > 0 
              ? 'bg-amber-50 text-amber-700 border-amber-200' 
              : 'bg-slate-50 text-slate-500 border-slate-200'
          }`}>
            {pendingCount}
          </Badge>
        </div>

        {/* Breakdown Row 2: Verified */}
        <div className="flex items-center justify-between py-2">
          <div className="space-y-0.5">
            <p className="text-xs font-semibold text-slate-700">Verified Doctors</p>
            <p className="text-[10px] text-slate-400">Active and practicing doctors</p>
          </div>
          <Badge variant="outline" className="rounded-full px-2.5 py-0.5 font-bold text-xs bg-emerald-50 text-emerald-700 border-emerald-200">
            {verifiedCount}
          </Badge>
        </div>
      </CardContent>
    </Card>
  )
}
