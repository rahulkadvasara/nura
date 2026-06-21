'use client'

import { useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { useMutation } from '@tanstack/react-query'
import { authService, ResetPasswordPayload } from '@/services/auth.service'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

const resetPasswordSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  otp: z.string().length(6, 'OTP must be exactly 6 characters'),
  new_password: z.string().min(8, 'Password must be at least 8 characters'),
  confirm_password: z.string()
}).refine((data) => data.new_password === data.confirm_password, {
  message: "Passwords don't match",
  path: ["confirm_password"],
})

type ResetPasswordFormValues = z.infer<typeof resetPasswordSchema>

export default function ResetPasswordPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const emailQuery = searchParams?.get('email') || ''

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordFormValues>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      email: emailQuery,
      otp: '',
    }
  })

  const resetMutation = useMutation({
    mutationFn: authService.resetPassword,
    onSuccess: (data) => {
      if (data.success) {
        toast.success(data.message || 'Password reset successfully')
        router.push('/auth/login')
      } else {
        toast.error(data.message || 'Password reset failed')
      }
    },
    onError: (error: any) => {
      toast.error(error?.message || 'Password reset failed. Please try again.')
    },
    onSettled: () => {
      setIsSubmitting(false)
    }
  })

  const onSubmit = (data: ResetPasswordFormValues) => {
    setIsSubmitting(true)
    resetMutation.mutate({
      email: data.email,
      otp: data.otp,
      new_password: data.new_password
    })
  }

  return (
    <>
      <div className="text-center">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
          Create new password
        </h1>
        <p className="text-sm text-muted-foreground mt-2">
          Your new password must be different from previous used passwords.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 mt-6">
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            placeholder="name@example.com"
            disabled={isSubmitting || !!emailQuery}
            {...register('email')}
          />
          {errors.email && (
            <p className="text-xs text-destructive">{errors.email.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="otp">Security Code (OTP)</Label>
          <Input
            id="otp"
            type="text"
            placeholder="123456"
            maxLength={6}
            disabled={isSubmitting}
            {...register('otp')}
          />
          {errors.otp && (
            <p className="text-xs text-destructive">{errors.otp.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="new_password">New Password</Label>
          <Input
            id="new_password"
            type="password"
            disabled={isSubmitting}
            {...register('new_password')}
          />
          {errors.new_password && (
            <p className="text-xs text-destructive">{errors.new_password.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="confirm_password">Confirm Password</Label>
          <Input
            id="confirm_password"
            type="password"
            disabled={isSubmitting}
            {...register('confirm_password')}
          />
          {errors.confirm_password && (
            <p className="text-xs text-destructive">{errors.confirm_password.message}</p>
          )}
        </div>

        <Button className="w-full" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Resetting password...' : 'Reset Password'}
        </Button>
      </form>

      <div className="mt-4 text-center text-sm">
        <Link href="/auth/login" className="text-primary hover:underline font-medium">
          Back to sign in
        </Link>
      </div>
    </>
  )
}
