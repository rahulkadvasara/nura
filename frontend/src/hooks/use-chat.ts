import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { chatService, ChatSession, ChatMessage, ChatHistory, ChatStatistics, ChatExecutionResponse, ChatSessionStatisticsResponse } from '@/services/chat.service'

export function useSessions(limit = 50, skip = 0, includeArchived = true) {
  return useQuery<ChatSession[], Error>({
    queryKey: ['chat', 'sessions', { limit, skip, includeArchived }],
    queryFn: async () => {
      const response = await chatService.listSessions(limit, skip, includeArchived)
      if (response.success && response.data) {
        return response.data.sessions
      }
      throw new Error(response.message || 'Failed to fetch chat sessions')
    },
    staleTime: 5000,
  })
}

export function useSession(sessionId: string | null) {
  return useQuery<ChatSession | null, Error>({
    queryKey: ['chat', 'session', sessionId],
    queryFn: async () => {
      if (!sessionId) return null
      const response = await chatService.getSession(sessionId)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch chat session details')
    },
    enabled: !!sessionId,
    staleTime: 5000,
  })
}

export function useMessages(sessionId: string | null, limit = 100, skip = 0) {
  return useQuery<ChatHistory, Error>({
    queryKey: ['chat', 'messages', sessionId, { limit, skip }],
    queryFn: async () => {
      if (!sessionId) return { messages: [], total: 0, limit, skip }
      const response = await chatService.getMessages(sessionId, limit, skip)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch chat history')
    },
    enabled: !!sessionId,
    staleTime: 1000,
  })
}

export function useCreateSession() {
  const queryClient = useQueryClient()
  return useMutation<ChatSession, Error, { patientId: string; title: string; description?: string }>({
    mutationFn: async ({ patientId, title, description }) => {
      const response = await chatService.createSession(patientId, title, description)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to create chat session')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat', 'sessions'] })
    },
  })
}

export function useUpdateSession() {
  const queryClient = useQueryClient()
  return useMutation<
    ChatSession, 
    Error, 
    { sessionId: string; payload: { title?: string; pinned?: boolean; archived?: boolean; description?: string } }
  >({
    mutationFn: async ({ sessionId, payload }) => {
      const response = await chatService.updateSession(sessionId, payload)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to update chat session')
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['chat', 'sessions'] })
      queryClient.invalidateQueries({ queryKey: ['chat', 'session', variables.sessionId] })
    },
  })
}

export function useDeleteSession() {
  const queryClient = useQueryClient()
  return useMutation<void, Error, string>({
    mutationFn: async (sessionId: string) => {
      const response = await chatService.deleteSession(sessionId)
      if (!response.success) {
        throw new Error(response.message || 'Failed to delete chat session')
      }
    },
    onSuccess: (_, sessionId) => {
      queryClient.invalidateQueries({ queryKey: ['chat', 'sessions'] })
      queryClient.invalidateQueries({ queryKey: ['chat', 'session', sessionId] })
    },
  })
}

export function useCreateMessage() {
  const queryClient = useQueryClient()
  return useMutation<
    ChatMessage, 
    Error, 
    {
      session_id: string
      patient_id: string
      role: 'USER' | 'ASSISTANT' | 'SYSTEM'
      content: string
      metadata?: Record<string, any>
    }
  >({
    mutationFn: async (payload) => {
      const response = await chatService.createMessage(payload)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to post message')
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['chat', 'messages', variables.session_id] })
      queryClient.invalidateQueries({ queryKey: ['chat', 'sessions'] })
    },
  })
}

export function useChatStatistics() {
  return useQuery<ChatStatistics, Error>({
    queryKey: ['chat', 'statistics'],
    queryFn: async () => {
      const response = await chatService.getChatStatistics()
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch chat statistics')
    },
    staleTime: 10000,
  })
}

export function useExecuteMessage() {
  const queryClient = useQueryClient()
  return useMutation<
    ChatExecutionResponse,
    Error,
    { sessionId: string; message: string }
  >({
    mutationFn: async ({ sessionId, message }) => {
      const response = await chatService.executeMessage(sessionId, message)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'AI execution failed')
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['chat', 'messages', variables.sessionId] })
      queryClient.invalidateQueries({ queryKey: ['chat', 'session', variables.sessionId] })
      queryClient.invalidateQueries({ queryKey: ['chat', 'sessions'] })
      queryClient.invalidateQueries({ queryKey: ['chat', 'session-statistics', variables.sessionId] })
    }
  })
}

export function useSessionStatistics(sessionId: string | null) {
  return useQuery<ChatSessionStatisticsResponse | null, Error>({
    queryKey: ['chat', 'session-statistics', sessionId],
    queryFn: async () => {
      if (!sessionId) return null
      const response = await chatService.getSessionStatistics(sessionId)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch session statistics')
    },
    enabled: !!sessionId,
    staleTime: 5000,
  })
}
