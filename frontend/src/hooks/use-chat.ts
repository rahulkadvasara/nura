import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  chatService,
  ChatSession,
  ChatMessage,
  ChatHistory,
  ChatStatistics,
  ChatExecutionResponse,
  ChatSessionStatisticsResponse,
  CitationInfo,
  ConversationEvaluationResponse,
  MemoryUpdateResponse,
  SessionMemoryDetail,
  MemoryStatisticsResponse,
  SearchHit,
  Bookmark
} from '@/services/chat.service'

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

export function useRegenerateMessage() {
  const queryClient = useQueryClient()
  return useMutation<
    ChatExecutionResponse,
    Error,
    { sessionId: string }
  >({
    mutationFn: async ({ sessionId }) => {
      const response = await chatService.regenerateMessage(sessionId)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Regeneration failed')
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['chat', 'messages', variables.sessionId] })
      queryClient.invalidateQueries({ queryKey: ['chat', 'session', variables.sessionId] })
      queryClient.invalidateQueries({ queryKey: ['chat', 'sessions'] })
      queryClient.invalidateQueries({ queryKey: ['chat', 'session-statistics', variables.sessionId] })
    }
  })
}

export function useSubmitFeedback() {
  return useMutation<
    { success: boolean; message: string },
    Error,
    { messageId: string; rating: 'helpful' | 'unhelpful'; comment?: string }
  >({
    mutationFn: async ({ messageId, rating, comment }) => {
      const response = await chatService.submitFeedback(messageId, rating, comment)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Feedback submission failed')
    }
  })
}

export function useMessageCitations(messageId: string | null) {
  return useQuery<CitationInfo[], Error>({
    queryKey: ['chat', 'citations', messageId],
    queryFn: async () => {
      if (!messageId) return []
      const response = await chatService.getMessageCitations(messageId)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch citations')
    },
    enabled: !!messageId,
    staleTime: 60000,
  })
}

export function useFollowupQuestions(messageId: string | null) {
  return useQuery<string[], Error>({
    queryKey: ['chat', 'followups', messageId],
    queryFn: async () => {
      if (!messageId) return []
      const response = await chatService.getFollowupQuestions(messageId)
      if (response.success && response.data) {
        return response.data.questions
      }
      throw new Error(response.message || 'Failed to fetch follow-ups')
    },
    enabled: !!messageId,
    staleTime: 60000,
  })
}

export function useEvaluateMemory() {
  return useMutation<
    ConversationEvaluationResponse,
    Error,
    { sessionId: string }
  >({
    mutationFn: async ({ sessionId }) => {
      const response = await chatService.evaluateMemory(sessionId)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Evaluation failed')
    }
  })
}

export function useForceMemorySync() {
  const queryClient = useQueryClient()
  return useMutation<
    MemoryUpdateResponse,
    Error,
    { sessionId: string }
  >({
    mutationFn: async ({ sessionId }) => {
      const response = await chatService.forceMemorySync(sessionId)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Synchronization failed')
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['chat', 'session-memory', variables.sessionId] })
      queryClient.invalidateQueries({ queryKey: ['chat', 'memory-statistics'] })
    }
  })
}

export function useMemoryStatistics() {
  return useQuery<MemoryStatisticsResponse, Error>({
    queryKey: ['chat', 'memory-statistics'],
    queryFn: async () => {
      const response = await chatService.getMemoryStatistics()
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch memory statistics')
    },
    staleTime: 10000
  })
}

export function useSessionMemory(sessionId: string | null) {
  return useQuery<SessionMemoryDetail[], Error>({
    queryKey: ['chat', 'session-memory', sessionId],
    queryFn: async () => {
      if (!sessionId) return []
      const response = await chatService.getSessionMemory(sessionId)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch session memories')
    },
    enabled: !!sessionId,
    staleTime: 10000
  })
}

export function useSearchConversations(params: {
  query: string
  session_id?: string
  date_from?: string
  date_to?: string
  favorites?: boolean
  archived?: boolean
  agent?: string
}, enabled = false) {
  return useQuery<SearchHit[], Error>({
    queryKey: ['chat', 'search', params],
    queryFn: async () => {
      if (!params.query) return []
      const response = await chatService.searchConversations(params)
      if (response.success && response.data) {
        return response.data.results
      }
      throw new Error(response.message || 'Search failed')
    },
    enabled: enabled && !!params.query,
    staleTime: 2000
  })
}

export function useExportConversation() {
  return useMutation<Blob, Error, { sessionId: string; format: 'md' | 'pdf' | 'json' }>({
    mutationFn: async ({ sessionId, format }) => {
      return await chatService.exportConversation(sessionId, format)
    }
  })
}

export function useBookmarkMessage() {
  const queryClient = useQueryClient()
  return useMutation<Bookmark, Error, string>({
    mutationFn: async (messageId: string) => {
      const response = await chatService.bookmarkMessage(messageId)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to bookmark message')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat', 'bookmarks'] })
      queryClient.invalidateQueries({ queryKey: ['chat', 'messages'] })
    }
  })
}

export function useRemoveBookmark() {
  const queryClient = useQueryClient()
  return useMutation<{ deleted: boolean }, Error, string>({
    mutationFn: async (messageId: string) => {
      const response = await chatService.removeBookmark(messageId)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to remove bookmark')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat', 'bookmarks'] })
      queryClient.invalidateQueries({ queryKey: ['chat', 'messages'] })
    }
  })
}

export function useBookmarks() {
  return useQuery<Bookmark[], Error>({
    queryKey: ['chat', 'bookmarks'],
    queryFn: async () => {
      const response = await chatService.getBookmarks()
      if (response.success && response.data) {
        return response.data.bookmarks
      }
      throw new Error(response.message || 'Failed to fetch bookmarks')
    },
    staleTime: 5000
  })
}

export function useChatHealth() {
  return useQuery({
    queryKey: ['chat', 'health'],
    queryFn: async () => {
      const response = await chatService.getHealth()
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch health status')
    },
    refetchInterval: 10000
  })
}

export function useChatAdminStatistics() {
  return useQuery({
    queryKey: ['chat', 'admin-statistics'],
    queryFn: async () => {
      const response = await chatService.getStatistics()
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch statistics')
    },
    refetchInterval: 10000
  })
}

export function useChatCacheStats() {
  return useQuery({
    queryKey: ['chat', 'cache-stats'],
    queryFn: async () => {
      const response = await chatService.getCacheStats()
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch cache stats')
    },
    refetchInterval: 10000
  })
}

export function useChatPerformance() {
  return useQuery({
    queryKey: ['chat', 'performance'],
    queryFn: async () => {
      const response = await chatService.getPerformance()
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch performance metrics')
    },
    refetchInterval: 10000
  })
}

export function useChatStreamingStats() {
  return useQuery({
    queryKey: ['chat', 'streaming-stats'],
    queryFn: async () => {
      const response = await chatService.getStreamingStats()
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch streaming stats')
    },
    refetchInterval: 10000
  })
}


