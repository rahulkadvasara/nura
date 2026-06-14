// Common Types

export interface ApiResponse<T = any> {
  success: boolean
  message: string
  data?: T
  errors?: string[]
}

export interface PaginatedResponse<T = any> extends ApiResponse<T[]> {
  pagination: {
    page: number
    limit: number
    total: number
    pages: number
  }
}

// User Types
export interface User {
  id: string
  role: 'patient' | 'doctor' | 'admin'
  email: string
  full_name: string
  phone?: string
  profile_picture?: string
  auth_provider: 'local' | 'google'
  email_verified: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

// Health Types
export interface HealthStatus {
  status: string
  app: string
  environment: string
  mongodb: string
  qdrant: string
}