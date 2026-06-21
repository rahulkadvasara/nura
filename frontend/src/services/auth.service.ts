import { apiClient } from '@/lib/axios'
import { ApiResponse } from '@/types'

// Payload Interfaces
export interface RegisterPayload {
  full_name: string
  email: string
  password: string
}

export interface VerifyOtpPayload {
  email: string
  otp: string
}

export interface LoginPayload {
  email: string
  password: string
}

export interface ForgotPasswordPayload {
  email: string
}

export interface ResetPasswordPayload {
  email: string
  otp: string
  new_password: string
}

export interface GoogleLoginPayload {
  id_token: string
}

export interface RefreshPayload {
  refresh_token: string
}

export interface LogoutPayload {
  refresh_token: string
}

// Service methods
export const authService = {
  async register(data: RegisterPayload): Promise<ApiResponse> {
    const response = await apiClient.post<ApiResponse>('/auth/register', data)
    return response.data
  },

  async verifyOTP(data: VerifyOtpPayload): Promise<ApiResponse> {
    const response = await apiClient.post<ApiResponse>('/auth/verify-otp', data)
    return response.data
  },

  async login(data: LoginPayload): Promise<ApiResponse> {
    const response = await apiClient.post<ApiResponse>('/auth/login', data)
    return response.data
  },

  async refresh(data: RefreshPayload): Promise<ApiResponse> {
    const response = await apiClient.post<ApiResponse>('/auth/refresh', data)
    return response.data
  },

  async logout(data: LogoutPayload): Promise<ApiResponse> {
    const response = await apiClient.post<ApiResponse>('/auth/logout', data)
    return response.data
  },

  async forgotPassword(data: ForgotPasswordPayload): Promise<ApiResponse> {
    const response = await apiClient.post<ApiResponse>('/auth/forgot-password', data)
    return response.data
  },

  async resetPassword(data: ResetPasswordPayload): Promise<ApiResponse> {
    const response = await apiClient.post<ApiResponse>('/auth/reset-password', data)
    return response.data
  },

  async getCurrentUser(): Promise<ApiResponse> {
    const response = await apiClient.get<ApiResponse>('/auth/me')
    return response.data
  },

  async googleLogin(data: GoogleLoginPayload): Promise<ApiResponse> {
    const response = await apiClient.post<ApiResponse>('/auth/google', data)
    return response.data
  }
}
