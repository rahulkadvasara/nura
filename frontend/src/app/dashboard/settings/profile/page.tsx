'use client'

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { useAuthStore } from '@/stores/auth'
import { userService } from '@/services/user.service'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

const profileSchema = z.object({
  full_name: z.string().min(2, 'Name must be at least 2 characters'),
  phone: z.string().optional().nullable(),
  profile_picture: z.string().url('Must be a valid URL').optional().nullable().or(z.literal('')),
})

type ProfileFormValues = z.infer<typeof profileSchema>

export default function ProfileSettingsPage() {
  const { user, setUser } = useAuthStore()
  const queryClient = useQueryClient()
  
  const { data: profileData, isLoading } = useQuery({
    queryKey: ['userProfile'],
    queryFn: userService.getProfile,
  })

  const form = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      full_name: '',
      phone: '',
      profile_picture: '',
    },
  })

  // Update form when data arrives
  useEffect(() => {
    if (profileData) {
      form.reset({
        full_name: profileData.full_name || '',
        phone: profileData.phone || '',
        profile_picture: profileData.profile_picture || '',
      })
    } else if (user) {
      // Fallback to auth store user data initially
      form.reset({
        full_name: user.full_name || '',
        phone: user.phone || '',
        profile_picture: user.profile_picture || '',
      })
    }
  }, [profileData, user, form])

  const updateMutation = useMutation({
    mutationFn: userService.updateProfile,
    onSuccess: (data) => {
      // Update global user store
      setUser(data)
      queryClient.invalidateQueries({ queryKey: ['userProfile'] })
      toast.success('Profile updated successfully')
    },
    onError: (error: any) => {
      toast.error(error?.message || 'Failed to update profile')
    }
  })

  const onSubmit = (data: ProfileFormValues) => {
    // Convert empty string to undefined for optional fields to match Partial<User> type
    const payload = {
      ...data,
      phone: data.phone || undefined,
      profile_picture: data.profile_picture || undefined,
    }
    updateMutation.mutate(payload)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-10">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">Profile</h3>
        <p className="text-sm text-muted-foreground">
          Update your personal information and how others see you on the platform.
        </p>
      </div>
      <div className="border-t border-slate-200"></div>
      
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input 
            id="email" 
            type="email" 
            value={user?.email || ''} 
            disabled 
            className="bg-slate-50 text-slate-500"
          />
          <p className="text-[0.8rem] text-muted-foreground">
            Your email address is used for authentication and cannot be changed here.
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="full_name">Full Name</Label>
          <Input 
            id="full_name" 
            placeholder="John Doe" 
            {...form.register('full_name')} 
          />
          {form.formState.errors.full_name && (
            <p className="text-sm text-destructive">{form.formState.errors.full_name.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="phone">Phone Number</Label>
          <Input 
            id="phone" 
            type="tel"
            placeholder="+1 (555) 000-0000" 
            {...form.register('phone')} 
          />
          {form.formState.errors.phone && (
            <p className="text-sm text-destructive">{form.formState.errors.phone.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="profile_picture">Profile Picture URL</Label>
          <Input 
            id="profile_picture" 
            type="url"
            placeholder="https://example.com/avatar.jpg" 
            {...form.register('profile_picture')} 
          />
          {form.formState.errors.profile_picture && (
            <p className="text-sm text-destructive">{form.formState.errors.profile_picture.message}</p>
          )}
        </div>

        <Button 
          type="submit" 
          disabled={updateMutation.isPending || !form.formState.isDirty}
        >
          {updateMutation.isPending ? 'Saving...' : 'Update profile'}
        </Button>
      </form>
    </div>
  )
}
