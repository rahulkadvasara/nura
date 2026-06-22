'use client'

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { toast } from 'sonner'
import { 
  Clock, 
  Plus, 
  Trash2, 
  Edit2, 
  Loader2, 
  Calendar, 
  AlertCircle, 
  X, 
  Info, 
  CheckCircle,
  AlertTriangle
} from 'lucide-react'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  useDoctorAvailability,
  useCreateAvailabilitySlot,
  useUpdateAvailabilitySlot,
  useDeleteAvailabilitySlot
} from '@/hooks/use-doctor-availability'
import { DoctorAvailability } from '@/types'

// Zod validation schema for form
const slotSchema = z.object({
  date: z.string().min(1, 'Date is required'),
  start_time: z.string().min(1, 'Start time is required'),
  end_time: z.string().min(1, 'End time is required'),
  slot_duration: z.coerce.number().min(5, 'Minimum 5 minutes').max(240, 'Maximum 240 minutes'),
  is_available: z.boolean().default(true),
}).refine((data) => {
  const [startH, startM] = data.start_time.split(':').map(Number)
  const [endH, endM] = data.end_time.split(':').map(Number)
  return (endH * 60 + endM) > (startH * 60 + startM)
}, {
  message: 'End time must be after start time',
  path: ['end_time']
})

type SlotFormValues = z.infer<typeof slotSchema>

function formatTime(timeStr: string) {
  const [hourStr, minStr] = timeStr.split(':')
  const hour = parseInt(hourStr)
  const ampm = hour >= 12 ? 'PM' : 'AM'
  const displayHour = hour % 12 || 12
  return `${displayHour}:${minStr} ${ampm}`
}

function formatDate(dateStr: string) {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    timeZone: 'UTC'
  })
}

