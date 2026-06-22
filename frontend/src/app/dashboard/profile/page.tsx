'use client'

import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { toast } from 'sonner'
import { 
  User, 
  Loader2, 
  CheckCircle2, 
  ShieldCheck, 
  Award, 
  FileText, 
  Coins, 
  Clock, 
  GraduationCap, 
  Globe, 
  AlertCircle
} from 'lucide-react'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useDoctorProfile, useUpdateDoctorProfile } from '@/hooks/use-doctor-profile'

// Validation schema
const profileSchema = z.object({
  education: z.string().min(1, 'Education/Degrees are required').max(500),
  consultation_fee: z.coerce.number().min(0, 'Consultation fee must be positive'),
  experience_years: z.coerce.number().int().min(0, 'Experience must be positive').max(80, 'Must be under 80 years'),
  languages: z.string().min(1, 'Languages are required'),
  bio: z.string().min(10, 'Biography must be at least 10 characters').max(2000, 'Biography must be under 2000 characters'),
})

type ProfileFormValues = z.infer<typeof profileSchema>

function ProfileContent() {
  const { data, isLoading, isError, error, refetch } = useDoctorProfile()
  const updateMutation = useUpdateDoctorProfile()

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isValid }
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    mode: 'onChange'
  })

  // Pre-fill form when data is loaded
  useEffect(() => {
    if (data) {
      const { profile } = data
      setValue('education', profile.education || '')
      setValue('consultation_fee', profile.consultation_fee)
      setValue('experience_years', profile.experience_years)
      setValue('languages', profile.languages ? profile.languages.join(', ') : '')
      setValue('bio', profile.bio || '')
    }
  }, [data, setValue])

  const onSubmit = async (values: ProfileFormValues) => {
    try {
      const formattedPayload = {
        ...values,
        languages: values.languages.split(',').map(lang => lang.trim()).filter(Boolean)
      }
      await updateMutation.mutateAsync(formattedPayload)
      toast.success('Professional profile updated successfully')
    } catch (err: any) {
      toast.error(err.message || 'Failed to update professional profile')
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'verified':
      case 'approved':
      case 'Approved':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200'
      case 'rejected':
      case 'Rejected':
        return 'bg-rose-50 text-rose-700 border-rose-200'
      default:
        return 'bg-amber-50 text-amber-700 border-amber-200'
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-slate-200 rounded-md animate-pulse" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 h-[400px] bg-white border border-slate-200 rounded-xl animate-pulse" />
          <div className="h-[250px] bg-white border border-slate-200 rounded-xl animate-pulse" />
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
          Failed to load profile details
        </h3>
        <p className="text-sm text-slate-500 mb-5 max-w-md">
          {error?.message || 'Something went wrong while fetching your profile. Please check your credentials.'}
        </p>
        <Button onClick={() => refetch()} variant="outline" className="border-slate-300">
          Retry
        </Button>
      </div>
    )
  }

  if (!data) return null

  const { profile, documents } = data

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Header with status badge */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 border-b pb-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Practitioner Profile</h1>
          <p className="text-slate-500 mt-1">Manage your public medical profile and settings.</p>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <Badge className={`px-3 py-1 font-semibold text-sm border ${getStatusColor(profile.profile_status)}`}>
            {profile.profile_status === 'verified' && <CheckCircle2 className="h-4 w-4 mr-1.5 inline" />}
            Status: {profile.profile_status.toUpperCase()}
          </Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Form settings */}
        <form onSubmit={handleSubmit(onSubmit)} className="lg:col-span-2 space-y-6">
          <Card className="border-slate-200 shadow-sm">
            <CardHeader>
              <CardTitle className="text-base font-bold text-slate-800 flex items-center gap-2">
                <User className="h-5 w-5 text-teal-600" />
                Professional Credentials
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="education" className="flex items-center gap-1.5">
                  <GraduationCap className="h-4 w-4 text-slate-400" />
                  Education & Degrees
                </Label>
                <Input 
                  id="education" 
                  placeholder="e.g. MBBS, MD (Cardiology)" 
                  {...register('education')} 
                />
                {errors.education && <p className="text-xs text-rose-500">{errors.education.message}</p>}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="consultation_fee" className="flex items-center gap-1.5">
                    <Coins className="h-4 w-4 text-slate-400" />
                    Consultation Fee (INR)
                  </Label>
                  <div className="relative">
                    <Input 
                      id="consultation_fee" 
                      type="number"
                      placeholder="e.g. 500" 
                      {...register('consultation_fee')} 
                    />
                    <span className="absolute right-3 top-2.5 text-xs text-slate-400 font-medium">₹</span>
                  </div>
                  {errors.consultation_fee && <p className="text-xs text-rose-500">{errors.consultation_fee.message}</p>}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="experience_years" className="flex items-center gap-1.5">
                    <Clock className="h-4 w-4 text-slate-400" />
                    Years of Experience
                  </Label>
                  <div className="relative">
                    <Input 
                      id="experience_years" 
                      type="number"
                      placeholder="e.g. 10" 
                      {...register('experience_years')} 
                    />
                    <span className="absolute right-3 top-2.5 text-xs text-slate-400 font-medium">Years</span>
                  </div>
                  {errors.experience_years && <p className="text-xs text-rose-500">{errors.experience_years.message}</p>}
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="languages" className="flex items-center gap-1.5">
                  <Globe className="h-4 w-4 text-slate-400" />
                  Languages Spoken (Comma Separated)
                </Label>
                <Input 
                  id="languages" 
                  placeholder="e.g. English, Hindi, Spanish" 
                  {...register('languages')} 
                />
                {errors.languages && <p className="text-xs text-rose-500">{errors.languages.message}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="bio">Professional Biography</Label>
                <textarea 
                  id="bio" 
                  rows={6}
                  placeholder="Tell patients about your medical background, specialization, clinical experience..."
                  className="flex w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-teal-600 disabled:cursor-not-allowed disabled:opacity-50 leading-relaxed"
                  {...register('bio')} 
                />
                {errors.bio && <p className="text-xs text-rose-500">{errors.bio.message}</p>}
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-end gap-3">
            <Button 
              type="submit" 
              disabled={updateMutation.isPending || !isValid} 
              className="bg-teal-600 hover:bg-teal-700 text-white flex items-center gap-2"
            >
              {updateMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              Save Profile Settings
            </Button>
          </div>
        </form>

        {/* Right Column: Read-only profile details and document status */}
        <div className="space-y-6">
          {/* Read only info card */}
          <Card className="border-slate-200 shadow-sm bg-slate-50/50">
            <CardHeader>
              <CardTitle className="text-sm font-bold text-slate-800 flex items-center gap-2">
                <Award className="h-4 w-4 text-teal-600" />
                Office Registration
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-xs leading-relaxed">
              <div className="flex justify-between border-b pb-2 border-slate-100">
                <span className="text-slate-500">Specialization</span>
                <span className="font-semibold text-slate-850">{profile.specialization}</span>
              </div>
              <div className="flex justify-between border-b pb-2 border-slate-100">
                <span className="text-slate-500">Affiliation</span>
                <span className="font-semibold text-slate-850">{profile.hospital || 'Not affiliated'}</span>
              </div>
              <div className="flex justify-between border-b pb-2 border-slate-100">
                <span className="text-slate-500">License Number</span>
                <span className="font-semibold text-slate-850">{profile.license_number || 'N/A'}</span>
              </div>
              <div className="flex justify-between border-b pb-2 border-slate-100">
                <span className="text-slate-500">Member Since</span>
                <span className="font-semibold text-slate-850">{new Date(profile.created_at).toLocaleDateString('en-IN')}</span>
              </div>
              <p className="text-[10px] text-slate-400 mt-2 leading-normal">
                * Note: Registration credentials are locked on approval. Contact administration support to request license adjustments.
              </p>
            </CardContent>
          </Card>

          {/* Verification documents visibility */}
          <Card className="border-slate-200 shadow-sm">
            <CardHeader>
              <CardTitle className="text-sm font-bold text-slate-800 flex items-center gap-2">
                <FileText className="h-4 w-4 text-teal-600" />
                Uploaded Documents
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {documents.length === 0 ? (
                <p className="text-xs text-slate-500 italic">No documents uploaded.</p>
              ) : (
                documents.map((doc) => (
                  <div 
                    key={doc.id} 
                    className="flex flex-col p-2.5 bg-slate-50 border border-slate-100 rounded-lg text-xs gap-1.5"
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-semibold capitalize text-slate-700">
                        {doc.document_type.replace('_', ' ')}
                      </span>
                      <Badge className={`text-[10px] font-normal border ${getStatusColor(doc.verification_status)}`}>
                        {doc.verification_status}
                      </Badge>
                    </div>
                    <a 
                      href={doc.document_url} 
                      target="_blank" 
                      rel="noopener noreferrer" 
                      className="text-[11px] text-teal-600 hover:underline inline-block truncate max-w-[200px]"
                    >
                      View Submitted Credentials
                    </a>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default function DoctorProfilePage() {
  return (
    <ProtectedRoute allowedRoles={['doctor']}>
      <ProfileContent />
    </ProtectedRoute>
  )
}
