'use client'

import { useState } from 'react'
import { Calendar, Clock, Stethoscope, AlertCircle, XCircle } from 'lucide-react'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { useAppointments, useCancelAppointment } from '@/hooks/use-appointments'
import { toast } from 'sonner'
import { useCreatePaymentOrder } from '@/hooks/use-payment'
import { useAuthStore } from '@/stores/auth'

type TabType = 'approved' | 'pending' | 'cancelled'

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
  const { user } = useAuthStore()
  const [payingId, setPayingId] = useState<string | null>(null)

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
        handler: function (response: any) {
          console.log('Razorpay callback payload captured:', response)
          toast.success('Payment completed successfully!')
          
          alert(
            `Payment Checkout Success!\n\n` +
            `Captured Callback Payload:\n` +
            `- Payment ID: ${response.razorpay_payment_id}\n` +
            `- Order ID: ${response.razorpay_order_id}\n` +
            `- Signature: ${response.razorpay_signature}\n\n` +
            `(Note: Verification will be completed in Sprint 2)`
          )
          
          refetch()
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
          ondismiss: () => {
            toast.error('Payment checkout closed.')
          }
        }
      }

      const rzp = new (window as any).Razorpay(options)
      rzp.on('payment.failed', function (response: any) {
        toast.error(`Checkout payment failed: ${response.error.description}`)
      })
      rzp.open()

    } catch (err: any) {
      console.error('Payment error:', err)
      toast.error(err.message || 'Payment initialization failed. Please try again.')
    } finally {
      setPayingId(null)
    }
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
                    {appt.payment_status && appt.payment_status !== 'pending' && (
                      <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200">Paid</Badge>
                    )}
                  </div>

                  {appt.reason && (
                    <p className="text-xs text-slate-600 bg-slate-50 border border-slate-100 rounded px-2.5 py-1.5 leading-relaxed max-w-2xl">
                      <span className="font-semibold text-slate-800">Reason:</span> {appt.reason}
                    </p>
                  )}
                </div>

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

                {appt.status === 'approved' && appt.payment_status === 'pending' && (
                  <Button
                    variant="default"
                    size="sm"
                    onClick={() => handlePayNow(appt)}
                    disabled={payingId === appt.id}
                    className="bg-teal-600 hover:bg-teal-700 text-white text-xs shrink-0 flex items-center gap-1 h-9 px-3 rounded-lg font-semibold"
                  >
                    {payingId === appt.id ? 'Initializing...' : 'Pay Now'}
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
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
