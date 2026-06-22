'use client'

import { useState, useEffect, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { 
  usePendingDoctors, 
  useDoctorDetail, 
  useApproveDoctor, 
  useRejectDoctor 
} from '@/hooks/use-admin-doctor'
import { 
  ClipboardList, 
  Stethoscope, 
  User, 
  Mail, 
  Award, 
  Building, 
  FileText, 
  ShieldAlert, 
  Check, 
  X, 
  ExternalLink,
  ChevronRight,
  Info,
  Clock
} from 'lucide-react'
import { toast } from 'sonner'

function VerificationQueueContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const urlSelectedId = searchParams.get('id')
  
  const { data: pendingQueue, isLoading: listLoading, isError: listError, refetch } = usePendingDoctors()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  
  const { data: selectedDoctor, isLoading: detailLoading } = useDoctorDetail(selectedId)
  const approveMutation = useApproveDoctor()
  const rejectMutation = useRejectDoctor()

  const [rejectionReason, setRejectionReason] = useState('')
  const [showRejectModal, setShowRejectModal] = useState(false)

  // Sync state with URL search param
  useEffect(() => {
    if (urlSelectedId) {
      setSelectedId(urlSelectedId)
    } else if (pendingQueue && pendingQueue.length > 0 && !selectedId) {
      setSelectedId(pendingQueue[0].id)
    }
  }, [urlSelectedId, pendingQueue])

  const selectDoctor = (id: string) => {
    setSelectedId(id)
    router.replace(`/dashboard/admin/doctors?id=${id}`)
  }

  const handleApprove = async () => {
    if (!selectedId) return
    try {
      await approveMutation.mutateAsync(selectedId)
      toast.success('Doctor application approved successfully')
      setRejectionReason('')
      // Select first in remaining queue if any
      const nextPending = pendingQueue?.find(d => d.id !== selectedId)
      if (nextPending) {
        selectDoctor(nextPending.id)
      } else {
        setSelectedId(null)
        router.replace('/dashboard/admin/doctors')
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to approve application')
    }
  }

  const handleReject = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedId) return
    if (!rejectionReason.trim()) {
      toast.error('Rejection reason is required')
      return
    }

    try {
      await rejectMutation.mutateAsync({
        profileId: selectedId,
        reason: rejectionReason
      })
      toast.success('Doctor application rejected successfully')
      setShowRejectModal(false)
      setRejectionReason('')
      // Select first in remaining queue if any
      const nextPending = pendingQueue?.find(d => d.id !== selectedId)
      if (nextPending) {
        selectDoctor(nextPending.id)
      } else {
        setSelectedId(null)
        router.replace('/dashboard/admin/doctors')
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to reject application')
    }
  }

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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Doctor Verification Center</h1>
        <p className="text-slate-500">Review medical licenses and academic credentials to authorize doctor status.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Review Queue */}
        <div className="space-y-4">
          <Card className="border-slate-200 shadow-sm h-[calc(100vh-220px)] flex flex-col">
            <CardHeader className="pb-3 border-b">
              <CardTitle className="text-base font-semibold text-slate-900 flex items-center gap-2">
                <ClipboardList className="h-5 w-5 text-teal-600" />
                Onboarding Queue
                {pendingQueue && pendingQueue.length > 0 && (
                  <Badge className="ml-auto bg-teal-600 hover:bg-teal-700 text-white font-bold">
                    {pendingQueue.length}
                  </Badge>
                )}
              </CardTitle>
              <CardDescription className="text-xs">
                Pending administrative checks
              </CardDescription>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto p-3 space-y-2">
              {listLoading ? (
                <div className="space-y-2">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="h-16 bg-slate-50 rounded-lg animate-pulse" />
                  ))}
                </div>
              ) : listError ? (
                <div className="text-center py-8 text-rose-500">
                  <ShieldAlert className="h-8 w-8 mx-auto mb-2" />
                  <p className="text-sm font-semibold">Error loading queue</p>
                  <Button size="sm" variant="outline" className="mt-2" onClick={() => refetch()}>
                    Retry
                  </Button>
                </div>
              ) : !pendingQueue || pendingQueue.length === 0 ? (
                <div className="text-center py-16 text-slate-400">
                  <ClipboardList className="h-12 w-12 mx-auto mb-3 text-slate-300 animate-bounce" />
                  <p className="text-sm font-semibold text-slate-800">Queue is Empty</p>
                  <p className="text-xs text-slate-400 mt-1 max-w-[200px] mx-auto">
                    All doctor onboarding applications have been processed.
                  </p>
                </div>
              ) : (
                pendingQueue.map((doctor) => {
                  const isSelected = doctor.id === selectedId
                  return (
                    <div
                      key={doctor.id}
                      onClick={() => selectDoctor(doctor.id)}
                      className={`
                        p-3 rounded-xl border text-left cursor-pointer transition-all flex items-center justify-between
                        ${isSelected
                          ? 'border-teal-500 bg-teal-50/40 shadow-sm'
                          : 'border-slate-100 bg-white hover:bg-slate-50 hover:border-slate-200'
                        }
                      `}
                    >
                      <div className="space-y-1">
                        <p className="font-semibold text-sm text-slate-900">{doctor.full_name}</p>
                        <p className="text-xs text-slate-500 flex items-center gap-1">
                          <Stethoscope className="h-3 w-3 text-teal-600" />
                          {doctor.specialization}
                        </p>
                        <p className="text-[10px] text-slate-400 flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          Submitted {formatDate(doctor.created_at)}
                        </p>
                      </div>
                      <ChevronRight className={`h-4 w-4 text-slate-400 transition-transform ${isSelected ? 'translate-x-1 text-teal-600' : ''}`} />
                    </div>
                  )
                })
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Columns: Detail Panel */}
        <div className="lg:col-span-2">
          {!selectedId ? (
            <Card className="border-slate-200 shadow-sm h-[calc(100vh-220px)] flex flex-col items-center justify-center text-center p-8 bg-slate-50 border-dashed">
              <div className="p-4 rounded-full bg-slate-100 mb-4">
                <Info className="h-8 w-8 text-slate-400" />
              </div>
              <h3 className="text-base font-semibold text-slate-800 mb-1">
                No Applicant Selected
              </h3>
              <p className="text-sm text-slate-500 max-w-sm">
                Select a pending doctor from the onboarding queue on the left side to review their credentials and documents.
              </p>
            </Card>
          ) : detailLoading ? (
            <Card className="border-slate-200 shadow-sm h-[calc(100vh-220px)] flex items-center justify-center">
              <div className="space-y-4 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600 mx-auto" />
                <p className="text-sm text-slate-500">Retrieving applicant documents...</p>
              </div>
            </Card>
          ) : !selectedDoctor ? (
            <Card className="border-slate-200 shadow-sm h-[calc(100vh-220px)] flex items-center justify-center p-8 text-rose-500">
              <ShieldAlert className="h-8 w-8 mx-auto mb-2" />
              <p className="text-sm font-semibold">Failed to retrieve profile detail data.</p>
            </Card>
          ) : (
            <Card className="border-slate-200 shadow-sm h-[calc(100vh-220px)] flex flex-col">
              <CardHeader className="pb-3 border-b flex flex-row items-center justify-between flex-wrap gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <CardTitle className="text-xl font-bold text-slate-900">
                      {selectedDoctor.user.full_name}
                    </CardTitle>
                    <Badge variant="outline" className="rounded-full bg-amber-50 text-amber-700 border-amber-200 text-xs px-2 py-0.5 capitalize">
                      {selectedDoctor.profile.profile_status}
                    </Badge>
                  </div>
                  <CardDescription className="flex items-center gap-1.5 text-xs">
                    <Mail className="h-3.5 w-3.5 text-slate-400" />
                    {selectedDoctor.user.email}
                  </CardDescription>
                </div>
                
                {/* Actions */}
                <div className="flex gap-2">
                  <Button 
                    onClick={() => setShowRejectModal(true)} 
                    variant="outline" 
                    className="border-rose-200 hover:bg-rose-50 text-rose-700 h-9 rounded-lg"
                    disabled={approveMutation.isPending || rejectMutation.isPending}
                  >
                    <X className="mr-1.5 h-4 w-4" />
                    Reject
                  </Button>
                  <Button 
                    onClick={handleApprove} 
                    className="bg-teal-600 hover:bg-teal-700 text-white h-9 rounded-lg shadow-sm"
                    disabled={approveMutation.isPending || rejectMutation.isPending}
                  >
                    <Check className="mr-1.5 h-4 w-4" />
                    Approve & Promote
                  </Button>
                </div>
              </CardHeader>
              
              <CardContent className="flex-1 overflow-y-auto p-6 space-y-6">
                {/* Details Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-4">
                    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                      <Stethoscope className="h-4 w-4 text-teal-600" />
                      Professional Credentials
                    </h3>
                    <div className="bg-slate-50 border border-slate-100 rounded-xl p-4 space-y-3 text-sm">
                      <div className="flex justify-between border-b pb-2"><span className="text-slate-500">Specialization</span><span className="font-semibold text-slate-800">{selectedDoctor.profile.specialization}</span></div>
                      <div className="flex justify-between border-b pb-2"><span className="text-slate-500">Experience</span><span className="font-semibold text-slate-800">{selectedDoctor.profile.experience_years} Years</span></div>
                      <div className="flex justify-between border-b pb-2"><span className="text-slate-500">Consultation Fee</span><span className="font-semibold text-slate-800">₹{selectedDoctor.profile.consultation_fee}</span></div>
                      <div className="flex justify-between border-b pb-2"><span className="text-slate-500">License Number</span><span className="font-semibold text-slate-800">{selectedDoctor.profile.license_number || 'N/A'}</span></div>
                      <div className="flex justify-between"><span className="text-slate-500">Hospital</span><span className="font-semibold text-slate-800">{selectedDoctor.profile.hospital || 'Not provided'}</span></div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                      <Award className="h-4 w-4 text-teal-600" />
                      Education & Background
                    </h3>
                    <div className="bg-slate-50 border border-slate-100 rounded-xl p-4 space-y-3 text-sm">
                      <div className="border-b pb-2">
                        <span className="text-slate-500 block mb-1">Education / Degrees</span>
                        <span className="font-semibold text-slate-800">{selectedDoctor.profile.education || 'Not provided'}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block mb-1">Languages Spoken</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {selectedDoctor.profile.languages.map((lang, idx) => (
                            <Badge key={idx} variant="secondary" className="text-xs">
                              {lang}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Biography */}
                <div className="space-y-2">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Biography</h3>
                  <div className="bg-slate-50 border border-slate-100 rounded-xl p-4 text-slate-700 text-xs leading-relaxed italic">
                    &ldquo;{selectedDoctor.profile.bio || 'No biography details provided by doctor.'}&rdquo;
                  </div>
                </div>

                {/* Verification Documents Links */}
                <div className="space-y-3">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                    <FileText className="h-4 w-4 text-teal-600" />
                    Submitted Credential Documents
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {selectedDoctor.documents.map((doc) => (
                      <div 
                        key={doc.id}
                        className="bg-white border border-slate-200 rounded-xl p-4 flex flex-col justify-between h-[120px] shadow-sm hover:border-teal-500 transition-colors"
                      >
                        <div className="space-y-1">
                          <span className="text-xs font-bold capitalize text-slate-800 block">
                            {doc.document_type.replace('_', ' ')}
                          </span>
                          <span className="text-[10px] text-slate-400 block">
                            Status: <span className="capitalize">{doc.verification_status}</span>
                          </span>
                        </div>
                        <a 
                          href={doc.document_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-xs font-medium text-teal-600 hover:text-teal-700 transition-colors flex items-center gap-1.5 mt-2"
                        >
                          Open Document
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-md border-slate-200 shadow-xl bg-white animate-in zoom-in-95 duration-150">
            <form onSubmit={handleReject}>
              <CardHeader className="pb-3 border-b">
                <CardTitle className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <ShieldAlert className="h-5 w-5 text-rose-600" />
                  Reject Doctor Credentials
                </CardTitle>
                <CardDescription>
                  Please specify the exact reason for rejecting this doctor application.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-4 space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="reason">Reason for Rejection</Label>
                  <textarea
                    id="reason"
                    rows={4}
                    placeholder="e.g. License document URL is inaccessible, specialization mismatch, or invalid credentials..."
                    required
                    value={rejectionReason}
                    onChange={(e) => setRejectionReason(e.target.value)}
                    className="flex w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-rose-500 text-slate-800"
                  />
                </div>
                <div className="flex justify-end gap-2 pt-2 border-t">
                  <Button 
                    type="button" 
                    variant="outline" 
                    onClick={() => { setShowRejectModal(false); setRejectionReason('') }}
                    className="border-slate-200"
                  >
                    Cancel
                  </Button>
                  <Button 
                    type="submit" 
                    className="bg-rose-600 hover:bg-rose-700 text-white"
                    disabled={!rejectionReason.trim()}
                  >
                    Reject Credentials
                  </Button>
                </div>
              </CardContent>
            </form>
          </Card>
        </div>
      )}
    </div>
  )
}

export default function AdminDoctorsPage() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <Suspense fallback={
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
        </div>
      }>
        <VerificationQueueContent />
      </Suspense>
    </ProtectedRoute>
  )
}
