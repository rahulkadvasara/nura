'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { useMutation } from '@tanstack/react-query'
import { authService, ForgotPasswordPayload } from '@/services/auth.service'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

const forgotPasswordSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
})

export default function ForgotPasswordPage() {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordPayload>({
    resolver: zodResolver(forgotPasswordSchema),
  })

  const forgotPasswordMutation = useMutation({
    mutationFn: authService.forgotPassword,
    onSuccess: (data) => {
      // Regardless of success/fail internally, we show a generic success message
      // to prevent account enumeration as per requirements.
      setIsSuccess(true)
      toast.success(data.message || 'If an account exists, a reset link has been sent.')
    },
    onError: () => {
      // Still show success to prevent enumeration
      setIsSuccess(true)
      toast.success('If an account exists, a reset link has been sent.')
    },
    onSettled: () => {
      setIsSubmitting(false)
    }
  })

  const onSubmit = (data: ForgotPasswordPayload) => {
    setIsSubmitting(true)
    forgotPasswordMutation.mutate(data)
  }

  if (isSuccess) {
    return (
      <div className="text-center space-y-6">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
          Check your email
        </h1>
        <p className="text-sm text-muted-foreground">
          If an account exists for that email, we have sent password reset instructions.
        </p>
        <div className="pt-4">
          <Link href="/auth/login">
            <Button variant="outline" className="w-full">
              Return to sign in
            </Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <>
      <div className="text-center">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
          Reset password
        </h1>
        <p className="text-sm text-muted-foreground mt-2">
          Enter your email and we&apos;ll send you instructions to reset your password
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 mt-6">
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            placeholder="name@example.com"
            disabled={isSubmitting}
            {...register('email')}
          />
          {errors.email && (
            <p className="text-xs text-destructive">{errors.email.message}</p>
          )}
        </div>

        <Button className="w-full" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Sending instructions...' : 'Send instructions'}
        </Button>
      </form>

      <div className="mt-4 text-center text-sm">
        Remember your password?{' '}
        <Link href="/auth/login" className="text-primary hover:underline font-medium">
          Sign in
        </Link>
      </div>
    </>
  )
}
