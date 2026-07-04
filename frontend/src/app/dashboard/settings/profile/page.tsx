'use client'

import { useState, useEffect, useRef } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { useAuthStore } from '@/stores/auth'
import { userService } from '@/services/user.service'
import { apiClient } from '@/lib/axios'
import { Camera, Trash2, Loader2, Edit3, X } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

const profileSchema = z.object({
  full_name: z.string().min(2, 'Name must be at least 2 characters'),
  phone: z.string().optional().nullable(),
})

type ProfileFormValues = z.infer<typeof profileSchema>

export default function ProfileSettingsPage() {
  const { user, setUser } = useAuthStore()
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null)
  const [avatarFile, setAvatarFile] = useState<File | null>(null)
  const [shouldRemoveAvatar, setShouldRemoveAvatar] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  const { data: profileData, isLoading } = useQuery({
    queryKey: ['userProfile'],
    queryFn: userService.getProfile,
  })

  const form = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      full_name: '',
      phone: '',
    },
  })

  // Initialize preview and form data from API or auth store
  const resetFormState = () => {
    if (profileData) {
      form.reset({
        full_name: profileData.full_name || '',
        phone: profileData.phone || '',
      })
      setAvatarPreview(profileData.profile_picture || null)
    } else if (user) {
      form.reset({
        full_name: user.full_name || '',
        phone: user.phone || '',
      })
      setAvatarPreview(user.profile_picture || null)
    }
    setAvatarFile(null)
    setShouldRemoveAvatar(false)
  }

  useEffect(() => {
    resetFormState()
  }, [profileData, user])

  const handleCancel = () => {
    resetFormState()
    setIsEditing(false)
  }

  const onSubmit = async (data: ProfileFormValues) => {
    try {
      setIsSaving(true)
      let currentUser = user

      // 1. Perform avatar deletion if marked for removal
      if (shouldRemoveAvatar) {
        const response = await apiClient.delete('/users/avatar')
        if (response.data) {
          currentUser = response.data
          setUser(currentUser)
        }
      } 
      // 2. Perform avatar upload if a new file was chosen locally
      else if (avatarFile) {
        const formData = new FormData()
        formData.append('file', avatarFile)
        const response = await apiClient.post('/users/avatar', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })
        if (response.data) {
          currentUser = response.data
          setUser(currentUser)
        }
      }

      // 3. Perform fields (Name, Phone) update
      const updatedProfile = await userService.updateProfile({
        full_name: data.full_name,
        phone: data.phone || undefined,
      })

      setUser(updatedProfile)
      queryClient.invalidateQueries({ queryKey: ['userProfile'] })
      toast.success('Profile updated successfully')
      
      setAvatarFile(null)
      setShouldRemoveAvatar(false)
      setIsEditing(false)
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || err?.message || 'Failed to update profile')
    } finally {
      setIsSaving(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validate format
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
    if (!allowedTypes.includes(file.type)) {
      toast.error('Invalid format. Please select a JPG, JPEG, PNG, or WEBP image.')
      return
    }

    // Validate size limit (5MB)
    const maxFileSize = 5 * 1024 * 1024
    if (file.size > maxFileSize) {
      toast.error('File too large. Maximum size allowed is 5MB.')
      return
    }

    setAvatarFile(file)
    setShouldRemoveAvatar(false)

    // Set preview locally
    const reader = new FileReader()
    reader.onloadend = () => {
      setAvatarPreview(reader.result as string)
    }
    reader.readAsDataURL(file)
  }

  const handleRemoveAvatar = () => {
    setShouldRemoveAvatar(true)
    setAvatarFile(null)
    setAvatarPreview(null)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-10">
        <Loader2 className="animate-spin h-8 w-8 text-teal-600" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-medium text-slate-900">Profile Settings</h3>
          <p className="text-sm text-slate-500">
            Update your personal information and how others see you on the platform.
          </p>
        </div>
        {!isEditing && (
          <Button
            type="button"
            onClick={() => setIsEditing(true)}
            className="bg-teal-600 hover:bg-teal-700 text-white font-semibold shadow-sm px-4 py-2 text-xs flex items-center gap-1.5 rounded-lg"
          >
            <Edit3 className="h-4 w-4" />
            Edit Profile
          </Button>
        )}
      </div>
      <div className="border-t border-slate-200"></div>
      
      <div className="space-y-6">
        {/* Avatar Upload Flow */}
        <div className="space-y-2">
          <Label className="text-sm font-semibold text-slate-700">Profile Avatar</Label>
          <div className="flex items-center gap-6 bg-slate-50/50 p-4 rounded-xl border border-slate-100/80">
            <div 
              onClick={() => isEditing && !isSaving && fileInputRef.current?.click()}
              className={`relative group h-20 w-20 rounded-full overflow-hidden border border-slate-200 bg-white flex items-center justify-center shadow-sm transition-all flex-shrink-0 ${
                isEditing ? 'cursor-pointer hover:border-teal-500 hover:ring-1 hover:ring-teal-500' : 'cursor-default'
              }`}
            >
              {avatarPreview ? (
                <img 
                  src={avatarPreview} 
                  alt="Avatar preview" 
                  className="h-full w-full object-cover" 
                />
              ) : (
                <span className="text-xl font-bold text-slate-400">
                  {user?.full_name?.charAt(0).toUpperCase() || 'U'}
                </span>
              )}
              
              {isEditing && (
                <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 flex flex-col items-center justify-center transition-opacity text-white gap-1">
                  <Camera className="h-4.5 w-4.5 text-white" />
                  <span className="text-[9px] font-bold">Edit</span>
                </div>
              )}

              {isSaving && (
                <div className="absolute inset-0 bg-black/50 flex items-center justify-center text-white">
                  <Loader2 className="h-5 w-5 animate-spin text-teal-400" />
                </div>
              )}
            </div>

            {isEditing && (
              <div className="flex flex-col gap-2">
                <input 
                  type="file" 
                  ref={fileInputRef} 
                  onChange={handleFileChange} 
                  accept="image/png, image/jpeg, image/jpg, image/webp" 
                  className="hidden" 
                />
                <div className="flex gap-2.5">
                  <Button 
                    type="button" 
                    variant="outline" 
                    size="sm" 
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isSaving}
                    className="border-slate-200 hover:bg-slate-50 font-semibold text-xs py-1.5 h-8"
                  >
                    Upload Image
                  </Button>
                  {avatarPreview && (
                    <Button 
                      type="button" 
                      variant="outline" 
                      size="sm" 
                      onClick={handleRemoveAvatar}
                      disabled={isSaving}
                      className="border-rose-100 text-rose-600 hover:bg-rose-50 hover:border-rose-200 font-semibold text-xs py-1.5 h-8 flex items-center gap-1"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      Remove
                    </Button>
                  )}
                </div>
                <p className="text-[11px] text-slate-400 font-medium">
                  PNG, JPG, JPEG or WEBP. Max size 5MB.
                </p>
              </div>
            )}
            {!isEditing && (
              <div className="text-xs text-slate-400">
                Click <span className="font-semibold text-slate-600">Edit Profile</span> to modify your avatar or info.
              </div>
            )}
          </div>
        </div>

        {/* Info Form */}
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="email">Email Address</Label>
            <Input 
              id="email" 
              type="email" 
              value={profileData?.email || user?.email || ''} 
              disabled 
              className="bg-slate-550 text-slate-500 border-slate-200 bg-slate-50/80 cursor-not-allowed"
            />
            <p className="text-[0.75rem] text-slate-400 font-medium">
              Your email address is verified and used for account security. It cannot be altered.
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="full_name">Full Name</Label>
            <Input 
              id="full_name" 
              placeholder="Your full name" 
              {...form.register('full_name')} 
              disabled={!isEditing || isSaving}
              className={`border-slate-200 focus:border-teal-500 focus:ring-teal-500 ${
                !isEditing ? 'bg-slate-50/50 cursor-not-allowed text-slate-600' : ''
              }`}
            />
            {form.formState.errors.full_name && (
              <p className="text-xs text-rose-500 font-semibold">{form.formState.errors.full_name.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="phone">Phone Number</Label>
            <Input 
              id="phone" 
              type="tel"
              placeholder="+91 99999 99999" 
              {...form.register('phone')} 
              disabled={!isEditing || isSaving}
              className={`border-slate-200 focus:border-teal-500 focus:ring-teal-500 ${
                !isEditing ? 'bg-slate-50/50 cursor-not-allowed text-slate-600' : ''
              }`}
            />
            {form.formState.errors.phone && (
              <p className="text-xs text-rose-500 font-semibold">{form.formState.errors.phone.message}</p>
            )}
          </div>

          {isEditing && (
            <div className="flex items-center gap-3 pt-2">
              <Button 
                type="submit" 
                disabled={isSaving || (!form.formState.isDirty && !avatarFile && !shouldRemoveAvatar)}
                className="bg-teal-600 hover:bg-teal-700 text-white font-semibold shadow-sm px-5"
              >

                {isSaving ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  'Save Changes'
                )}
              </Button>
              <Button 
                type="button" 
                variant="outline"
                onClick={handleCancel}
                disabled={isSaving}
                className="border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold shadow-sm px-5"
              >
                Cancel
              </Button>
            </div>
          )}
        </form>
      </div>
    </div>
  )
}
