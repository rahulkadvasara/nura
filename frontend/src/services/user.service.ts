import apiClient from '@/lib/axios'
import { User } from '@/types'

export interface NotificationPreferences {
  id?: string
  user_id?: string
  email_enabled: boolean
  appointment_enabled: boolean
  reminder_enabled: boolean
  report_enabled: boolean
  marketing_enabled: boolean
}

export const userService = {
  getProfile: async () => {
    const response = await apiClient.get('/users/profile')
    return response.data
  },

  updateProfile: async (data: Partial<User>) => {
    const response = await apiClient.put('/users/profile', data)
    return response.data
  },

  getPreferences: async (): Promise<NotificationPreferences> => {
    const response = await apiClient.get('/users/preferences')
    return response.data
  },

  updatePreferences: async (data: Partial<NotificationPreferences>): Promise<NotificationPreferences> => {
    const response = await apiClient.put('/users/preferences', data)
    return response.data
  }
}
