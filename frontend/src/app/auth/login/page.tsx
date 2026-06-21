'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { useMutation } from '@tanstack/react-query'
import { authService, LoginPayload } from '@/services/auth.service'
import { useAuthStore } from '@/stores/auth'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { GoogleAuthButton } from '@/components/auth/GoogleAuthButton'

const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
})

export default function LoginPage() {
  const router = useRouter()
  const { login } = useAuthStore()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginPayload>({
    resolver: zodResolver(loginSchema),
  })

  const loginMutation = useMutation({
    mutationFn: authService.login,
    onSuccess: (data) => {
      // API_CONTRACT states data returns { access_token, refresh_token, user }
      if (data.success && data.data) {
        login(data.data.user, data.data.access_token, data.data.refresh_token)
        toast.success('Logged in successfully')
        router.push('/dashboard')
      } else {
        toast.error(data.message || 'Login failed')
      }
    },
    onError: (error: any) => {
      toast.error(error?.message || 'Invalid credentials')
    },
    onSettled: () => {
      setIsSubmitting(false)
    }
  })

  const onSubmit = (data: LoginPayload) => {
    setIsSubmitting(true)
    loginMutation.mutate(data)
  }

  return (
    <>
      <div className="text-center">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
          Welcome back
        </h1>
        <p className="text-sm text-muted-foreground mt-2">
          Enter your email to sign in to your account
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

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="password">Password</Label>
            <Link
              href="/auth/forgot-password"
              className="text-xs text-primary hover:underline"
            >
              Forgot password?
            </Link>
          </div>
          <Input
            id="password"
            type="password"
            disabled={isSubmitting}
            {...register('password')}
          />
          {errors.password && (
            <p className="text-xs text-destructive">{errors.password.message}</p>
          )}
        </div>

        <Button className="w-full" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Signing in...' : 'Sign In'}
        </Button>
      </form>

      <div className="mt-6">
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <span className="w-full border-t border-slate-200" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-white px-2 text-muted-foreground">
              Or continue with
            </span>
          </div>
        </div>
        
        <div className="mt-6 flex justify-center w-full">
          <GoogleAuthButton />
        </div>
      </div>

      <div className="mt-6 text-center text-sm">
        Don&apos;t have an account?{' '}
        <Link href="/auth/register" className="text-primary hover:underline font-medium">
          Sign up
        </Link>
      </div>
    </>
  )
}
