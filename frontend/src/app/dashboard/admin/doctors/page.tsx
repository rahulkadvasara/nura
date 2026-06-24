'use client'

import { useState, useEffect, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import { 
  useAdminDoctors,
  useDoctorDetail, 
  useApproveDoctor, 
  useRejectDoctor,
  useSuspendDoctor,
  useReactivateDoctor
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
  Clock,
  UserX,
  UserCheck
} from 'lucide-react'
import { toast } from 'sonner'

function VerificationQueueContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const urlSelectedId = searchParams.get('id')
  
  const [activeTab, setActiveTab] = useState<'pending' | 'verified' | 'rejected' | 'suspended'>('pending')
  const { data: doctorsQueue, isLoading: listLoading, isError: listError, refetch } = useAdminDoctors(activeTab)
  
  const [selectedId, setSelectedId] = useState<string | null>(null)
  
  const { data: selectedDoctor, isLoading: detailLoading } = useDoctorDetail(selectedId)
  const approveMutation = useApproveDoctor()
  const rejectMutation = useRejectDoctor()
  const suspendMutation = useSuspendDoctor()
  const reactivateMutation = useReactivateDoctor()

  const [rejectionReason, setRejectionReason] = useState('')
  const [showRejectModal, setShowRejectModal] = useState(false)
  const [showSuspendModal, setShowSuspendModal] = useState(false)
  const [showReactivateModal, setShowReactivateModal] = useState(false)

  // Sync state with URL search param
  useEffect(() => {
    if (urlSelectedId) {
      setSelectedId(urlSelectedId)
    } else if (doctorsQueue && doctorsQueue.length > 0 && !selectedId) {
      setSelectedId(doctorsQueue[0].id)
    } else if (!doctorsQueue || doctorsQueue.length === 0) {
      setSelectedId(null)
    }
  }, [urlSelectedId, doctorsQueue])

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
      const nextPending = doctorsQueue?.find(d => d.id !== selectedId)
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
      const nextPending = doctorsQueue?.find(d => d.id !== selectedId)
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

  const handleSuspend = async () => {
    if (!selectedId) return
    try {
      await suspendMutation.mutateAsync(selectedId)
      toast.success('Doctor practitioner suspended successfully')
      setShowSuspendModal(false)
      const nextDoctor = doctorsQueue?.find(d => d.id !== selectedId)
      if (nextDoctor) {
        selectDoctor(nextDoctor.id)
      } else {
        setSelectedId(null)
        router.replace('/dashboard/admin/doctors')
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to suspend doctor')
    }
  }

  const handleReactivate = async () => {
    if (!selectedId) return
    try {
      await reactivateMutation.mutateAsync(selectedId)
      toast.success('Doctor practitioner reactivated successfully')
      setShowReactivateModal(false)
      const nextDoctor = doctorsQueue?.find(d => d.id !== selectedId)
      if (nextDoctor) {
        selectDoctor(nextDoctor.id)
      } else {
        setSelectedId(null)
        router.replace('/dashboard/admin/doctors')
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to reactivate doctor')
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

  const tabs = [
    { id: 'pending', name: 'Pending' },
    { id: 'verified', name: 'Approved' },
    { id: 'rejected', name: 'Rejected' },
    { id: 'suspended', name: 'Suspended' }
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Doctor Operations Center</h1>
        <p className="text-slate-500">Review credentials, verify profiles, and manage active status of medical practitioners.</p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 gap-1 bg-slate-50/50 p-1 rounded-lg max-w-md">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => {
              setActiveTab(tab.id as any)
              setSelectedId(null)
              router.replace('/dashboard/admin/doctors')
            }}
            className={`flex-1 py-2 text-center text-xs font-semibold rounded-md transition-all ${
              activeTab === tab.id
                ? 'bg-white text-teal-600 shadow-sm border border-slate-200/50'
                : 'text-slate-550 hover:text-slate-900 hover:bg-white/50'
            }`}
          >
            {tab.name}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Review Queue */}
        <div className="space-y-4">
          <Card className="border-slate-200 shadow-sm h-[calc(100vh-280px)] flex flex-col">
            <CardHeader className="pb-3 border-b">
              <CardTitle className="text-base font-semibold text-slate-900 flex items-center gap-2">
                <ClipboardList className="h-5 w-5 text-teal-600" />
                {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} List
                {doctorsQueue && doctorsQueue.length > 0 && (
                  <Badge className="ml-auto bg-teal-600 hover:bg-teal-700 text-white font-bold">
                    {doctorsQueue.length}
                  </Badge>
                )}
              </CardTitle>
              <CardDescription className="text-xs">
                {activeTab === 'pending'
                  ? 'Awaiting administrative review'
                  : activeTab === 'verified'
                  ? 'Active practitioners on platform'
                  : activeTab === 'rejected'
                  ? 'Rejected application profiles'
                  : 'Suspended doctor credentials'}
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
              ) : !doctorsQueue || doctorsQueue.length === 0 ? (
                <div className="text-center py-16 text-slate-400">
                  <ClipboardList className="h-12 w-12 mx-auto mb-3 text-slate-300" />
                  <p className="text-sm font-semibold text-slate-800">Queue is Empty</p>
                  <p className="text-xs text-slate-400 mt-1 max-w-[200px] mx-auto">
                    No doctor profiles found in this category.
                  </p>
                </div>
              ) : (
                doctorsQueue.map((doctor) => {
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
                        <div className="flex items-center gap-1.5">
                          <p className="font-semibold text-sm text-slate-900">{doctor.full_name}</p>
                          {doctor.is_active === false && (
                            <span className="h-2 w-2 rounded-full bg-rose-500" title="User account suspended" />
                          )}
                        </div>
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
            <Card className="border-slate-200 shadow-sm h-[calc(100vh-280px)] flex flex-col items-center justify-center text-center p-8 bg-slate-50 border-dashed">
              <div className="p-4 rounded-full bg-slate-100 mb-4">
                <Info className="h-8 w-8 text-slate-400" />
              </div>
              <h3 className="text-base font-semibold text-slate-800 mb-1">
                No Practitioner Selected
              </h3>
              <p className="text-sm text-slate-500 max-w-sm">
                Select a doctor application profile from the left column queue to view details and professional credentials.
              </p>
            </Card>
          ) : detailLoading ? (
            <Card className="border-slate-200 shadow-sm h-[calc(100vh-280px)] flex items-center justify-center">
              <div className="space-y-4 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600 mx-auto" />
                <p className="text-sm text-slate-500">Retrieving practitioner records...</p>
              </div>
            </Card>
          ) : !selectedDoctor ? (
            <Card className="border-slate-200 shadow-sm h-[calc(100vh-280px)] flex items-center justify-center p-8 text-rose-500">
              <ShieldAlert className="h-8 w-8 mx-auto mb-2" />
              <p className="text-sm font-semibold">Failed to retrieve profile detail data.</p>
            </Card>
          ) : (
            <Card className="border-slate-200 shadow-sm h-[calc(100vh-280px)] flex flex-col">
              <CardHeader className="pb-3 border-b flex flex-row items-center justify-between flex-wrap gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <CardTitle className="text-xl font-bold text-slate-900">
                      {selectedDoctor.user.full_name}
                    </CardTitle>
                    <Badge
                      variant="outline"
                      className={`rounded-full border text-xs px-2 py-0.5 capitalize font-bold ${
                        selectedDoctor.profile.profile_status === 'verified'
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : selectedDoctor.profile.profile_status === 'suspended'
                          ? 'bg-rose-50 text-rose-700 border-rose-200 animate-pulse'
                          : selectedDoctor.profile.profile_status === 'rejected'
                          ? 'bg-slate-100 text-slate-700 border-slate-200'
                          : 'bg-amber-50 text-amber-700 border-amber-200'
                      }`}
                    >
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
                  {selectedDoctor.profile.profile_status === 'pending' && (
                    <>
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
                        className="bg-teal-600 hover:bg-teal-700 text-white h-9 rounded-lg shadow-sm border-0"
                        disabled={approveMutation.isPending || rejectMutation.isPending}
                      >
                        <Check className="mr-1.5 h-4 w-4" />
                        Approve & Promote
                      </Button>
                    </>
                  )}

                  {selectedDoctor.profile.profile_status === 'verified' && (
                    <Button
                      onClick={() => setShowSuspendModal(true)}
                      variant="destructive"
                      className="h-9 rounded-lg shadow-sm"
                      disabled={suspendMutation.isPending}
                    >
                      <UserX className="mr-1.5 h-4 w-4" />
                      Suspend Practitioner
                    </Button>
                  )}

                  {selectedDoctor.profile.profile_status === 'suspended' && (
                    <Button
                      onClick={() => setShowReactivateModal(true)}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white h-9 rounded-lg shadow-sm border-0"
                      disabled={reactivateMutation.isPending}
                    >
                      <UserCheck className="mr-1.5 h-4 w-4" />
                      Reactivate Practitioner
                    </Button>
                  )}
                </div>
              </CardHeader>
              
              <CardContent className="flex-1 overflow-y-auto p-6 space-y-6">
                {/* Rejection Notice */}
                {selectedDoctor.profile.profile_status === 'rejected' && selectedDoctor.profile.rejection_reason && (
                  <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 text-rose-800 text-sm flex gap-3 items-start">
                    <ShieldAlert className="h-5 w-5 text-rose-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold">Application Rejection Reason:</span>
                      <p className="mt-1 text-xs text-rose-700 leading-relaxed">
                        {selectedDoctor.profile.rejection_reason}
                      </p>
                    </div>
                  </div>
                )}

                {/* Suspension Notice */}
                {selectedDoctor.profile.profile_status === 'suspended' && (
                  <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 text-rose-800 text-sm flex gap-3 items-start">
                    <ShieldAlert className="h-5 w-5 text-rose-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold">Practitioner Suspended</span>
                      <p className="mt-1 text-xs text-rose-700 leading-relaxed font-semibold">
                        This doctor profile is suspended. Their user login access is disabled, all active web sessions are revoked, and their doctor dashboard is locked out.
                      </p>
                    </div>
                  </div>
                )}

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

      {/* Suspend Confirmation Modal */}
      {showSuspendModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-md border-slate-200 shadow-xl bg-white animate-in zoom-in-95 duration-150">
            <CardHeader className="pb-3 border-b">
              <CardTitle className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <ShieldAlert className="h-5 w-5 text-rose-600" />
                Suspend Doctor Practitioner
              </CardTitle>
              <CardDescription>
                Confirm suspension of professional profile and access rights.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-4 space-y-4">
              <p className="text-sm text-slate-600">
                Are you sure you want to suspend <span className="font-bold text-slate-900">{selectedDoctor?.user.full_name}</span>?
              </p>
              <div className="bg-rose-50 border border-rose-100 rounded-lg p-3 text-xs text-rose-700 space-y-1 font-semibold">
                <p>• Associated user account will be deactivated.</p>
                <p>• All active login sessions will be immediately terminated.</p>
                <p>• Practitioner will be blocked from accessing the doctor dashboard and scheduling slots.</p>
              </div>
              <div className="flex justify-end gap-2 pt-2 border-t">
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => setShowSuspendModal(false)}
                  className="border-slate-200"
                >
                  Cancel
                </Button>
                <Button 
                  type="button" 
                  onClick={handleSuspend}
                  variant="destructive"
                >
                  Suspend Practitioner
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Reactivate Confirmation Modal */}
      {showReactivateModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-md border-slate-200 shadow-xl bg-white animate-in zoom-in-95 duration-150">
            <CardHeader className="pb-3 border-b">
              <CardTitle className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <UserCheck className="h-5 w-5 text-emerald-600" />
                Reactivate Doctor Practitioner
              </CardTitle>
              <CardDescription>
                Confirm reactivation of doctor profile and platform access.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-4 space-y-4">
              <p className="text-sm text-slate-600">
                Are you sure you want to reactivate <span className="font-bold text-slate-900">{selectedDoctor?.user.full_name}</span>?
              </p>
              <div className="bg-emerald-50 border border-emerald-100 rounded-lg p-3 text-xs text-emerald-700 space-y-1">
                <p>• Doctor&apos;s profile status will be restored to Verified.</p>
                <p>• Associated user account will be reactivated, allowing them to login.</p>
              </div>
              <div className="flex justify-end gap-2 pt-2 border-t">
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => setShowReactivateModal(false)}
                  className="border-slate-200"
                >
                  Cancel
                </Button>
                <Button 
                  type="button" 
                  onClick={handleReactivate}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white border-0"
                >
                  Reactivate Profile
                </Button>
              </div>
            </CardContent>
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
