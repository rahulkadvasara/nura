'use client'

import { useParams, useRouter } from 'next/navigation'
import { 
  ArrowLeft, 
  Clock, 
  MapPin, 
  Languages, 
  Star, 
  DollarSign, 
  Calendar,
  User,
  GraduationCap,
  Award,
  AlertCircle,
  Stethoscope
} from 'lucide-react'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useDoctorDetails, useDoctorAvailability } from '@/hooks/use-doctor-discovery'
import { DoctorAvailability } from '@/types'

function formatDateHeader(dateStr: string): string {
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-IN', {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
    })
  } catch {
    return dateStr
  }
}

function DoctorDetailsContent() {
  const params = useParams()
  const router = useRouter()
  const doctorId = params.doctorId as string

  const { 
    data: doctor, 
    isLoading: isProfileLoading, 
    isError: isProfileError, 
    error: profileError 
  } = useDoctorDetails(doctorId)

  const { 
    data: availabilityData, 
    isLoading: isAvailLoading, 
    isError: isAvailError 
  } = useDoctorAvailability(doctorId)

  const slots = availabilityData?.slots || []

  // Group slots by date
  const groupedSlots = slots.reduce((acc, slot) => {
    if (!acc[slot.date]) {
      acc[slot.date] = []
    }
    acc[slot.date].push(slot)
    return acc
  }, {} as Record<string, DoctorAvailability[]>)

  // Sort dates chronologically
  const sortedDates = Object.keys(groupedSlots).sort()

  const handleBack = () => {
    router.push('/dashboard/doctors')
  }

  const isLoading = isProfileLoading || isAvailLoading

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse max-w-5xl">
        <div className="h-6 w-32 bg-slate-200 rounded-md" />
        <div className="h-[200px] bg-white border border-slate-200 rounded-xl" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 h-[300px] bg-white border border-slate-200 rounded-xl" />
          <div className="h-[200px] bg-white border border-slate-200 rounded-xl" />
        </div>
      </div>
    )
  }

  if (isProfileError || !doctor) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="p-4 rounded-full bg-red-50 mb-4">
          <AlertCircle className="h-8 w-8 text-red-500" />
        </div>
        <h3 className="text-lg font-semibold text-slate-800 mb-1">
          Failed to load doctor profile
        </h3>
        <p className="text-sm text-slate-500 mb-5 max-w-md">
          {profileError?.message || 'The requested doctor profile could not be loaded.'}
        </p>
        <Button onClick={handleBack} className="bg-teal-600 hover:bg-teal-700 text-white">
          Back to Directory
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Back Button */}
      <button 
        onClick={handleBack}
        className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 font-medium transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Directory
      </button>

      {/* Doctor Info Card */}
      <Card className="border-slate-200 shadow-sm bg-white overflow-hidden">
        <CardContent className="p-6 md:p-8">
          <div className="flex flex-col md:flex-row gap-6 items-start">
            {/* Profile pic */}
            {doctor.profile_picture ? (
              <img
                src={doctor.profile_picture}
                alt={doctor.name}
                className="h-24 w-24 md:h-28 md:w-28 rounded-2xl object-cover border border-slate-100 shadow-sm shrink-0"
              />
            ) : (
              <div className="h-24 w-24 md:h-28 md:w-28 rounded-2xl bg-teal-50 border border-teal-100/50 text-teal-600 flex items-center justify-center shrink-0">
                <User className="h-10 w-10" />
              </div>
            )}

            {/* General Credentials info */}
            <div className="space-y-4 flex-1">
              <div>
                <div className="flex flex-col sm:flex-row sm:items-center gap-2 mb-1.5">
                  <h1 className="text-2xl font-bold text-slate-900">
                    {doctor.name.toLowerCase().startsWith('dr.') ? doctor.name : `Dr. ${doctor.name}`}
                  </h1>
                  <Badge className="bg-teal-50 text-teal-700 hover:bg-teal-100/50 border-teal-100/30 text-xs py-0.5 px-2.5 self-start sm:self-auto font-semibold">
                    {doctor.specialization}
                  </Badge>
                </div>

                <div className="flex items-center gap-1.5 text-xs text-slate-500">
                  <div className="flex items-center text-amber-500">
                    <Star className="h-4 w-4 fill-current" />
                    <span className="font-bold text-slate-700 ml-1">
                      {doctor.average_rating > 0 ? doctor.average_rating.toFixed(1) : 'New'}
                    </span>
                  </div>
                  <span>•</span>
                  <span>{doctor.total_reviews} Reviews</span>
                </div>
              </div>

              {/* Bio summary */}
              {doctor.bio && (
                <p className="text-sm text-slate-600 leading-relaxed max-w-3xl">
                  {doctor.bio}
                </p>
              )}

              {/* Grid with info */}
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-xs text-slate-500 pt-2 border-t border-slate-50">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-slate-400" />
                  <span>{doctor.experience_years} Years of Experience</span>
                </div>
                {doctor.hospital && (
                  <div className="flex items-center gap-2">
                    <MapPin className="h-4 w-4 text-slate-400" />
                    <span className="truncate">{doctor.hospital}</span>
                  </div>
                )}
                {doctor.languages && doctor.languages.length > 0 && (
                  <div className="flex items-center gap-2">
                    <Languages className="h-4 w-4 text-slate-400" />
                    <span>Speaks: {doctor.languages.join(', ')}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Side: Booking slots list */}
        <div className="md:col-span-2 space-y-6">
          <Card className="border-slate-200 shadow-sm bg-white">
            <CardHeader className="border-b border-slate-100">
              <CardTitle className="text-base font-bold text-slate-800 flex items-center gap-2">
                <Calendar className="h-5 w-5 text-teal-600" />
                Available Consultation Slots
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              {isAvailError && (
                <div className="text-sm text-rose-500 p-3 bg-rose-50 border border-rose-100 rounded-md">
                  Failed to load doctor&apos;s availability slots. Please try again.
                </div>
              )}

              {!isAvailError && sortedDates.length === 0 && (
                <div className="flex flex-col items-center justify-center py-8 text-center text-slate-400 space-y-2 border border-dashed rounded-lg p-6 bg-slate-50/50">
                  <Calendar className="h-8 w-8 text-slate-300" />
                  <p className="text-xs">No future available slots matching this doctor.</p>
                </div>
              )}

              {!isAvailError && sortedDates.length > 0 && (
                <div className="space-y-6">
                  {sortedDates.map((dateStr) => (
                    <div key={dateStr} className="space-y-2.5">
                      {/* Group Header */}
                      <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-teal-500 inline-block" />
                        {formatDateHeader(dateStr)}
                      </h4>
                      {/* Slot Timings Grid */}
                      <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
                        {groupedSlots[dateStr].map((slot) => (
                          <div 
                            key={slot.id}
                            className="bg-slate-50/70 border border-slate-100 text-slate-700 py-2 px-2.5 text-center text-xs font-semibold rounded-lg hover:border-teal-500/30 hover:bg-teal-50/20 cursor-not-allowed transition-colors select-none"
                          >
                            {slot.start_time}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Side: Professional details / booking sidebar */}
        <div className="space-y-6">
          {/* Fee card & Booking actions */}
          <Card className="border-slate-200 shadow-sm bg-white overflow-hidden">
            <CardHeader className="bg-slate-50/50 border-b border-slate-100 p-4">
              <CardTitle className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                Booking Information
              </CardTitle>
            </CardHeader>
            <CardContent className="p-5 space-y-5">
              <div className="flex justify-between items-baseline border-b border-slate-50 pb-4">
                <span className="text-xs text-slate-500 font-medium">Consultation Fee</span>
                <span className="text-2xl font-black text-slate-900">
                  ₹{doctor.consultation_fee}
                </span>
              </div>

              {/* Disabled booking CTA button */}
              <div className="space-y-3">
                <Button 
                  disabled 
                  className="w-full bg-teal-600 disabled:opacity-50 text-white font-bold py-2.5 text-sm cursor-not-allowed"
                >
                  Book Appointment
                </Button>
                <p className="text-[10px] text-slate-400 leading-relaxed text-center font-medium">
                  * Online scheduling is currently locked. Booking functions will be activated in Phase 6, Sprint 2.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Qualifications & Education details */}
          <Card className="border-slate-200 shadow-sm bg-white">
            <CardHeader className="border-b border-slate-100 p-4">
              <CardTitle className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                Academic Qualifications
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 space-y-3.5 text-xs text-slate-600 leading-normal">
              {doctor.education && (
                <div className="flex items-start gap-2.5">
                  <GraduationCap className="h-4 w-4 text-slate-400 shrink-0" />
                  <div>
                    <span className="font-semibold text-slate-800 block">Education</span>
                    <span>{doctor.education}</span>
                  </div>
                </div>
              )}
              {doctor.qualifications && doctor.qualifications.length > 0 && (
                <div className="flex items-start gap-2.5">
                  <Award className="h-4 w-4 text-slate-400 shrink-0" />
                  <div>
                    <span className="font-semibold text-slate-800 block">Certifications</span>
                    <span>{doctor.qualifications.join(', ')}</span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default function DoctorDetailsPage() {
  return (
    <ProtectedRoute allowedRoles={['patient']}>
      <DoctorDetailsContent />
    </ProtectedRoute>
  )
}
