'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { useMutation } from '@tanstack/react-query'
import { authService, VerifyOtpPayload } from '@/services/auth.service'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

const verifyOtpSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  otp: z.string().length(6, 'OTP must be exactly 6 characters'),
})

export default function VerifyOtpPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [countdown, setCountdown] = useState(60)

  const emailQuery = searchParams?.get('email') || ''

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<VerifyOtpPayload>({
    resolver: zodResolver(verifyOtpSchema),
    defaultValues: {
      email: emailQuery,
      otp: '',
    }
  })

  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000)
      return () => clearTimeout(timer)
    }
  }, [countdown])

  const verifyMutation = useMutation({
    mutationFn: authService.verifyOTP,
    onSuccess: (data) => {
      if (data.success) {
        toast.success(data.message || 'Account verified successfully')
        router.push('/auth/login')
      } else {
        toast.error(data.message || 'Verification failed')
      }
    },
    onError: (error: any) => {
      toast.error(error?.message || 'Invalid OTP. Please try again.')
    },
    onSettled: () => {
      setIsSubmitting(false)
    }
  })

  const onSubmit = (data: VerifyOtpPayload) => {
    setIsSubmitting(true)
    verifyMutation.mutate(data)
  }

  const handleResend = () => {
    if (countdown === 0) {
      setCountdown(60)
      toast.success('A new OTP has been sent to your email')
      // In a real app, this would call authService.resendOTP(emailQuery)
    }
  }

  return (
    <>
      <div className="text-center">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
          Verify your email
        </h1>
        <p className="text-sm text-muted-foreground mt-2">
          Enter the 6-digit code we sent to your email
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 mt-6">
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            disabled={true}
            {...register('email')}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="otp">Security Code</Label>
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

        <Button className="w-full" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Verifying...' : 'Verify Account'}
        </Button>
      </form>

      <div className="mt-4 text-center text-sm">
        Didn&apos;t receive a code?{' '}
        <button 
          onClick={handleResend}
          disabled={countdown > 0}
          className={`font-medium ${countdown > 0 ? 'text-slate-400 cursor-not-allowed' : 'text-primary hover:underline'}`}
        >
          {countdown > 0 ? `Resend code in ${countdown}s` : 'Resend code'}
        </button>
      </div>
    </>
  )
}
