'use client'

import { useState, useEffect } from 'react'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { adminManagementService } from '@/services/admin-management.service'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import { toast } from 'react-hot-toast'
import {
  Shield,
  UserPlus,
  Search,
  User,
  Mail,
  Calendar,
  Clock,
  Activity,
  Power,
  AlertTriangle,
  Copy,
  Check,
  Loader2,
  X,
  Lock,
} from 'lucide-react'
import { User as UserType, AuditLog, AdminDetailResponse } from '@/types'

export default function AdminManagementPage() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <AdminManagementContent />
    </ProtectedRoute>
  )
}

function AdminManagementContent() {
  const [admins, setAdmins] = useState<UserType[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')

  // Selected Admin Detail
  const [selectedAdminId, setSelectedAdminId] = useState<string | null>(null)
  const [adminDetail, setAdminDetail] = useState<AdminDetailResponse | null>(null)
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [isDetailDrawerOpen, setIsDetailDrawerOpen] = useState(false)

  // Create Modal
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [createName, setCreateName] = useState('')
  const [createEmail, setCreateEmail] = useState('')
  const [creating, setCreating] = useState(false)
  const [tempPassword, setTempPassword] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  // Status Action (Enable/Disable) Confirmation Modal
  const [confirmModalOpen, setConfirmModalOpen] = useState(false)
  const [actionType, setActionType] = useState<'enable' | 'disable'>('enable')
  const [adminToUpdate, setAdminToUpdate] = useState<UserType | null>(null)
  const [updatingStatus, setUpdatingStatus] = useState(false)

  const fetchAdmins = async () => {
    try {
      setLoading(true)
      const res = await adminManagementService.listAdmins()
      if (res.success && res.data) {
        setAdmins(res.data)
      } else {
        toast.error(res.message || 'Failed to fetch administrators')
      }
    } catch (err) {
      console.error(err)
      toast.error('An error occurred while fetching administrators')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAdmins()
  }, [])

  const handleOpenDetail = async (adminId: string) => {
    try {
      setSelectedAdminId(adminId)
      setLoadingDetail(true)
      setIsDetailDrawerOpen(true)
      const res = await adminManagementService.getAdminDetail(adminId)
      if (res.success && res.data) {
        setAdminDetail(res.data)
      } else {
        toast.error(res.message || 'Failed to fetch administrator details')
        setIsDetailDrawerOpen(false)
      }
    } catch (err) {
      console.error(err)
      toast.error('Failed to load administrator details')
      setIsDetailDrawerOpen(false)
    } finally {
      setLoadingDetail(false)
    }
  }

  const handleCreateAdmin = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!createName.trim() || !createEmail.trim()) {
      toast.error('All fields are required')
      return
    }

    try {
      setCreating(true)
      const res = await adminManagementService.createAdmin({
        full_name: createName,
        email: createEmail,
      })

      if (res.success && res.data) {
        toast.success('Administrator created successfully!')
        setTempPassword(res.data.temporary_password)
        fetchAdmins()
      } else {
        toast.error(res.message || 'Failed to create administrator')
      }
    } catch (err: any) {
      console.error(err)
      const msg = err.response?.data?.message || 'Failed to create administrator'
      toast.error(msg)
    } finally {
      setCreating(false)
    }
  }

  const closeCreateModal = () => {
    setIsCreateModalOpen(false)
    setCreateName('')
    setCreateEmail('')
    setTempPassword(null)
    setCopied(false)
  }

  const copyToClipboard = () => {
    if (tempPassword) {
      navigator.clipboard.writeText(tempPassword)
      setCopied(true)
      toast.success('Password copied to clipboard!')
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const openConfirmModal = (admin: UserType, type: 'enable' | 'disable') => {
    setAdminToUpdate(admin)
    setActionType(type)
    setConfirmModalOpen(true)
  }

  const handleToggleStatus = async () => {
    if (!adminToUpdate) return

    try {
      setUpdatingStatus(true)
      const res =
        actionType === 'enable'
          ? await adminManagementService.enableAdmin(adminToUpdate.id)
          : await adminManagementService.disableAdmin(adminToUpdate.id)

      if (res.success) {
        toast.success(`Administrator successfully ${actionType}d`)
        setConfirmModalOpen(false)
        fetchAdmins()
        
        // Refresh detail view if it's open for the updated admin
        if (isDetailDrawerOpen && selectedAdminId === adminToUpdate.id) {
          handleOpenDetail(adminToUpdate.id)
        }
      } else {
        toast.error(res.message || `Failed to ${actionType} administrator`)
      }
    } catch (err: any) {
      console.error(err)
      const msg = err.response?.data?.message || `Failed to ${actionType} administrator`
      toast.error(msg)
    } finally {
      setUpdatingStatus(false)
    }
  }

  // Filter list of admins
  const filteredAdmins = admins.filter((admin) => {
    const query = searchTerm.toLowerCase()
    return (
      admin.full_name.toLowerCase().includes(query) ||
      admin.email.toLowerCase().includes(query)
    )
  })

  return (
    <div className="space-y-6 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 flex items-center gap-2">
            <Shield className="h-8 w-8 text-teal-600" />
            Platform Administrators
          </h1>
          <p className="text-slate-500 mt-1">
            Manage administrative access accounts, toggle availability status, and review security audit trails.
          </p>
        </div>
        <Button
          onClick={() => setIsCreateModalOpen(true)}
          className="bg-teal-600 hover:bg-teal-700 text-white flex items-center gap-2 font-semibold shadow"
        >
          <UserPlus className="h-4 w-4" />
          Add Administrator
        </Button>
      </div>

      {/* Filter Row */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative w-full sm:w-96">
          <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Search admins by name or email..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 pr-4 py-2 border-slate-200 focus:ring-teal-500 focus:border-teal-500 rounded-lg shadow-sm"
          />
        </div>
        <div className="text-sm text-slate-500 font-medium">
          Showing {filteredAdmins.length} of {admins.length} administrators
        </div>
      </div>

      {/* Main Table Card */}
      <Card className="border-slate-200 shadow-md overflow-hidden rounded-xl bg-white">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">
                    Name / Email
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">
                    Date Created
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">
                    Last Login
                  </th>
                  <th className="px-6 py-4 text-right text-xs font-bold text-slate-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-slate-100">
                {loading ? (
                  Array.from({ length: 3 }).map((_, i) => (
                    <tr key={i} className="animate-pulse">
                      <td className="px-6 py-4">
                        <div className="h-4 bg-slate-200 rounded w-48 mb-2" />
                        <div className="h-3 bg-slate-100 rounded w-32" />
                      </td>
                      <td className="px-6 py-4">
                        <div className="h-6 bg-slate-200 rounded w-16" />
                      </td>
                      <td className="px-6 py-4">
                        <div className="h-4 bg-slate-200 rounded w-24" />
                      </td>
                      <td className="px-6 py-4">
                        <div className="h-4 bg-slate-200 rounded w-24" />
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="h-8 bg-slate-200 rounded w-20 ml-auto" />
                      </td>
                    </tr>
                  ))
                ) : filteredAdmins.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-12 text-center text-slate-400">
                      <Shield className="h-12 w-12 mx-auto text-slate-300 mb-3" />
                      <h3 className="font-semibold text-slate-700 text-lg">No administrators found</h3>
                      <p className="text-sm mt-1">Adjust search parameters or add a new administrator.</p>
                    </td>
                  </tr>
                ) : (
                  filteredAdmins.map((admin) => (
                    <tr
                      key={admin.id}
                      className="hover:bg-slate-50/80 transition-colors cursor-pointer group"
                      onClick={() => handleOpenDetail(admin.id)}
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-3">
                          <div className="h-10 w-10 rounded-full bg-teal-50 text-teal-600 font-bold flex items-center justify-center text-sm shadow-inner">
                            {admin.full_name.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <div className="text-sm font-semibold text-slate-800 group-hover:text-teal-600 transition-colors">
                              {admin.full_name}
                            </div>
                            <div className="text-xs text-slate-400 flex items-center gap-1 mt-0.5">
                              <Mail className="h-3.5 w-3.5" />
                              {admin.email}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {admin.is_active ? (
                          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            Active
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-red-50 text-red-700 border border-red-200">
                            Disabled
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3.5 w-3.5 text-slate-400" />
                          {new Date(admin.created_at).toLocaleDateString(undefined, {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric',
                          })}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                        <div className="flex items-center gap-1">
                          <Clock className="h-3.5 w-3.5 text-slate-400" />
                          {admin.last_login_at
                            ? new Date(admin.last_login_at).toLocaleString(undefined, {
                                dateStyle: 'short',
                                timeStyle: 'short',
                              })
                            : 'Never logged in'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div
                          className="flex items-center justify-end gap-2"
                          onClick={(e) => e.stopPropagation()} // Prevent opening details modal when toggle button clicked
                        >
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleOpenDetail(admin.id)}
                            className="text-slate-600 hover:text-teal-600 border-slate-200 text-xs py-1 px-2.5 h-8 font-semibold"
                          >
                            View
                          </Button>
                          {admin.is_active ? (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => openConfirmModal(admin, 'disable')}
                              className="text-red-600 hover:text-red-700 hover:bg-red-50/50 border-red-200 text-xs py-1 px-2.5 h-8 font-semibold"
                            >
                              Disable
                            </Button>
                          ) : (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => openConfirmModal(admin, 'enable')}
                              className="text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50/50 border-emerald-200 text-xs py-1 px-2.5 h-8 font-semibold"
                            >
                              Enable
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Admin Details Drawer/Modal */}
      <Dialog open={isDetailDrawerOpen} onOpenChange={setIsDetailDrawerOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto rounded-xl">
          <DialogHeader className="border-b pb-4">
            <DialogTitle className="flex items-center gap-2 text-xl font-bold">
              <Shield className="h-6 w-6 text-teal-600" />
              Administrator Details
            </DialogTitle>
          </DialogHeader>

          {loadingDetail || !adminDetail ? (
            <div className="py-20 flex justify-center items-center">
              <Loader2 className="h-10 w-10 text-teal-600 animate-spin" />
            </div>
          ) : (
            <div className="space-y-6 py-4">
              {/* Profile details grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 bg-slate-50 p-5 rounded-xl border border-slate-100 shadow-inner">
                <div className="space-y-3">
                  <div>
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Full Name</span>
                    <span className="text-base font-bold text-slate-800 flex items-center gap-1.5 mt-0.5">
                      <User className="h-4 w-4 text-slate-400" />
                      {adminDetail.profile.full_name}
                    </span>
                  </div>
                  <div>
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Email Address</span>
                    <span className="text-base font-semibold text-slate-800 flex items-center gap-1.5 mt-0.5">
                      <Mail className="h-4 w-4 text-slate-400" />
                      {adminDetail.profile.email}
                    </span>
                  </div>
                  <div>
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Authorization Provider</span>
                    <span className="text-sm font-semibold text-slate-700 capitalize mt-0.5 inline-block">
                      {adminDetail.profile.auth_provider}
                    </span>
                  </div>
                </div>
                <div className="space-y-3">
                  <div>
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Account Status</span>
                    <div className="mt-1 flex items-center gap-2">
                      {adminDetail.profile.is_active ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-50 text-red-700 border border-red-200">
                          Disabled
                        </span>
                      )}
                      {adminDetail.profile.email_verified ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200">
                          Verified
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-yellow-50 text-yellow-700 border border-yellow-200">
                          Unverified
                        </span>
                      )}
                    </div>
                  </div>
                  <div>
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Date Registered</span>
                    <span className="text-sm font-semibold text-slate-700 flex items-center gap-1.5 mt-0.5">
                      <Calendar className="h-4 w-4 text-slate-400" />
                      {new Date(adminDetail.profile.created_at).toLocaleString()}
                    </span>
                  </div>
                  <div>
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Last Active</span>
                    <span className="text-sm font-semibold text-slate-700 flex items-center gap-1.5 mt-0.5">
                      <Clock className="h-4 w-4 text-slate-400" />
                      {adminDetail.profile.last_login_at
                        ? new Date(adminDetail.profile.last_login_at).toLocaleString()
                        : 'Never'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Status Actions inside Detail View */}
              <div className="flex items-center justify-between border-t pt-4">
                <span className="text-sm text-slate-500 font-medium">Modify Access Privileges:</span>
                {adminDetail.profile.is_active ? (
                  <Button
                    onClick={() => openConfirmModal(adminDetail.profile, 'disable')}
                    className="bg-red-600 hover:bg-red-700 text-white font-semibold flex items-center gap-1.5"
                  >
                    <Power className="h-4 w-4" />
                    Disable Account
                  </Button>
                ) : (
                  <Button
                    onClick={() => openConfirmModal(adminDetail.profile, 'enable')}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold flex items-center gap-1.5"
                  >
                    <Power className="h-4 w-4" />
                    Enable Account
                  </Button>
                )}
              </div>

              {/* Audit Summary Events List */}
              <div className="border-t pt-4 space-y-3">
                <h4 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                  <Activity className="h-4 w-4 text-slate-500" />
                  Recent Audit Logs Summary
                </h4>
                <div className="max-h-60 overflow-y-auto border border-slate-200 rounded-lg divide-y divide-slate-100 bg-slate-50">
                  {adminDetail.audit_summary.length === 0 ? (
                    <div className="py-6 text-center text-slate-400 text-sm">
                      No audited history events logged for this user.
                    </div>
                  ) : (
                    adminDetail.audit_summary.map((log: AuditLog) => (
                      <div key={log.id} className="p-3 text-xs space-y-1 bg-white hover:bg-slate-50">
                        <div className="flex justify-between items-center">
                          <span className="font-bold text-teal-700 bg-teal-50 border border-teal-100 rounded px-1.5 py-0.5">
                            {log.action}
                          </span>
                          <span className="text-slate-400">
                            {new Date(log.created_at).toLocaleString()}
                          </span>
                        </div>
                        <div className="text-slate-600 flex flex-wrap gap-x-3 gap-y-0.5 font-medium mt-1">
                          <span>
                            Resource: <strong className="text-slate-800">{log.resource_type}</strong> ({log.resource_id})
                          </span>
                          {log.ip_address && (
                            <span>
                              IP: <strong className="text-slate-800">{log.ip_address}</strong>
                            </span>
                          )}
                        </div>
                        {log.new_value && (
                          <div className="bg-slate-50 p-1.5 rounded text-[10px] text-slate-500 border border-slate-100 mt-1 max-h-16 overflow-y-auto">
                            Details: {JSON.stringify(log.new_value)}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}

          <DialogFooter className="border-t pt-4">
            <Button
              onClick={() => setIsDetailDrawerOpen(false)}
              className="bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200 font-semibold px-4 h-10 w-full sm:w-auto"
            >
              Close Details
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Administrator Modal */}
      <Dialog open={isCreateModalOpen} onOpenChange={setIsCreateModalOpen}>
        <DialogContent className="max-w-md rounded-xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 font-bold text-xl">
              <UserPlus className="h-6 w-6 text-teal-600" />
              Create Administrator
            </DialogTitle>
            <DialogDescription>
              Submit details to provision a new administrative staff account.
            </DialogDescription>
          </DialogHeader>

          {tempPassword ? (
            // Display Temporary Password Screen
            <div className="py-4 space-y-4">
              <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-5 text-center space-y-3">
                <div className="mx-auto w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center text-emerald-600">
                  <Lock className="h-6 w-6" />
                </div>
                <h4 className="font-bold text-slate-800">Account Provisioned successfully!</h4>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Provide the temporary password below to the user. They must use this to complete their first authentication login.
                </p>
                <div className="bg-white border border-slate-200 rounded-lg p-3 font-mono text-lg font-bold tracking-wider text-slate-800 select-all relative flex items-center justify-between shadow-inner">
                  <span>{tempPassword}</span>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={copyToClipboard}
                    className="text-teal-600 hover:text-teal-700 p-2"
                  >
                    {copied ? <Check className="h-5 w-5 text-emerald-600" /> : <Copy className="h-5 w-5" />}
                  </Button>
                </div>
              </div>
              <Button
                onClick={closeCreateModal}
                className="w-full bg-teal-600 hover:bg-teal-700 text-white font-bold h-11 rounded-lg"
              >
                Done
              </Button>
            </div>
          ) : (
            // Create Admin Form
            <form onSubmit={handleCreateAdmin} className="space-y-4 py-2">
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block">Full Name</label>
                <Input
                  required
                  placeholder="Enter administrator full name..."
                  value={createName}
                  onChange={(e) => setCreateName(e.target.value)}
                  className="border-slate-200 focus:ring-teal-500 focus:border-teal-500 rounded-lg shadow-sm"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block">Email Address</label>
                <Input
                  required
                  type="email"
                  placeholder="Enter administrator email..."
                  value={createEmail}
                  onChange={(e) => setCreateEmail(e.target.value)}
                  className="border-slate-200 focus:ring-teal-500 focus:border-teal-500 rounded-lg shadow-sm"
                />
              </div>
              <DialogFooter className="pt-4 border-t gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={closeCreateModal}
                  className="border-slate-200 text-slate-700 font-semibold h-10 w-full sm:w-auto"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={creating}
                  className="bg-teal-600 hover:bg-teal-700 text-white font-semibold h-10 w-full sm:w-auto flex items-center justify-center gap-1.5"
                >
                  {creating && <Loader2 className="h-4 w-4 animate-spin" />}
                  Create Account
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>

      {/* Status Toggle Confirmation Modal */}
      <Dialog open={confirmModalOpen} onOpenChange={setConfirmModalOpen}>
        <DialogContent className="max-w-md rounded-xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 font-bold text-xl">
              <AlertTriangle className={actionType === 'disable' ? 'text-red-500 h-6 w-6' : 'text-emerald-500 h-6 w-6'} />
              Confirm Administrator Status Update
            </DialogTitle>
          </DialogHeader>

          {adminToUpdate && (
            <div className="py-2 space-y-3">
              <p className="text-sm text-slate-600 leading-relaxed">
                Are you sure you want to <strong className="text-slate-800">{actionType}</strong> the administrative account for{' '}
                <strong className="text-slate-800">{adminToUpdate.full_name} ({adminToUpdate.email})</strong>?
              </p>
              {actionType === 'disable' && (
                <div className="bg-red-50 border border-red-200/60 rounded-lg p-3 text-xs text-red-700 flex items-start gap-2">
                  <AlertTriangle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold">Important Safeguard Note:</span> Disabling this administrator will revoke all system dashboard privileges immediately. The lockout safety constraint strictly prevents disabling the last active administrator in the system.
                  </div>
                </div>
              )}
            </div>
          )}

          <DialogFooter className="pt-4 border-t gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setConfirmModalOpen(false)}
              className="border-slate-200 text-slate-700 font-semibold h-10 w-full sm:w-auto"
            >
              Cancel
            </Button>
            <Button
              type="button"
              disabled={updatingStatus}
              onClick={handleToggleStatus}
              className={
                actionType === 'disable'
                  ? 'bg-red-600 hover:bg-red-700 text-white font-semibold h-10 w-full sm:w-auto flex items-center justify-center gap-1.5'
                  : 'bg-emerald-600 hover:bg-emerald-700 text-white font-semibold h-10 w-full sm:w-auto flex items-center justify-center gap-1.5'
              }
            >
              {updatingStatus && <Loader2 className="h-4 w-4 animate-spin" />}
              Yes, Confirm
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
