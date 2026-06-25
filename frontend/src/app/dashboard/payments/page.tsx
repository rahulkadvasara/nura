'use client'

import { useState } from 'react'
import { Calendar, Search, Stethoscope, AlertCircle, FileText, ChevronLeft, ChevronRight } from 'lucide-react'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { usePaymentHistory } from '@/hooks/use-payment-admin'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'

type StatusType = 'all' | 'success' | 'pending' | 'failed'

interface ReceiptInfo {
  transactionId: string
  doctorShare: number
  platformFee: number
  totalAmount: number
  doctorName: string
  date: string
  time: string
}

function PatientPaymentsContent() {
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<StatusType>('all')
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 8

  const [receiptDetails, setReceiptDetails] = useState<ReceiptInfo | null>(null)

  const queryParams = {
    search: search.trim() || undefined,
    status_filter: status === 'all' ? undefined : status,
    limit: itemsPerPage,
    skip: (currentPage - 1) * itemsPerPage,
  }

  const { data, isLoading, isError, error, refetch } = usePaymentHistory(queryParams)

  const payments = data?.payments || []
  const totalItems = data?.total || 0
  const totalPages = Math.ceil(totalItems / itemsPerPage) || 1

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value)
    setCurrentPage(1)
  }

  const handleStatusChange = (newStatus: StatusType) => {
    setStatus(newStatus)
    setCurrentPage(1)
  }

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage)
    }
  }

  const handleViewReceipt = (payment: any) => {
    const receiptInfo = payment.receipt_information || {}
    const totalAmount = payment.amount || 0
    const doctorShare = receiptInfo.doctor_share || (totalAmount * 0.85)
    const platformFee = receiptInfo.platform_fee || (totalAmount * 0.15)
    const timeStr = payment.appointment?.slot_time || 'N/A'

    setReceiptDetails({
      transactionId: receiptInfo.razorpay_payment_id || receiptInfo.transaction_reference || 'N/A',
      doctorShare,
      platformFee,
      totalAmount,
      doctorName: payment.doctor?.full_name || 'Doctor',
      date: payment.appointment?.slot_date || 'N/A',
      time: timeStr,
    })
  }

  const getStatusBadge = (paymentStatus: string) => {
    const s = paymentStatus.toLowerCase()
    if (s === 'success' || s === 'paid' || s === 'completed') {
      return <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200 font-semibold">Success</Badge>
    } else if (s === 'failed') {
      return <Badge className="bg-rose-50 text-rose-700 border-rose-250 font-semibold">Failed</Badge>
    } else {
      return <Badge className="bg-amber-50 text-amber-700 border-amber-200 font-semibold">Pending</Badge>
    }
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto px-4 sm:px-6 py-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Payment History</h1>
        <p className="text-slate-500 mt-1">Review all your processed transaction history and access receipts.</p>
      </div>

      {/* Filters Panel */}
      <div className="flex flex-col md:flex-row gap-4 justify-between items-stretch md:items-center bg-white p-4 border border-slate-200 rounded-2xl shadow-sm">
        {/* Search */}
        <div className="relative flex-grow max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            value={search}
            onChange={handleSearchChange}
            placeholder="Search by doctor name..."
            className="pl-10 pr-4 h-10 border-slate-200 rounded-xl"
          />
        </div>

        {/* Status Buttons */}
        <div className="flex flex-wrap gap-1.5 p-0.5 bg-slate-50 rounded-xl border border-slate-100 w-fit">
          {(['all', 'success', 'pending', 'failed'] as StatusType[]).map((s) => (
            <button
              key={s}
              onClick={() => handleStatusChange(s)}
              className={`px-4 py-1.5 text-xs font-semibold rounded-lg capitalize transition-colors ${
                status === s
                  ? 'bg-white text-teal-650 shadow-sm border border-slate-100'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-24 bg-white border border-slate-100 rounded-2xl animate-pulse" />
          ))}
        </div>
      )}

      {/* Error State */}
      {isError && (
        <div className="flex flex-col items-center justify-center py-12 text-center bg-white border border-slate-200 rounded-2xl">
          <div className="p-3 rounded-full bg-rose-50 mb-3 text-rose-500">
            <AlertCircle className="h-6 w-6" />
          </div>
          <h3 className="text-base font-semibold text-slate-800 mb-1">Failed to retrieve payments</h3>
          <p className="text-xs text-slate-500 mb-4 max-w-sm">
            {error?.message || 'We ran into an issue loading your payment logs.'}
          </p>
          <Button onClick={() => refetch()} variant="outline" size="sm" className="rounded-xl">
            Retry
          </Button>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !isError && payments.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center bg-white border border-dashed rounded-2xl p-6">
          <div className="p-4 rounded-full bg-slate-50 mb-3 text-slate-400 border border-slate-100">
            <FileText className="h-6 w-6" />
          </div>
          <h3 className="text-base font-semibold text-slate-805 mb-1 font-bold font-semibold text-slate-800">No transactions found</h3>
          <p className="text-xs text-slate-500 max-w-xs">
            {status !== 'all' || search
              ? 'No transactions matched your search filters.'
              : 'You have not made any consultations payments on the platform yet.'}
          </p>
        </div>
      )}

      {/* Payments History List */}
      {!isLoading && !isError && payments.length > 0 && (
        <div className="space-y-3">
          {payments.map((p: any) => {
            const isSuccess = p.status?.toLowerCase() === 'success' || p.status?.toLowerCase() === 'paid' || p.status?.toLowerCase() === 'completed'
            return (
              <Card key={p.payment_id} className="border-slate-200 hover:shadow-sm transition-shadow bg-white overflow-hidden rounded-2xl">
                <CardContent className="p-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                  <div className="space-y-1.5 flex-grow">
                    <div className="flex flex-wrap items-center gap-2">
                      <Stethoscope className="h-4 w-4 text-teal-600 shrink-0" />
                      <h3 className="font-bold text-slate-900 text-sm sm:text-base">
                        {p.doctor?.full_name?.toLowerCase().startsWith('dr.') ? p.doctor.full_name : `Dr. ${p.doctor?.full_name}`}
                      </h3>
                      <span className="text-xs text-slate-300">•</span>
                      <span className="text-xs text-slate-500 font-medium">{p.doctor?.specialization}</span>
                    </div>

                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-slate-500 font-medium">
                      <div className="flex items-center gap-1.5">
                        <Calendar className="h-3.5 w-3.5 text-slate-400" />
                        <span>
                          {p.appointment?.slot_date || 'N/A'} at {p.appointment?.slot_time || 'N/A'}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-slate-300">•</span>
                        <span>Paid: </span>
                        <span className="font-bold text-slate-900">INR {p.amount.toFixed(2)}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        {getStatusBadge(p.status)}
                      </div>
                    </div>

                    {/* Meta info */}
                    <div className="flex flex-col gap-1 text-[10px] text-slate-450 pt-1">
                      <div>Payment Order ID: <span className="font-mono text-slate-500">{p.receipt_information?.razorpay_order_id || 'N/A'}</span></div>
                      {p.receipt_information?.razorpay_payment_id && (
                        <div>Transaction Reference: <span className="font-mono text-slate-500">{p.receipt_information.razorpay_payment_id}</span></div>
                      )}
                    </div>
                  </div>

                  {isSuccess && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleViewReceipt(p)}
                      className="border-teal-200 text-teal-600 hover:bg-teal-50 hover:text-teal-700 hover:border-teal-300 text-xs shrink-0 flex items-center gap-1.5 h-9 px-3 rounded-lg font-semibold"
                    >
                      <FileText className="h-3.5 w-3.5" />
                      View Receipt
                    </Button>
                  )}
                </CardContent>
              </Card>
            )
          })}

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-slate-200 pt-4 px-1">
              <p className="text-xs text-slate-500 font-medium">
                Showing Page <span className="font-semibold text-slate-800">{currentPage}</span> of{' '}
                <span className="font-semibold text-slate-800">{totalPages}</span>
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="h-8 w-8 p-0 rounded-lg border-slate-200"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className="h-8 w-8 p-0 rounded-lg border-slate-200"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Receipt Modal (reused) */}
      <Dialog open={!!receiptDetails} onOpenChange={(open) => !open && setReceiptDetails(null)}>
        <DialogContent className="max-w-md bg-white border border-slate-200 rounded-2xl shadow-2xl p-6">
          <DialogHeader className="text-center flex flex-col items-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-emerald-600 mb-2">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <DialogTitle className="text-xl font-extrabold text-slate-900 tracking-tight">Payment Receipt</DialogTitle>
            <DialogDescription className="text-slate-500 text-xs">
              Your payment was verified successfully and split securely.
            </DialogDescription>
          </DialogHeader>

          {receiptDetails && (
            <div className="mt-4 space-y-4">
              {/* Receipt metadata box */}
              <div className="bg-slate-50 border border-slate-100 rounded-xl p-4 space-y-3">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-slate-400 font-medium">Transaction ID</span>
                  <span className="font-mono text-slate-800 font-semibold select-all bg-white border border-slate-100 px-2 py-0.5 rounded">
                    {receiptDetails.transactionId}
                  </span>
                </div>

                <div className="flex justify-between items-center text-xs">
                  <span className="text-slate-400 font-medium">Doctor</span>
                  <span className="text-slate-800 font-semibold">
                    {receiptDetails.doctorName.toLowerCase().startsWith('dr.') ? receiptDetails.doctorName : `Dr. ${receiptDetails.doctorName}`}
                  </span>
                </div>

                <div className="flex justify-between items-center text-xs">
                  <span className="text-slate-400 font-medium">Date & Time</span>
                  <span className="text-slate-800 font-semibold">
                    {receiptDetails.date} at {receiptDetails.time}
                  </span>
                </div>
              </div>

              {/* Price Breakdown splits */}
              <div className="space-y-2 px-1">
                <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Revenue Breakdown</h4>
                
                <div className="flex justify-between items-center text-sm py-1">
                  <span className="text-slate-600 font-medium">Consultation Fee</span>
                  <span className="text-slate-900 font-semibold">INR {receiptDetails.totalAmount.toFixed(2)}</span>
                </div>

                <div className="flex justify-between items-center text-xs text-slate-500 py-0.5 border-t border-slate-100/50 pt-2">
                  <span className="flex items-center gap-1.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-teal-500"></span>
                    Doctor Share (85%)
                  </span>
                  <span className="font-medium text-slate-700">INR {receiptDetails.doctorShare.toFixed(2)}</span>
                </div>

                <div className="flex justify-between items-center text-xs text-slate-500 py-0.5">
                  <span className="flex items-center gap-1.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-slate-400"></span>
                    Platform Fee (15%)
                  </span>
                  <span className="font-medium text-slate-700">INR {receiptDetails.platformFee.toFixed(2)}</span>
                </div>
              </div>

              {/* Receipt tear cut look line */}
              <div className="relative flex py-2 items-center">
                <div className="flex-grow border-t border-dashed border-slate-200"></div>
              </div>

              {/* Grand Total */}
              <div className="flex justify-between items-center bg-teal-50 border border-teal-100/30 rounded-xl px-4 py-3">
                <span className="text-sm font-bold text-teal-900">Total Paid</span>
                <span className="text-base font-extrabold text-teal-700">INR {receiptDetails.totalAmount.toFixed(2)}</span>
              </div>

              {/* Razorpay Safe badge */}
              <div className="flex items-center justify-center gap-1 text-[10px] text-slate-400 font-semibold pt-1">
                <svg className="h-3.5 w-3.5 text-emerald-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                Verified secure payment by Razorpay
              </div>
            </div>
          )}

          <DialogFooter className="mt-6">
            <Button
              onClick={() => setReceiptDetails(null)}
              className="w-full bg-teal-600 hover:bg-teal-700 text-white rounded-xl py-2 font-bold text-xs shadow"
            >
              Close Receipt
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default function PatientPaymentsPage() {
  return (
    <ProtectedRoute allowedRoles={['patient']}>
      <PatientPaymentsContent />
    </ProtectedRoute>
  )
}
