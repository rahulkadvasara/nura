import axios from 'axios'

// Base API URL configuration
// Local Development Fallback: 'http://localhost:8000/api/v1'
// Production (Render) Fallback: 'https://<YOUR-RENDER-BACKEND-NAME>.onrender.com/api/v1'
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

import { useAuthStore } from '@/stores/auth'

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 || error.response?.status === 403) {
      // Handle unauthorized
      useAuthStore.getState().logout()
      
      // Only redirect if we're in the browser and not already on login
      if (typeof window !== 'undefined' && !window.location.pathname.includes('/auth/login')) {
        window.location.href = '/auth/login'
      }
    }
    
    // Normalize error
    let message = error.response?.data?.message

    if (!message && error.response?.data?.detail) {
      const detail = error.response.data.detail
      if (Array.isArray(detail)) {
        message = detail.map((err: any) => err.msg || err.message).join(', ')
      } else if (typeof detail === 'string') {
        message = detail
      }
    }

    if (!message) {
      message = error.message || 'An unexpected error occurred'
    }

    const normalizedError: any = new Error(message)
    normalizedError.status = error.response?.status
    normalizedError.data = error.response?.data
    normalizedError.errors = error.response?.data?.errors || error.response?.data?.detail
    
    return Promise.reject(normalizedError)
  }
)

export default apiClient