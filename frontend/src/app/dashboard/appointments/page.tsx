'use client'

import { useState } from 'react'
import { Calendar, Clock, Stethoscope, AlertCircle, XCircle } from 'lucide-react'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { useAppointments, useCancelAppointment } from '@/hooks/use-appointments'
import { toast } from 'sonner'
import { useCreatePaymentOrder, useVerifyPayment, useFailPayment, useCancelPayment } from '@/hooks/use-payment'
import { useAuthStore } from '@/stores/auth'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'

type TabType = 'approved' | 'pending' | 'cancelled'

interface ReceiptInfo {
  transactionId: string
  doctorShare: number
  platformFee: number
  totalAmount: number
  doctorName: string
  date: string
  time: string
}

const loadRazorpayScript = () => {
  return new Promise((resolve) => {
    if (typeof window !== 'undefined' && (window as any).Razorpay) {
      resolve(true)
      return
    }
    const script = document.createElement('script')
    script.src = 'https://checkout.razorpay.com/v1/checkout.js'
    script.onload = () => resolve(true)
    script.onerror = () => resolve(false)
    document.body.appendChild(script)
  })
}

function AppointmentsContent() {
  const [activeTab, setActiveTab] = useState<TabType>('pending')
  const { data: appointments = [], isLoading, isError, error, refetch } = useAppointments()
  const { mutateAsync: cancelAppointment, isPending: isCancelling } = useCancelAppointment()
  const [selectedCancelId, setSelectedCancelId] = useState<string | null>(null)

  const { mutateAsync: createPaymentOrder } = useCreatePaymentOrder()
  const { mutateAsync: verifyPayment } = useVerifyPayment()
  const { mutateAsync: failPayment } = useFailPayment()
  const { mutateAsync: cancelPayment } = useCancelPayment()
  const { user } = useAuthStore()
  
  const [payingId, setPayingId] = useState<string | null>(null)
  const [receiptDetails, setReceiptDetails] = useState<ReceiptInfo | null>(null)

  const handlePayNow = async (appt: any) => {
    try {
      setPayingId(appt.id)
      
      const loaded = await loadRazorpayScript()
      if (!loaded) {
        throw new Error('Razorpay SDK failed to load. Please check your internet connection.')
      }

      const res = await createPaymentOrder(appt.id)

      const options = {
        key: res.razorpay_key_id,
        amount: res.amount * 100, // paise
        currency: res.currency,
        name: 'Nura Healthcare',
        description: `Consultation fee for Dr. ${appt.doctor_name}`,
        order_id: res.razorpay_order_id,
        handler: async function (response: any) {
          console.log('Razorpay callback payload captured:', response)
          
          const verifyPromise = verifyPayment({
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_order_id: response.razorpay_order_id,
            razorpay_signature: response.razorpay_signature,
          })

          toast.promise(verifyPromise, {
            loading: 'Verifying payment details securely...',
            success: (data) => {
              // Set receipt details from response
              if (data && data.revenue_split_summary) {
                setReceiptDetails({
                  transactionId: response.razorpay_payment_id,
                  doctorShare: data.revenue_split_summary.doctor_share,
                  platformFee: data.revenue_split_summary.platform_share,
                  totalAmount: data.revenue_split_summary.amount,
                  doctorName: appt.doctor_name,
                  date: appt.appointment_date,
                  time: appt.appointment_time,
                })
              }
              refetch()
              return 'Payment verified and appointment confirmed!'
            },
            error: (err) => {
              console.error('Verification failed:', err)
              return err.message || 'Payment verification failed. Please contact support.'
            }
          })
        },
        prefill: {
          name: user?.full_name || '',
          email: user?.email || '',
          contact: user?.phone || '',
        },
        theme: {
          color: '#0d9488',
        },
        modal: {
          ondismiss: async () => {
            try {
              await cancelPayment(res.payment_id)
              toast.error('Payment checkout closed. Order cancelled.')
              refetch()
            } catch (err) {
              console.error('Cancel payment error:', err)
            }
          }
        }
      }

      const rzp = new (window as any).Razorpay(options)
      rzp.on('payment.failed', async function (response: any) {
        console.error('Razorpay payment failed callback:', response)
        try {
          await failPayment({
            paymentId: res.payment_id,
            errorDetails: response.error,
          })
          toast.error(`Checkout payment failed: ${response.error.description || 'Gateway error'}`)
          refetch()
        } catch (err) {
          console.error('Fail payment error:', err)
        }
      })
      rzp.open()

    } catch (err: any) {
      console.error('Payment error:', err)
      toast.error(err.message || 'Payment initialization failed. Please try again.')
    } finally {
      setPayingId(null)
    }
  }

  const handleViewReceipt = (appt: any) => {
    const totalAmount = appt.consultation_fee || 0
    const doctorShare = totalAmount * 0.85
    const platformFee = totalAmount * 0.15

    setReceiptDetails({
      transactionId: appt.razorpay_payment_id || 'N/A',
      doctorShare,
      platformFee,
      totalAmount,
      doctorName: appt.doctor_name,
      date: appt.appointment_date,
      time: appt.appointment_time,
    })
  }

  const handleCancel = async (id: string) => {
    if (window.confirm('Are you sure you want to cancel this appointment request?')) {
      try {
        setSelectedCancelId(id)
        await cancelAppointment(id)
        toast.success('Appointment request cancelled successfully.')
      } catch (err: any) {
        toast.error(err.message || 'Failed to cancel appointment request')
      } finally {
        setSelectedCancelId(null)
      }
    }
  }

  // Segment appointments
  const pendingRequests = appointments.filter(a => a.status === 'pending')
  const approvedRequests = appointments.filter(a => a.status === 'approved' || a.status === 'in_progress' || a.status === 'completed')
  const cancelledRequests = appointments.filter(a => a.status === 'cancelled' || a.status === 'rejected')

  const getActiveList = () => {
    switch (activeTab) {
      case 'approved':
        return approvedRequests
      case 'pending':
        return pendingRequests
      case 'cancelled':
        return cancelledRequests
      default:
        return []
    }
  }

  const activeList = getActiveList()

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'approved':
        return <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200">Approved</Badge>
      case 'in_progress':
        return <Badge className="bg-indigo-50 text-indigo-700 border-indigo-200">In Progress</Badge>
      case 'completed':
        return <Badge className="bg-blue-50 text-blue-700 border-blue-200">Completed</Badge>
      case 'pending':
        return <Badge className="bg-amber-50 text-amber-700 border-amber-200">Pending Approval</Badge>
      case 'cancelled':
        return <Badge className="bg-slate-50 text-slate-600 border-slate-200">Cancelled</Badge>
      case 'rejected':
        return <Badge className="bg-rose-50 text-rose-700 border-rose-200">Rejected</Badge>
      default:
        return <Badge>{status}</Badge>
    }
  }

  const isPaid = (appt: any) => {
    return appt.payment_status === 'paid' || appt.payment_status === 'success' || appt.payment_status === 'completed'
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">My Appointments</h1>
        <p className="text-slate-500 mt-1">Track and manage your scheduled consultations and requests.</p>
      </div>

      {/* Tabs list */}
      <div className="flex border-b border-slate-200">
        <button
          onClick={() => setActiveTab('pending')}
          className={`pb-3 px-4 text-sm font-semibold border-b-2 transition-all ${
            activeTab === 'pending'
              ? 'border-teal-600 text-teal-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Pending Requests ({pendingRequests.length})
        </button>
        <button
          onClick={() => setActiveTab('approved')}
          className={`pb-3 px-4 text-sm font-semibold border-b-2 transition-all ${
            activeTab === 'approved'
              ? 'border-teal-600 text-teal-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Upcoming Appointments ({approvedRequests.length})
        </button>
        <button
          onClick={() => setActiveTab('cancelled')}
          className={`pb-3 px-4 text-sm font-semibold border-b-2 transition-all ${
            activeTab === 'cancelled'
              ? 'border-teal-600 text-teal-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Cancelled / Rejected ({cancelledRequests.length})
        </button>
      </div>

      {isLoading && (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-28 bg-white border border-slate-200 rounded-xl animate-pulse" />
          ))}
        </div>
      )}

      {isError && (
        <div className="flex flex-col items-center justify-center py-12 text-center bg-white border rounded-xl">
          <div className="p-3 rounded-full bg-rose-50 mb-3">
            <AlertCircle className="h-6 w-6 text-rose-500" />
          </div>
          <h3 className="text-base font-semibold text-slate-800 mb-1">Failed to load appointments</h3>
          <p className="text-xs text-slate-500 mb-4 max-w-sm">
            {error?.message || 'Something went wrong while retrieving your appointment list.'}
          </p>
          <Button onClick={() => refetch()} variant="outline" size="sm">
            Retry
          </Button>
        </div>
      )}

      {!isLoading && !isError && activeList.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 text-center bg-white border border-dashed rounded-xl p-6">
          <div className="p-3 rounded-full bg-slate-50 mb-3 text-slate-400">
            <Calendar className="h-6 w-6" />
          </div>
          <h3 className="text-base font-semibold text-slate-800 mb-1">No appointments found</h3>
          <p className="text-xs text-slate-500 max-w-sm">
            {activeTab === 'pending'
              ? 'You do not have any pending appointment requests right now.'
              : activeTab === 'approved'
              ? 'You do not have any upcoming approved consultations scheduled.'
              : 'No cancelled or rejected appointment history was found.'}
          </p>
        </div>
      )}

      {!isLoading && !isError && activeList.length > 0 && (
        <div className="space-y-4">
          {activeList.map((appt) => (
            <Card key={appt.id} className="border-slate-200 hover:shadow-sm transition-shadow bg-white overflow-hidden">
              <CardContent className="p-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Stethoscope className="h-4 w-4 text-teal-600 shrink-0" />
                    <h3 className="font-bold text-slate-900">
                      {appt.doctor_name.toLowerCase().startsWith('dr.') ? appt.doctor_name : `Dr. ${appt.doctor_name}`}
                    </h3>
                    <span className="text-xs text-slate-400">•</span>
                    <span className="text-xs text-slate-500 font-medium">{appt.specialization}</span>
                  </div>

                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-slate-500 font-medium">
                    <div className="flex items-center gap-1">
                      <Calendar className="h-3.5 w-3.5 text-slate-400" />
                      <span>{appt.appointment_date}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="h-3.5 w-3.5 text-slate-400" />
                      <span>{appt.appointment_time}</span>
                    </div>
                    {getStatusBadge(appt.status)}
                    
                    {isPaid(appt) && (
                      <div className="flex flex-col gap-0.5 ml-1">
                        <div className="flex items-center gap-1.5">
                          <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200">Paid</Badge>
                          {appt.verified_at && (
                            <span className="text-[10px] text-slate-400">
                              on {new Date(appt.verified_at).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                      </div>
                    )}

                    {!isPaid(appt) && appt.payment_status && (
                      <div className="flex flex-col gap-0.5 ml-1">
                        {appt.payment_status === 'failed' && (
                          <Badge className="bg-rose-50 text-rose-700 border-rose-200">Failed</Badge>
                        )}
                        {appt.payment_status === 'cancelled' && (
                          <Badge className="bg-slate-50 text-slate-600 border-slate-200">Cancelled</Badge>
                        )}
                        {appt.payment_status === 'created' && (
                          <Badge className="bg-amber-50 text-amber-700 border-amber-200">Created</Badge>
                        )}
                      </div>
                    )}
                  </div>

                  {appt.razorpay_payment_id && isPaid(appt) && (
                    <div className="text-[10px] font-mono text-slate-500 bg-slate-50 border border-slate-100 rounded px-1.5 py-0.5 w-fit">
                      Txn ID: {appt.razorpay_payment_id}
                    </div>
                  )}

                  {appt.reason && (
                    <p className="text-xs text-slate-600 bg-slate-50 border border-slate-100 rounded px-2.5 py-1.5 leading-relaxed max-w-2xl">
                      <span className="font-semibold text-slate-800">Reason:</span> {appt.reason}
                    </p>
                  )}
                </div>

                <div className="flex gap-2 shrink-0">
                  {appt.status === 'pending' && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleCancel(appt.id)}
                      disabled={isCancelling && selectedCancelId === appt.id}
                      className="border-rose-200 text-rose-600 hover:bg-rose-50 hover:text-rose-700 hover:border-rose-300 text-xs shrink-0 flex items-center gap-1 h-9 px-3 rounded-lg"
                    >
                      <XCircle className="h-3.5 w-3.5" />
                      {isCancelling && selectedCancelId === appt.id ? 'Cancelling...' : 'Cancel Request'}
                    </Button>
                  )}

                  {appt.status === 'approved' && !isPaid(appt) && (
                    <Button
                      variant="default"
                      size="sm"
                      onClick={() => handlePayNow(appt)}
                      disabled={payingId !== null}
                      className="bg-teal-600 hover:bg-teal-700 text-white text-xs shrink-0 flex items-center gap-1 h-9 px-3 rounded-lg font-semibold shadow-sm"
                    >
                      {payingId === appt.id ? 'Initializing...' : (appt.payment_status === 'failed' || appt.payment_status === 'cancelled' ? 'Retry Payment' : 'Pay Now')}
                    </Button>
                  )}

                  {isPaid(appt) && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleViewReceipt(appt)}
                      className="border-teal-200 text-teal-600 hover:bg-teal-50 hover:text-teal-700 hover:border-teal-300 text-xs shrink-0 flex items-center gap-1.5 h-9 px-3 rounded-lg font-semibold"
                    >
                      <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      View Receipt
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Receipt Modal */}
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

export default function AppointmentsPage() {
  return (
    <ProtectedRoute allowedRoles={['patient']}>
      <AppointmentsContent />
    </ProtectedRoute>
  )
}
