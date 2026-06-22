'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { 
  useDoctorApplication, 
  useApplyAsDoctor, 
  useUpdateDoctorApplication 
} from '@/hooks/use-doctor-application'
import { useAuthStore } from '@/stores/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { 
  Stethoscope, 
  Loader2, 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  FileText, 
  Globe, 
  Building, 
  Award, 
  ShieldCheck, 
  Clock, 
  Coins,
  ArrowRight,
  ArrowLeft,
  ChevronRight,
  PenTool,
  Check
} from 'lucide-react'

// Zod validation schema
const applicationSchema = z.object({
  specialization: z.string().min(1, 'Specialization is required').max(200),
  experience_years: z.coerce.number().int().min(0, 'Experience must be positive').max(80, 'Must be under 80 years'),
  consultation_fee: z.coerce.number().min(0, 'Consultation fee must be positive'),
  bio: z.string().min(10, 'Bio must be at least 10 characters').max(2000, 'Bio must be under 2000 characters'),
  education: z.string().min(1, 'Education/Degrees are required').max(500),
  languages: z.string().min(1, 'At least one language is required'),
  hospital: z.string().max(300, 'Hospital name is too long').optional(),
  license_number: z.string().min(1, 'License number is required').max(100),
  
  // Document URLs
  degree_certificate_url: z.string().url('Must be a valid document URL'),
  medical_license_url: z.string().url('Must be a valid document URL'),
  identity_proof_url: z.string().url('Must be a valid document URL'),
})

type ApplicationFormValues = z.infer<typeof applicationSchema>