function AvailabilityContent() {
  const { data: slots, isLoading, isError, error, refetch } = useDoctorAvailability()
  const createMutation = useCreateAvailabilitySlot()
  const updateMutation = useUpdateAvailabilitySlot()
  const deleteMutation = useDeleteAvailabilitySlot()

  const [isAddOpen, setIsAddOpen] = useState(false)
  const [editingSlot, setEditingSlot] = useState<DoctorAvailability | null>(null)

  // Setup Add Form
  const {
    register: registerAdd,
    handleSubmit: handleSubmitAdd,
    reset: resetAdd,
    formState: { errors: errorsAdd, isValid: isValidAdd }
  } = useForm<SlotFormValues>({
    resolver: zodResolver(slotSchema),
    mode: 'onChange',
    defaultValues: {
      slot_duration: 30,
      is_available: true
    }
  })

  // Setup Edit Form
  const {
    register: registerEdit,
    handleSubmit: handleSubmitEdit,
    setValue: setValueEdit,
    reset: resetEdit,
    formState: { errors: errorsEdit, isValid: isValidEdit }
  } = useForm<SlotFormValues>({
    resolver: zodResolver(slotSchema),
    mode: 'onChange'
  })

  // Populate Edit form values when editingSlot changes
  useEffect(() => {
    if (editingSlot) {
      setValueEdit('date', editingSlot.date)
      setValueEdit('start_time', editingSlot.start_time)
      setValueEdit('end_time', editingSlot.end_time)
      setValueEdit('slot_duration', editingSlot.slot_duration)
      setValueEdit('is_available', editingSlot.is_available)
    }
  }, [editingSlot, setValueEdit])

  // Group slots by date
  const grouped = slots ? slots.reduce((acc, slot) => {
    if (!acc[slot.date]) {
      acc[slot.date] = []
    }
    acc[slot.date].push(slot)
    return acc
  }, {} as Record<string, DoctorAvailability[]>) : {}

  const sortedDates = Object.keys(grouped).sort((a, b) => new Date(a).getTime() - new Date(b).getTime())
  sortedDates.forEach(date => {
    grouped[date].sort((a, b) => a.start_time.localeCompare(b.start_time))
  })

  const onAddSubmit = async (values: SlotFormValues) => {
    try {
      await createMutation.mutateAsync({
        ...values,
        active: true // default for legacy field
      })
      toast.success('Availability slot added successfully')
      setIsAddOpen(false)
      resetAdd()
    } catch (err: any) {
      toast.error(err.message || 'Failed to add availability slot')
    }
  }

  const onEditSubmit = async (values: SlotFormValues) => {
    if (!editingSlot) return
    try {
      await updateMutation.mutateAsync({
        id: editingSlot.id,
        slot: values
      })
      toast.success('Availability slot updated successfully')
      setEditingSlot(null)
      resetEdit()
    } catch (err: any) {
      toast.error(err.message || 'Failed to update availability slot')
    }
  }

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to permanently delete this availability slot?')) {
      try {
        await deleteMutation.mutateAsync(id)
        toast.success('Availability slot deleted successfully')
      } catch (err: any) {
        toast.error(err.message || 'Failed to delete availability slot')
      }
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div className="h-8 w-64 bg-slate-200 rounded-md animate-pulse" />
          <div className="h-10 w-40 bg-slate-200 rounded-md animate-pulse" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="h-[200px] bg-white border border-slate-200 rounded-xl animate-pulse" />
          <div className="h-[200px] bg-white border border-slate-200 rounded-xl animate-pulse" />
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="p-4 rounded-full bg-red-50 mb-4">
          <AlertCircle className="h-8 w-8 text-red-500" />
        </div>
        <h3 className="text-lg font-semibold text-slate-800 mb-1">
          Failed to load availability slots
        </h3>
        <p className="text-sm text-slate-500 mb-5 max-w-md">
          {error?.message || 'Something went wrong while fetching your slots. Please check your network and try again.'}
        </p>
        <Button onClick={() => refetch()} variant="outline" className="border-slate-300">
          Retry
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 border-b pb-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Manage Availability</h1>
          <p className="text-slate-500 mt-1">Configure your consultation calendar slots.</p>
        </div>
        <Button 
          onClick={() => setIsAddOpen(true)}
          className="bg-teal-600 hover:bg-teal-700 text-white flex items-center gap-2 self-start"
        >
          <Plus className="h-5 w-5" />
          Add Slot
        </Button>
      </div>

      {slots?.length === 0 ? (
        /* Empty State */
        <Card className="border-slate-200 text-center py-16">
          <CardContent className="flex flex-col items-center justify-center">
            <div className="p-4 rounded-full bg-teal-50 text-teal-600 mb-4">
              <Calendar className="h-10 w-10" />
            </div>
            <h3 className="text-lg font-bold text-slate-800 mb-1">No slots configured</h3>
            <p className="text-sm text-slate-500 mb-6 max-w-sm">
              You haven&apos;t added any schedule slots yet. Start setting up your availability so patients can book appointments.
            </p>
            <Button 
              onClick={() => setIsAddOpen(true)}
              className="bg-teal-600 hover:bg-teal-700 text-white"
            >
              Add Availability Slot
            </Button>
          </CardContent>
        </Card>
      ) : (
        /* Grouped Slots View */
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {sortedDates.map((dateStr) => (
            <Card key={dateStr} className="border-slate-200 shadow-sm overflow-hidden flex flex-col">
              <CardHeader className="bg-slate-50 border-b border-slate-100 py-3">
                <CardTitle className="text-sm font-bold text-slate-800 flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-teal-600" />
                  {formatDate(dateStr)}
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 flex-1 space-y-3">
                {grouped[dateStr].map((slot) => (
                  <div 
                    key={slot.id} 
                    className="flex items-center justify-between p-3 border border-slate-100 bg-slate-50/50 rounded-lg hover:border-slate-200 transition-colors"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-slate-400" />
                        <span className="text-sm font-semibold text-slate-800">
                          {formatTime(slot.start_time)} - {formatTime(slot.end_time)}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-slate-500">
                        <span>Duration: {slot.slot_duration} mins</span>
                        <span>•</span>
                        <Badge 
                          className={`font-normal border ${
                            slot.is_available && slot.active
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-100'
                              : 'bg-slate-100 text-slate-600 border-slate-200'
                          }`}
                        >
                          {slot.is_available && slot.active ? 'Available' : 'Unavailable'}
                        </Badge>
                      </div>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Button
                        size="icon"
                        variant="ghost"
                        onClick={() => setEditingSlot(slot)}
                        className="h-8 w-8 text-slate-500 hover:text-teal-600 hover:bg-teal-50"
                      >
                        <Edit2 className="h-4 w-4" />
                      </Button>
                      <Button
                        size="icon"
                        variant="ghost"
                        onClick={() => handleDelete(slot.id)}
                        disabled={deleteMutation.isPending}
                        className="h-8 w-8 text-slate-500 hover:text-red-600 hover:bg-red-50"
                      >
                        {deleteMutation.isPending ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Trash2 className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Add Slot Modal */}
      {isAddOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-xl border border-slate-200 shadow-xl max-w-md w-full overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="flex justify-between items-center bg-slate-50 px-6 py-4 border-b border-slate-100">
              <h3 className="font-bold text-slate-800 flex items-center gap-2 text-base">
                <Clock className="h-5 w-5 text-teal-600" />
                Add Availability Slot
              </h3>
              <Button 
                variant="ghost" 
                size="icon" 
                onClick={() => { setIsAddOpen(false); resetAdd(); }}
                className="h-8 w-8 hover:bg-slate-200 text-slate-500 rounded-full"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <form onSubmit={handleSubmitAdd(onAddSubmit)} className="p-6 space-y-4">
              <div className="space-y-2">
                <Label htmlFor="add-date">Date</Label>
                <Input 
                  id="add-date"
                  type="date"
                  min={new Date().toISOString().split('T')[0]}
                  {...registerAdd('date')} 
                />
                {errorsAdd.date && <p className="text-xs text-red-500">{errorsAdd.date.message}</p>}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="add-start">Start Time</Label>
                  <Input 
                    id="add-start"
                    type="time"
                    {...registerAdd('start_time')} 
                  />
                  {errorsAdd.start_time && <p className="text-xs text-red-500">{errorsAdd.start_time.message}</p>}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="add-end">End Time</Label>
                  <Input 
                    id="add-end"
                    type="time"
                    {...registerAdd('end_time')} 
                  />
                  {errorsAdd.end_time && <p className="text-xs text-red-500">{errorsAdd.end_time.message}</p>}
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="add-duration">Slot Duration (Minutes)</Label>
                <select
                  id="add-duration"
                  className="flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-teal-600"
                  {...registerAdd('slot_duration')}
                >
                  <option value={15}>15 Minutes</option>
                  <option value={30}>30 Minutes</option>
                  <option value={45}>45 Minutes</option>
                  <option value={60}>60 Minutes</option>
                  <option value={120}>120 Minutes</option>
                </select>
                {errorsAdd.slot_duration && <p className="text-xs text-red-500">{errorsAdd.slot_duration.message}</p>}
              </div>

              <div className="flex items-center gap-2 pt-2">
                <input
                  id="add-available"
                  type="checkbox"
                  className="rounded text-teal-600 focus:ring-teal-500 h-4 w-4"
                  {...registerAdd('is_available')}
                />
                <Label htmlFor="add-available" className="font-normal cursor-pointer select-none">
                  Mark this slot as available for booking immediately
                </Label>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t">
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => { setIsAddOpen(false); resetAdd(); }}
                  className="border-slate-200"
                >
                  Cancel
                </Button>
                <Button 
                  type="submit" 
                  disabled={createMutation.isPending || !isValidAdd}
                  className="bg-teal-600 hover:bg-teal-700 text-white flex items-center gap-2"
                >
                  {createMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                  Save Slot
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Slot Modal */}
      {editingSlot && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-xl border border-slate-200 shadow-xl max-w-md w-full overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="flex justify-between items-center bg-slate-50 px-6 py-4 border-b border-slate-100">
              <h3 className="font-bold text-slate-800 flex items-center gap-2 text-base">
                <Clock className="h-5 w-5 text-teal-600" />
                Edit Availability Slot
              </h3>
              <Button 
                variant="ghost" 
                size="icon" 
                onClick={() => { setEditingSlot(null); resetEdit(); }}
                className="h-8 w-8 hover:bg-slate-200 text-slate-500 rounded-full"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <form onSubmit={handleSubmitEdit(onEditSubmit)} className="p-6 space-y-4">
              <div className="p-3 bg-amber-50 border border-amber-100 rounded-lg flex items-start gap-2.5 text-xs text-amber-800 mb-1">
                <AlertTriangle className="h-4 w-4 mt-0.5 text-amber-600 flex-shrink-0" />
                <span>
                  <strong>Caution:</strong> Changes will fail if this slot is already booked for an approved appointment.
                </span>
              </div>

              <div className="space-y-2">
                <Label htmlFor="edit-date">Date</Label>
                <Input 
                  id="edit-date"
                  type="date"
                  {...registerEdit('date')} 
                />
                {errorsEdit.date && <p className="text-xs text-red-500">{errorsEdit.date.message}</p>}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="edit-start">Start Time</Label>
                  <Input 
                    id="edit-start"
                    type="time"
                    {...registerEdit('start_time')} 
                  />
                  {errorsEdit.start_time && <p className="text-xs text-red-500">{errorsEdit.start_time.message}</p>}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="edit-end">End Time</Label>
                  <Input 
                    id="edit-end"
                    type="time"
                    {...registerEdit('end_time')} 
                  />
                  {errorsEdit.end_time && <p className="text-xs text-red-500">{errorsEdit.end_time.message}</p>}
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="edit-duration">Slot Duration (Minutes)</Label>
                <select
                  id="edit-duration"
                  className="flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-teal-600"
                  {...registerEdit('slot_duration')}
                >
                  <option value={15}>15 Minutes</option>
                  <option value={30}>30 Minutes</option>
                  <option value={45}>45 Minutes</option>
                  <option value={60}>60 Minutes</option>
                  <option value={120}>120 Minutes</option>
                </select>
                {errorsEdit.slot_duration && <p className="text-xs text-red-500">{errorsEdit.slot_duration.message}</p>}
              </div>

              <div className="flex items-center gap-2 pt-2">
                <input
                  id="edit-available"
                  type="checkbox"
                  className="rounded text-teal-600 focus:ring-teal-500 h-4 w-4"
                  {...registerEdit('is_available')}
                />
                <Label htmlFor="edit-available" className="font-normal cursor-pointer select-none">
                  Mark this slot as available for booking
                </Label>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t">
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => { setEditingSlot(null); resetEdit(); }}
                  className="border-slate-200"
                >
                  Cancel
                </Button>
                <Button 
                  type="submit" 
                  disabled={updateMutation.isPending || !isValidEdit}
                  className="bg-teal-600 hover:bg-teal-700 text-white flex items-center gap-2"
                >
                  {updateMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                  Update Slot
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default function DoctorAvailabilityPage() {
  return (
    <ProtectedRoute allowedRoles={['doctor']}>
      <AvailabilityContent />
    </ProtectedRoute>
  )
}
