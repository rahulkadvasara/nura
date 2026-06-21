import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { User } from '@/types'

interface AuthState {
  user: User | null
  accessToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  
  // Actions
  setUser: (user: User | null) => void
  setAccessToken: (token: string | null) => void
  login: (user: User, accessToken: string, refreshToken: string) => void
  logout: () => void
  clearSession: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: true, // starts loading until hydration completes

      setUser: (user) => set({ user, isAuthenticated: !!user }),
      
      setAccessToken: (token) => {
        if (typeof window !== 'undefined') {
          if (token) {
            localStorage.setItem('access_token', token)
          } else {
            localStorage.removeItem('access_token')
          }
        }
        set({ accessToken: token })
      },
      
      login: (user, accessToken, refreshToken) => {
        if (typeof window !== 'undefined') {
          localStorage.setItem('access_token', accessToken)
          localStorage.setItem('refresh_token', refreshToken)
        }
        set({
          user,
          accessToken,
          isAuthenticated: true,
          isLoading: false
        })
      },
      
      logout: () => {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
        }
        set({
          user: null,
          accessToken: null,
          isAuthenticated: false,
          isLoading: false
        })
      },
      
      clearSession: () => {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
        }
        set({
          user: null,
          accessToken: null,
          isAuthenticated: false,
          isLoading: false
        })
      }
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        // we omit accessToken from zustand persist because it is stored directly in localStorage keys 
        // by the actions, which is what axios expects.
      }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          state.isLoading = false
          // Restore access token from local storage on hydration
          if (typeof window !== 'undefined') {
            const token = localStorage.getItem('access_token')
            if (token) {
              state.setAccessToken(token)
            }
          }
        }
      }
    }
  )
)