export default function DoctorApplicationPage() {
  const router = useRouter()
  const { user } = useAuthStore()
  const { data: application, isLoading, error, refetch } = useDoctorApplication()
  const applyMutation = useApplyAsDoctor()
  const updateMutation = useUpdateDoctorApplication()
  
  const [isEditing, setIsEditing] = useState(false)
  const [currentStep, setCurrentStep] = useState(1)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [submitSuccess, setSubmitSuccess] = useState(false)

  // Redirect non-patients
  useEffect(() => {
    if (user && user.role !== 'patient') {
      router.replace('/dashboard')
    }
  }, [user, router])

  const {
    register,
    handleSubmit,
    setValue,
    reset,
    trigger,
    formState: { errors, isValid }
  } = useForm<ApplicationFormValues>({
    resolver: zodResolver(applicationSchema),
    mode: 'onChange'
  })

  // Pre-fill form when editing
  useEffect(() => {
    if (application && (isEditing || application.profile_status === 'pending')) {
      const profile = application.profile
      const docs = application.documents
      
      setValue('specialization', profile.specialization)
      setValue('experience_years', profile.experience_years)
      setValue('consultation_fee', profile.consultation_fee)
      setValue('bio', profile.bio || '')
      setValue('education', profile.education || '')
      setValue('languages', profile.languages ? profile.languages.join(', ') : '')
      setValue('hospital', profile.hospital || '')
      setValue('license_number', profile.license_number || '')

      const degreeDoc = docs.find(d => d.document_type === 'degree')
      const licenseDoc = docs.find(d => d.document_type === 'license')
      const idDoc = docs.find(d => d.document_type === 'id_proof')

      if (degreeDoc) setValue('degree_certificate_url', degreeDoc.document_url)
      if (licenseDoc) setValue('medical_license_url', licenseDoc.document_url)
      if (idDoc) setValue('identity_proof_url', idDoc.document_url)
    }
  }, [application, isEditing, setValue])

  if (user?.role !== 'patient') {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-pulse text-slate-500">Redirecting...</div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-slate-200 rounded-md animate-pulse" />
        <div className="h-[400px] bg-white border border-slate-200 rounded-lg animate-pulse" />
      </div>
    )
  }

  const handleNextStep = async () => {
    let fieldsToValidate: (keyof ApplicationFormValues)[] = []
    if (currentStep === 1) {
      fieldsToValidate = ['specialization', 'experience_years', 'consultation_fee', 'license_number', 'hospital']
    } else if (currentStep === 2) {
      fieldsToValidate = ['education', 'languages', 'bio']
    }

    const isStepValid = await trigger(fieldsToValidate)
    if (isStepValid) {
      setCurrentStep(prev => prev + 1)
    }
  }

  const handlePrevStep = () => {
    setCurrentStep(prev => prev - 1)
  }

  const onSubmit = async (values: ApplicationFormValues) => {
    setSubmitError(null)
    const formattedPayload = {
      ...values,
      languages: values.languages.split(',').map(lang => lang.trim()).filter(Boolean)
    }

    try {
      if (application && isEditing) {
        await updateMutation.mutateAsync(formattedPayload)
        setIsEditing(false)
      } else {
        await applyMutation.mutateAsync(formattedPayload)
      }
      setSubmitSuccess(true)
      refetch()
    } catch (err: any) {
      setSubmitError(err.message || 'An unexpected error occurred. Please try again.')
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'verified':
      case 'Approved':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200'
      case 'rejected':
      case 'Rejected':
        return 'bg-rose-50 text-rose-700 border-rose-200'
      default:
        return 'bg-amber-50 text-amber-700 border-amber-200'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'verified':
      case 'Approved':
        return <CheckCircle2 className="h-10 w-10 text-emerald-500" />
      case 'rejected':
      case 'Rejected':
        return <XCircle className="h-10 w-10 text-rose-500" />
      default:
        return <Clock className="h-10 w-10 text-amber-500" />
    }
  }

  // Render Status View if application exists and not in editing mode
  if (application && !isEditing) {
    const { application_status, profile, documents } = application
    return (
      <div className="space-y-6 max-w-4xl">
        <div className="flex flex-col gap-1">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Doctor Application</h1>
          <p className="text-slate-500">Track your verification application status.</p>
        </div>

        {/* Overall Status Card */}
        <div className={`p-6 border rounded-xl flex items-start gap-4 shadow-sm ${getStatusColor(application_status)}`}>
          <div className="mt-1">{getStatusIcon(application_status)}</div>
          <div className="space-y-1 flex-1">
            <div className="flex items-center gap-2">
              <h2 className="font-bold text-lg">Status: {application_status}</h2>
              <Badge variant="outline" className={`${getStatusColor(application_status)} font-normal px-2.5 py-0.5`}>
                {profile.profile_status}
              </Badge>
            </div>
            <p className="text-sm opacity-90 leading-relaxed">
              {application_status === 'Pending Review' && 
                'Your onboarding application is currently under review by our medical directors. This process normally takes 2-3 business days. You will be notified via email.'}
              {application_status === 'Approved' && 
                'Congratulations! Your credentials have been successfully verified. You will be promoted to the Doctor role shortly. Our support team will guide you on next steps.'}
              {application_status === 'Rejected' && 
                'Unfortunately, your application was not approved. Please contact our support desk for detailed clarification on document requirements.'}
            </p>
            {application_status === 'Pending Review' && (
              <div className="pt-3">
                <Button 
                  onClick={() => setIsEditing(true)} 
                  variant="outline" 
                  className="bg-white hover:bg-slate-50 text-slate-800 border-slate-200"
                >
                  <PenTool className="mr-2 h-4 w-4" />
                  Edit Application Details
                </Button>
              </div>
            )}
          </div>
        </div>

        {/* Application Details Summary */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Profile Details */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="font-bold text-slate-800 border-b pb-2 flex items-center gap-2">
              <Stethoscope className="h-5 w-5 text-teal-600" />
              Professional Profile
            </h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between"><span className="text-slate-500">Specialization</span><span className="font-medium text-slate-800">{profile.specialization}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Experience</span><span className="font-medium text-slate-800">{profile.experience_years} Years</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Consultation Fee</span><span className="font-medium text-slate-800">₹{profile.consultation_fee}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">License Number</span><span className="font-medium text-slate-800">{profile.license_number}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Hospital</span><span className="font-medium text-slate-800">{profile.hospital || 'Not provided'}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Languages</span><span className="font-medium text-slate-800">{profile.languages.join(', ')}</span></div>
              <div className="pt-2 border-t"><span className="text-slate-500 block mb-1">Bio</span><p className="text-slate-700 italic bg-slate-50 p-3 rounded-lg leading-relaxed text-xs">{profile.bio}</p></div>
            </div>
          </div>

          {/* Document Details */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="font-bold text-slate-800 border-b pb-2 flex items-center gap-2">
              <FileText className="h-5 w-5 text-teal-600" />
              Uploaded Metadata
            </h3>
            <div className="space-y-4">
              {documents.map((doc) => (
                <div key={doc.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-100 text-sm">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="h-5 w-5 text-teal-500" />
                    <div>
                      <span className="font-medium capitalize text-slate-800 block">{doc.document_type.replace('_', ' ')}</span>
                      <a href={doc.document_url} target="_blank" rel="noopener noreferrer" className="text-xs text-teal-600 hover:underline">
                        View submitted URL
                      </a>
                    </div>
                  </div>
                  <Badge variant="outline" className={`${getStatusColor(doc.verification_status)} capitalize`}>
                    {doc.verification_status}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Render Form View
  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">
          {application ? 'Update Onboarding Application' : 'Apply as Doctor'}
        </h1>
        <p className="text-slate-500">
          {application ? 'Update your submitted credentials and verification details.' : 'Provide professional details and documents to be verified on Nura.'}
        </p>
      </div>

      {/* Step Indicator */}
      <div className="flex items-center justify-between bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
        <div className="flex items-center gap-2">
          <div className={`h-8 w-8 rounded-full flex items-center justify-center text-sm font-semibold transition-colors ${currentStep >= 1 ? 'bg-teal-600 text-white' : 'bg-slate-100 text-slate-600'}`}>1</div>
          <span className="text-sm font-medium text-slate-700">Information</span>
        </div>
        <ChevronRight className="h-4 w-4 text-slate-400" />
        <div className="flex items-center gap-2">
          <div className={`h-8 w-8 rounded-full flex items-center justify-center text-sm font-semibold transition-colors ${currentStep >= 2 ? 'bg-teal-600 text-white' : 'bg-slate-100 text-slate-600'}`}>2</div>
          <span className="text-sm font-medium text-slate-700">Bio & Languages</span>
        </div>
        <ChevronRight className="h-4 w-4 text-slate-400" />
        <div className="flex items-center gap-2">
          <div className={`h-8 w-8 rounded-full flex items-center justify-center text-sm font-semibold transition-colors ${currentStep >= 3 ? 'bg-teal-600 text-white' : 'bg-slate-100 text-slate-600'}`}>3</div>
          <span className="text-sm font-medium text-slate-700">Verification Docs</span>
        </div>
      </div>

      {/* Form Card */}
      <form onSubmit={handleSubmit(onSubmit)} className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-6">
        {submitError && (
          <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg flex items-center gap-2 text-sm">
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
            <span>{submitError}</span>
          </div>
        )}

        {/* STEP 1: Professional Information */}
        {currentStep === 1 && (
          <div className="space-y-4">
            <h2 className="text-lg font-bold text-slate-800 border-b pb-2 flex items-center gap-2">
              <Stethoscope className="h-5 w-5 text-teal-600" />
              Professional Details
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="specialization">Medical Specialization</Label>
                <Input 
                  id="specialization" 
                  placeholder="e.g. Cardiologist, Dermatologist" 
                  {...register('specialization')} 
                />
                {errors.specialization && <p className="text-xs text-rose-500">{errors.specialization.message}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="license_number">Medical License Number</Label>
                <Input 
                  id="license_number" 
                  placeholder="e.g. MCI-12345" 
                  {...register('license_number')} 
                />
                {errors.license_number && <p className="text-xs text-rose-500">{errors.license_number.message}</p>}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="experience_years">Years of Experience</Label>
                <div className="relative">
                  <Input 
                    id="experience_years" 
                    type="number"
                    placeholder="e.g. 5" 
                    {...register('experience_years')} 
                  />
                  <span className="absolute right-3 top-2.5 text-xs text-slate-400 font-medium">Years</span>
                </div>
                {errors.experience_years && <p className="text-xs text-rose-500">{errors.experience_years.message}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="consultation_fee">Consultation Fee (INR)</Label>
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
            </div>

            <div className="space-y-2">
              <Label htmlFor="hospital">Hospital / Clinic Affiliation (Optional)</Label>
              <Input 
                id="hospital" 
                placeholder="e.g. City General Hospital, Apollo Clinics" 
                {...register('hospital')} 
              />
              {errors.hospital && <p className="text-xs text-rose-500">{errors.hospital.message}</p>}
            </div>
          </div>
        )}

        {/* STEP 2: Bio & Education */}
        {currentStep === 2 && (
          <div className="space-y-4">
            <h2 className="text-lg font-bold text-slate-800 border-b pb-2 flex items-center gap-2">
              <Award className="h-5 w-5 text-teal-600" />
              Credentials & Languages
            </h2>

            <div className="space-y-2">
              <Label htmlFor="education">Education & Degrees</Label>
              <Input 
                id="education" 
                placeholder="e.g. MBBS, MD (Cardiology)" 
                {...register('education')} 
              />
              {errors.education && <p className="text-xs text-rose-500">{errors.education.message}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="languages">Languages Spoken (Comma Separated)</Label>
              <Input 
                id="languages" 
                placeholder="e.g. English, Hindi, Spanish" 
                {...register('languages')} 
              />
              {errors.languages && <p className="text-xs text-rose-500">{errors.languages.message}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="bio">Professional Biography (Min 10 characters)</Label>
              <textarea 
                id="bio" 
                rows={4}
                placeholder="Briefly describe your medical journey, clinical interests, and consultations philosophy..." 
                className="flex w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-teal-600 disabled:cursor-not-allowed disabled:opacity-50"
                {...register('bio')} 
              />
              {errors.bio && <p className="text-xs text-rose-500">{errors.bio.message}</p>}
            </div>
          </div>
        )}

        {/* STEP 3: Verification Documents URLs */}
        {currentStep === 3 && (
          <div className="space-y-4">
            <h2 className="text-lg font-bold text-slate-800 border-b pb-2 flex items-center gap-2">
              <FileText className="h-5 w-5 text-teal-600" />
              Verification Documents
            </h2>
            <p className="text-xs text-slate-500 bg-slate-50 p-3 rounded-lg">
              * Store metadata only. Upload verification documents to a secure public storage bucket (e.g. Supabase, Dropbox) and provide the direct download links below.
            </p>

            <div className="space-y-3">
              <div className="space-y-2">
                <Label htmlFor="degree_certificate_url">Degree Certificate URL</Label>
                <Input 
                  id="degree_certificate_url" 
                  placeholder="https://example.com/degree.pdf" 
                  {...register('degree_certificate_url')} 
                />
                {errors.degree_certificate_url && <p className="text-xs text-rose-500">{errors.degree_certificate_url.message}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="medical_license_url">Medical License Document URL</Label>
                <Input 
                  id="medical_license_url" 
                  placeholder="https://example.com/license.pdf" 
                  {...register('medical_license_url')} 
                />
                {errors.medical_license_url && <p className="text-xs text-rose-500">{errors.medical_license_url.message}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="identity_proof_url">Identity Proof URL (Aadhaar, Passport, etc.)</Label>
                <Input 
                  id="identity_proof_url" 
                  placeholder="https://example.com/passport.pdf" 
                  {...register('identity_proof_url')} 
                />
                {errors.identity_proof_url && <p className="text-xs text-rose-500">{errors.identity_proof_url.message}</p>}
              </div>
            </div>
          </div>
        )}

        {/* Navigation Buttons */}
        <div className="flex justify-between items-center pt-4 border-t">
          {currentStep > 1 ? (
            <Button type="button" onClick={handlePrevStep} variant="outline" className="border-slate-200">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Previous
            </Button>
          ) : (
            <div />
          )}

          {currentStep < 3 ? (
            <Button type="button" onClick={handleNextStep} className="bg-teal-600 hover:bg-teal-700 text-white">
              Next Step
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          ) : (
            <div className="flex gap-2">
              {application && (
                <Button 
                  type="button" 
                  onClick={() => setIsEditing(false)} 
                  variant="outline" 
                  className="border-slate-200"
                >
                  Cancel
                </Button>
              )}
              <Button 
                type="submit" 
                disabled={applyMutation.isPending || updateMutation.isPending || !isValid} 
                className="bg-teal-600 hover:bg-teal-700 text-white"
              >
                {(applyMutation.isPending || updateMutation.isPending) && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                <Check className="mr-2 h-4 w-4" />
                {application ? 'Update Application' : 'Submit Application'}
              </Button>
            </div>
          )}
        </div>
      </form>
    </div>
  )
}
