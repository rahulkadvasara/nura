'use client'

import { useState, useEffect } from 'react'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { adminUserService } from '@/services/admin-user.service'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import { toast } from 'react-hot-toast'
import {
  Users,
  Search,
  User as UserIcon,
  Mail,
  Calendar,
  Shield,
  Power,
  AlertTriangle,
  Loader2,
  X,
  CheckCircle2,
  XCircle,
  Clock,
  Filter,
} from 'lucide-react'
import { User } from '@/types'

export default function AdminUsersPage() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <AdminUsersContent />
    </ProtectedRoute>
  )
}

function AdminUsersContent() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')

  // Selected User Detail
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [isDetailDrawerOpen, setIsDetailDrawerOpen] = useState(false)
  const [loadingDetail, setLoadingDetail] = useState(false)

  // Status Action (Activate/Suspend) Modal
  const [confirmModalOpen, setConfirmModalOpen] = useState(false)
  const [actionType, setActionType] = useState<'activate' | 'suspend'>('suspend')
  const [userToUpdate, setUserToUpdate] = useState<User | null>(null)
  const [updatingStatus, setUpdatingStatus] = useState(false)

  const fetchUsers = async () => {
    try {
      setLoading(true)
      const roleParam = roleFilter === 'all' ? undefined : roleFilter
      const activeParam =
        statusFilter === 'all'
          ? undefined
          : statusFilter === 'active'
          ? true
          : false

      const res = await adminUserService.listUsers(
        search || undefined,
        roleParam,
        activeParam
      )
      if (res.success && res.data) {
        setUsers(res.data)
      } else {
        toast.error(res.message || 'Failed to fetch users')
      }
    } catch (err) {
      console.error(err)
      toast.error('An error occurred while fetching users')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      fetchUsers()
    }, 300)

    return () => clearTimeout(delayDebounceFn)
  }, [search, roleFilter, statusFilter])

  const handleOpenDetail = async (userId: string) => {
    try {
      setLoadingDetail(true)
      setIsDetailDrawerOpen(true)
      const res = await adminUserService.getUserDetail(userId)
      if (res.success && res.data) {
        setSelectedUser(res.data)
      } else {
        toast.error(res.message || 'Failed to fetch user details')
        setIsDetailDrawerOpen(false)
      }
    } catch (err) {
      console.error(err)
      toast.error('Failed to load user details')
      setIsDetailDrawerOpen(false)
    } finally {
      setLoadingDetail(false)
    }
  }

  const handleOpenConfirmModal = (user: User, action: 'activate' | 'suspend') => {
    setUserToUpdate(user)
    setActionType(action)
    setConfirmModalOpen(true)
  }

  const handleUpdateStatus = async () => {
    if (!userToUpdate) return

    try {
      setUpdatingStatus(true)
      let res
      if (actionType === 'activate') {
        res = await adminUserService.activateUser(userToUpdate.id)
      } else {
        res = await adminUserService.suspendUser(userToUpdate.id)
      }

      if (res.success) {
        toast.success(res.message || `User successfully ${actionType}d`)
        setConfirmModalOpen(false)
        fetchUsers()
        if (selectedUser?.id === userToUpdate.id) {
          // Refresh detail drawer if open
          handleOpenDetail(userToUpdate.id)
        }
      } else {
        toast.error(res.message || `Failed to ${actionType} user`)
      }
    } catch (err: any) {
      console.error(err)
      const errorMsg = err.response?.data?.detail || `An error occurred while updating status`
      toast.error(errorMsg)
    } finally {
      setUpdatingStatus(false)
    }
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">User Operations</h1>
          <p className="mt-2 text-sm text-slate-500">
            Manage platform users, verify their information, and activate or suspend their access.
          </p>
        </div>
      </div>

      {/* Filters & Search */}
      <Card className="border-slate-200 shadow-sm bg-white/50 backdrop-blur-sm">
        <CardContent className="p-4 sm:p-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* Search Input */}
            <div className="relative">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Search name or email..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 bg-slate-50 border-slate-200 focus:bg-white transition-colors"
              />
            </div>

            {/* Role Filter */}
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-slate-400 flex-shrink-0" />
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                className="w-full h-10 px-3 border border-slate-200 bg-slate-50 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:bg-white transition-colors"
              >
                <option value="all">All Roles</option>
                <option value="patient">Patient</option>
                <option value="doctor">Doctor</option>
                <option value="admin">Administrator</option>
              </select>
            </div>

            {/* Status Filter */}
            <div className="flex items-center gap-2">
              <Power className="h-4 w-4 text-slate-400 flex-shrink-0" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full h-10 px-3 border border-slate-200 bg-slate-50 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:bg-white transition-colors"
              >
                <option value="all">All Statuses</option>
                <option value="active">Active</option>
                <option value="suspended">Suspended</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card className="border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  User Info
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Role
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Verification
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Status
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Joined Date
                </th>
                <th scope="col" className="relative px-6 py-3">
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-200">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-10 text-center text-slate-500">
                    <div className="flex justify-center items-center gap-2">
                      <Loader2 className="h-5 w-5 animate-spin text-teal-600" />
                      <span>Loading platform users...</span>
                    </div>
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-10 text-center text-slate-500">
                    No users found matching current filters.
                  </td>
                </tr>
              ) : (
                users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50/50 transition-colors">
                    {/* User Info */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="h-10 w-10 flex-shrink-0 rounded-full bg-teal-50 flex items-center justify-center border border-teal-100 text-teal-700 font-bold">
                          {u.full_name ? u.full_name.charAt(0).toUpperCase() : 'U'}
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-semibold text-slate-900 hover:text-teal-600 cursor-pointer" onClick={() => handleOpenDetail(u.id)}>
                            {u.full_name}
                          </div>
                          <div className="text-sm text-slate-500">{u.email}</div>
                        </div>
                      </div>
                    </td>

                    {/* Role */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                          u.role === 'admin'
                            ? 'bg-purple-100 text-purple-800 border border-purple-200'
                            : u.role === 'doctor'
                            ? 'bg-blue-100 text-blue-800 border border-blue-200'
                            : 'bg-slate-100 text-slate-800 border border-slate-200'
                        }`}
                      >
                        {u.role.charAt(0).toUpperCase() + u.role.slice(1)}
                      </span>
                    </td>

                    {/* Email Verification */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      {u.email_verified ? (
                        <span className="inline-flex items-center gap-1 text-emerald-700 text-sm font-medium">
                          <CheckCircle2 className="h-4 w-4 text-emerald-500" /> Verified
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-slate-400 text-sm font-medium">
                          <XCircle className="h-4 w-4 text-slate-300" /> Unverified
                        </span>
                      )}
                    </td>

                    {/* Status */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      {u.is_active ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-800 border border-rose-200 animate-pulse">
                          Suspended
                        </span>
                      )}
                    </td>

                    {/* Joined Date */}
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                      {new Date(u.created_at).toLocaleDateString(undefined, {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                      })}
                    </td>

                    {/* Action buttons */}
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleOpenDetail(u.id)}
                        className="text-slate-600 hover:text-slate-900"
                      >
                        View Profile
                      </Button>

                      {u.is_active ? (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleOpenConfirmModal(u, 'suspend')}
                          className="text-rose-600 hover:text-rose-900 hover:bg-rose-50"
                        >
                          Suspend
                        </Button>
                      ) : (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleOpenConfirmModal(u, 'activate')}
                          className="text-emerald-600 hover:text-emerald-900 hover:bg-emerald-50"
                        >
                          Activate
                        </Button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* User Details Slide-over / Drawer */}
      {isDetailDrawerOpen && (
        <div className="fixed inset-0 overflow-hidden z-50">
          <div className="absolute inset-0 overflow-hidden">
            {/* Backdrop */}
            <div
              className="absolute inset-0 bg-slate-950/40 backdrop-blur-sm transition-opacity"
              onClick={() => setIsDetailDrawerOpen(false)}
            />

            <div className="pointer-events-none fixed inset-y-0 right-0 flex max-w-full pl-10">
              <div className="pointer-events-auto w-screen max-w-md transform bg-white shadow-2xl transition-all">
                <div className="flex h-full flex-col overflow-y-scroll py-6 shadow-xl">
                  {/* Drawer Header */}
                  <div className="px-4 sm:px-6 flex items-start justify-between border-b border-slate-100 pb-5">
                    <div>
                      <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                        <Users className="h-5 w-5 text-teal-600" />
                        <span>User Profile Information</span>
                      </h2>
                      <p className="mt-1 text-xs text-slate-500">ID: {selectedUser?.id}</p>
                    </div>
                    <button
                      type="button"
                      className="rounded-md text-slate-400 hover:text-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500"
                      onClick={() => setIsDetailDrawerOpen(false)}
                    >
                      <X className="h-6 w-6" />
                    </button>
                  </div>

                  {/* Drawer Content */}
                  <div className="relative flex-1 px-4 sm:px-6 py-6">
                    {loadingDetail ? (
                      <div className="flex justify-center items-center py-20">
                        <Loader2 className="h-8 w-8 animate-spin text-teal-600" />
                      </div>
                    ) : selectedUser ? (
                      <div className="space-y-6">
                        {/* Summary Card */}
                        <div className="flex flex-col items-center p-6 bg-slate-55 bg-gradient-to-br from-slate-50 to-slate-100/50 rounded-2xl border border-slate-200/60">
                          <div className="h-16 w-16 rounded-full bg-teal-600 text-white flex items-center justify-center font-bold text-2xl shadow-md">
                            {selectedUser.full_name ? selectedUser.full_name.charAt(0).toUpperCase() : 'U'}
                          </div>
                          <h3 className="mt-3 text-lg font-bold text-slate-900">{selectedUser.full_name}</h3>
                          <p className="text-sm text-slate-500">{selectedUser.email}</p>
                          <div className="mt-4 flex gap-2">
                            <span
                              className={`inline-flex px-3 py-1 rounded-full text-xs font-semibold ${
                                selectedUser.role === 'admin'
                                  ? 'bg-purple-100 text-purple-800 border border-purple-200'
                                  : selectedUser.role === 'doctor'
                                  ? 'bg-blue-100 text-blue-800 border border-blue-200'
                                  : 'bg-slate-100 text-slate-800 border border-slate-200'
                              }`}
                            >
                              {selectedUser.role.toUpperCase()}
                            </span>
                            <span
                              className={`inline-flex px-3 py-1 rounded-full text-xs font-semibold ${
                                selectedUser.is_active
                                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                                  : 'bg-rose-100 text-rose-800 border border-rose-200'
                              }`}
                            >
                              {selectedUser.is_active ? 'ACTIVE' : 'SUSPENDED'}
                            </span>
                          </div>
                        </div>

                        {/* Details Sections */}
                        <div className="space-y-4">
                          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Account Details</h4>

                          <div className="grid grid-cols-1 gap-4 bg-slate-50/50 p-4 rounded-xl border border-slate-100">
                            {/* Email */}
                            <div className="flex items-start gap-3">
                              <Mail className="h-4 w-4 text-slate-400 mt-1" />
                              <div>
                                <p className="text-xs text-slate-400 font-medium">Email Address</p>
                                <p className="text-sm font-semibold text-slate-955">{selectedUser.email}</p>
                              </div>
                            </div>

                            {/* Verification */}
                            <div className="flex items-start gap-3 border-t border-slate-100 pt-3">
                              <Shield className="h-4 w-4 text-slate-400 mt-1" />
                              <div>
                                <p className="text-xs text-slate-400 font-medium">Verification Status</p>
                                <p className={`text-sm font-semibold ${selectedUser.email_verified ? 'text-emerald-700' : 'text-slate-500'}`}>
                                  {selectedUser.email_verified ? 'Email Verified' : 'Email Unverified'}
                                </p>
                              </div>
                            </div>

                            {/* Auth Provider */}
                            <div className="flex items-start gap-3 border-t border-slate-100 pt-3">
                              <Clock className="h-4 w-4 text-slate-400 mt-1" />
                              <div>
                                <p className="text-xs text-slate-400 font-medium">Auth Provider</p>
                                <p className="text-sm font-semibold text-slate-800 uppercase">{selectedUser.auth_provider}</p>
                              </div>
                            </div>

                            {/* Joined */}
                            <div className="flex items-start gap-3 border-t border-slate-100 pt-3">
                              <Calendar className="h-4 w-4 text-slate-400 mt-1" />
                              <div>
                                <p className="text-xs text-slate-400 font-medium">Joined Date</p>
                                <p className="text-sm font-semibold text-slate-800">
                                  {new Date(selectedUser.created_at).toLocaleString()}
                                </p>
                              </div>
                            </div>

                            {/* Last Login */}
                            <div className="flex items-start gap-3 border-t border-slate-100 pt-3">
                              <Clock className="h-4 w-4 text-slate-400 mt-1" />
                              <div>
                                <p className="text-xs text-slate-400 font-medium">Last Login</p>
                                <p className="text-sm font-semibold text-slate-800">
                                  {selectedUser.last_login_at
                                    ? new Date(selectedUser.last_login_at).toLocaleString()
                                    : 'Never logged in'}
                                </p>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Action buttons */}
                        <div className="pt-6 border-t border-slate-100 flex gap-3">
                          {selectedUser.is_active ? (
                            <Button
                              variant="destructive"
                              className="w-full flex items-center justify-center gap-2"
                              onClick={() => handleOpenConfirmModal(selectedUser, 'suspend')}
                            >
                              <Power className="h-4 w-4" />
                              <span>Suspend Account</span>
                            </Button>
                          ) : (
                            <Button
                              variant="default"
                              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white flex items-center justify-center gap-2 border-0"
                              onClick={() => handleOpenConfirmModal(selectedUser, 'activate')}
                            >
                              <Power className="h-4 w-4" />
                              <span>Activate Account</span>
                            </Button>
                          )}
                        </div>
                      </div>
                    ) : (
                      <p className="text-center text-slate-500">Failed to load details.</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Modal */}
      <Dialog open={confirmModalOpen} onOpenChange={setConfirmModalOpen}>
        <DialogContent className="sm:max-w-md bg-white border border-slate-200">
          <DialogHeader>
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-rose-50 border border-rose-100 text-rose-600 mb-4">
              <AlertTriangle className="h-6 w-6" />
            </div>
            <DialogTitle className="text-center text-lg font-bold text-slate-900">
              Confirm Account {actionType === 'activate' ? 'Activation' : 'Suspension'}
            </DialogTitle>
            <DialogDescription className="text-center text-sm text-slate-500 mt-2">
              Are you sure you want to {actionType} the account for{' '}
              <span className="font-bold text-slate-800">{userToUpdate?.full_name}</span> ({userToUpdate?.email})?
              {actionType === 'suspend' && (
                <span className="block mt-2 font-semibold text-rose-600">
                  Warning: Suspending this user will immediately revoke all of their active sessions and prevent them from logging in.
                </span>
              )}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="sm:justify-center gap-2 mt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => setConfirmModalOpen(false)}
              className="border-slate-200 text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant={actionType === 'activate' ? 'default' : 'destructive'}
              className={actionType === 'activate' ? 'bg-emerald-600 hover:bg-emerald-700 text-white border-0' : ''}
              onClick={handleUpdateStatus}
              disabled={updatingStatus}
            >
              {updatingStatus ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  <span>Processing...</span>
                </>
              ) : (
                <span>Confirm {actionType.charAt(0).toUpperCase() + actionType.slice(1)}</span>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
