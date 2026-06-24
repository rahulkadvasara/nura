'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ShieldCheck, ShieldAlert, Clock, CheckCircle2, AlertCircle, XCircle } from 'lucide-react'

interface VerificationStatusCardProps {
  profileStatus: 'pending' | 'verified' | 'rejected' | 'suspended'
  documentStatus: 'pending' | 'approved' | 'rejected'
}

export function VerificationStatusCard({ profileStatus, documentStatus }: VerificationStatusCardProps) {
  const getStatusDetails = (status: string) => {
    switch (status) {
      case 'verified':
      case 'approved':
        return {
          label: 'Approved',
          className: 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-50',
          icon: CheckCircle2,
          iconColor: 'text-emerald-500',
        }
      case 'rejected':
        return {
          label: 'Rejected',
          className: 'bg-red-50 text-red-700 border-red-200 hover:bg-red-50',
          icon: XCircle,
          iconColor: 'text-red-500',
        }
      case 'suspended':
        return {
          label: 'Suspended',
          className: 'bg-rose-50 text-rose-700 border-rose-200 hover:bg-rose-50',
          icon: XCircle,
          iconColor: 'text-rose-500',
        }
      case 'pending':
      default:
        return {
          label: 'Pending Review',
          className: 'bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-50',
          icon: Clock,
          iconColor: 'text-amber-500',
        }
    }
  }

  const profileDetails = getStatusDetails(profileStatus)
  const documentDetails = getStatusDetails(documentStatus)

  // Overall status summary
  const isFullyVerified = (profileStatus === 'verified') && (documentStatus === 'approved')
  const isRejected = (profileStatus === 'rejected') || (documentStatus === 'rejected') || (profileStatus === 'suspended')

  return (
    <Card className="border-slate-200 shadow-sm hover:shadow-md transition-shadow">
      <CardHeader className="pb-3 flex flex-row items-center justify-between">
        <CardTitle className="text-base font-semibold text-slate-900">
          Verification Status
        </CardTitle>
        {isFullyVerified ? (
          <ShieldCheck className="h-5 w-5 text-emerald-500" />
        ) : isRejected ? (
          <ShieldAlert className="h-5 w-5 text-red-500" />
        ) : (
          <Clock className="h-5 w-5 text-amber-500" />
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Overall Status Banner */}
        <div className={`p-3 rounded-lg border text-xs leading-relaxed ${
          isFullyVerified 
            ? 'bg-emerald-50/50 border-emerald-100 text-emerald-800' 
            : isRejected 
              ? 'bg-red-50/50 border-red-100 text-red-800' 
              : 'bg-amber-50/50 border-amber-100 text-amber-800'
        }`}>
          {isFullyVerified && 'Your medical profile and credentials are fully verified. You are active and visible to patients.'}
          {isRejected && 'Your verification review was rejected. Please contact the administrator to re-verify your documents.'}
          {!isFullyVerified && !isRejected && 'Your credentials are under review. Verification normally takes 24-48 hours.'}
        </div>

        {/* Row 1: Profile status */}
        <div className="flex items-center justify-between py-2 border-b border-slate-100">
          <div className="space-y-0.5">
            <p className="text-xs font-semibold text-slate-700">Profile Status</p>
            <p className="text-[10px] text-slate-400">Doctor details & practice setup</p>
          </div>
          <div className="flex items-center gap-2">
            <profileDetails.icon className={`h-4 w-4 ${profileDetails.iconColor}`} />
            <Badge variant="outline" className={`rounded-full px-2.5 py-0.5 font-medium text-[11px] ${profileDetails.className}`}>
              {profileDetails.label}
            </Badge>
          </div>
        </div>

        {/* Row 2: Document status */}
        <div className="flex items-center justify-between py-2">
          <div className="space-y-0.5">
            <p className="text-xs font-semibold text-slate-700">Document Verification</p>
            <p className="text-[10px] text-slate-400">License and medical degree review</p>
          </div>
          <div className="flex items-center gap-2">
            <documentDetails.icon className={`h-4 w-4 ${documentDetails.iconColor}`} />
            <Badge variant="outline" className={`rounded-full px-2.5 py-0.5 font-medium text-[11px] ${documentDetails.className}`}>
              {documentDetails.label}
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
