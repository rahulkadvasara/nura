import { apiClient } from '@/lib/axios'
import { ApiResponse } from '@/types'

export interface Reminder {
  id: string
  patient_id: string
  reminder_type: 'medication' | 'appointment' | 'custom'
  title: string
  description?: string
  scheduled_time: string
  recurrence?: string
  status: 'active' | 'completed' | 'dismissed'
  source_type: 'manual' | 'auto'
  source_id?: string
  created_at: string
  updated_at: string
}

export interface ReminderCreateRequest {
  patient_id: string
  reminder_type: 'medication' | 'appointment' | 'custom'
  title: string
  description?: string
  scheduled_time: string
  recurrence?: string
  status?: 'active' | 'completed' | 'dismissed'
  source_type?: 'manual' | 'auto'
  source_id?: string
  override?: boolean
  override_reason?: string
}

export interface ReminderUpdateRequest {
  patient_id?: string
  reminder_type?: 'medication' | 'appointment' | 'custom'
  title?: string
  description?: string
  scheduled_time?: string
  recurrence?: string
  status?: 'active' | 'completed' | 'dismissed'
  source_type?: 'manual' | 'auto'
  source_id?: string
  override?: boolean
  override_reason?: string
}

export const reminderService = {
  getReminders: async (): Promise<ApiResponse<Reminder[]>> => {
    const response = await apiClient.get<ApiResponse<Reminder[]>>('/patient/reminders')
    return response.data
  },

  createReminder: async (request: ReminderCreateRequest): Promise<ApiResponse<Reminder>> => {
    const response = await apiClient.post<ApiResponse<Reminder>>('/patient/reminders', request)
    return response.data
  },

  updateReminder: async (reminderId: string, request: ReminderUpdateRequest): Promise<ApiResponse<Reminder>> => {
    const response = await apiClient.put<ApiResponse<Reminder>>(`/patient/reminders/${reminderId}`, request)
    return response.data
  },

  deleteReminder: async (reminderId: string): Promise<ApiResponse<void>> => {
    const response = await apiClient.delete<ApiResponse<void>>(`/patient/reminders/${reminderId}`)
    return response.data
  },
}
