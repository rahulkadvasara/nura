import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { reminderService, Reminder, ReminderCreateRequest, ReminderUpdateRequest } from '@/services/reminder.service'

export function usePatientReminders() {
  return useQuery<Reminder[], Error>({
    queryKey: ['patient', 'reminders'],
    queryFn: async () => {
      const response = await reminderService.getReminders()
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch reminders')
    },
    staleTime: 5000,
  })
}

export function useCreateReminder() {
  const queryClient = useQueryClient()
  return useMutation<Reminder, Error, ReminderCreateRequest>({
    mutationFn: async (request: ReminderCreateRequest) => {
      const response = await reminderService.createReminder(request)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to create reminder')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patient', 'reminders'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'patient'] })
    },
  })
}

export function useUpdateReminder() {
  const queryClient = useQueryClient()
  return useMutation<Reminder, Error, { reminderId: string; request: ReminderUpdateRequest }>({
    mutationFn: async ({ reminderId, request }) => {
      const response = await reminderService.updateReminder(reminderId, request)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to update reminder')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patient', 'reminders'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'patient'] })
    },
  })
}

export function useDeleteReminder() {
  const queryClient = useQueryClient()
  return useMutation<void, Error, string>({
    mutationFn: async (reminderId: string) => {
      const response = await reminderService.deleteReminder(reminderId)
      if (!response.success) {
        throw new Error(response.message || 'Failed to delete reminder')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patient', 'reminders'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'patient'] })
    },
  })
}
