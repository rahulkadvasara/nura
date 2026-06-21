'use client'

import { useRouter } from 'next/navigation'
import { GoogleLogin, CredentialResponse } from '@react-oauth/google'
import { useMutation } from '@tanstack/react-query'
import { authService } from '@/services/auth.service'
import { useAuthStore } from '@/stores/auth'
import { toast } from 'sonner'

export function GoogleAuthButton() {
  const router = useRouter()
  const { login } = useAuthStore()

  const googleMutation = useMutation({
    mutationFn: authService.googleLogin,
    onSuccess: (data) => {
      if (data.success && data.data) {
        login(data.data.user, data.data.access_token, data.data.refresh_token)
        toast.success('Successfully signed in with Google')
        router.push('/dashboard')
      } else {
        toast.error(data.message || 'Google sign-in failed')
      }
    },
    onError: (error: any) => {
      toast.error(error?.message || 'Google sign-in failed. Please try again.')
    }
  })

  const handleSuccess = (credentialResponse: CredentialResponse) => {
    if (credentialResponse.credential) {
      googleMutation.mutate({ id_token: credentialResponse.credential })
    }
  }

  const handleError = () => {
    toast.error('Google sign-in was unsuccessful or cancelled.')
  }

  return (
    <div className="flex justify-center w-full">
      <GoogleLogin
        onSuccess={handleSuccess}
        onError={handleError}
        theme="outline"
        size="large"
        width="100%"
        text="continue_with"
      />
    </div>
  )
}
