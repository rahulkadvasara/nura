import { apiClient } from '@/lib/axios'
import { ApiResponse } from '@/types'

export interface ChatSession {
  id: string
  patient_id: string
  title: string
  description?: string
  status: 'ACTIVE' | 'ARCHIVED' | 'DELETED'
  session_type: string
  active: boolean
  last_message_at: string
  message_count: number
  total_tokens: number
  total_cost: number
  last_agent_used?: string
  pinned: boolean
  archived: boolean
  metadata: Record<string, any>
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  id: string
  session_id: string
  patient_id: string
  role: 'USER' | 'ASSISTANT' | 'SYSTEM'
  content: string
  citations: any[]
  attachments: any[]
  token_usage: Record<string, number>
  latency_ms?: number
  metadata: Record<string, any>
  created_at: string
  edited_at?: string
  deleted: boolean
}

export interface ChatHistory {
  messages: ChatMessage[]
  total: number
  limit: number
  skip: number
}

export interface ChatStatistics {
  sessions_created: number
  sessions_archived: number
  sessions_deleted: number
  messages_created: number
  messages_edited: number
  messages_deleted: number
  average_messages_per_session: number
}

export interface ChatExecutionResponse {
  assistant_message: string
  agent_used?: string
  citations: any[]
  usage: Record<string, number>
  latency_ms: number
  cost: number
}

export interface ChatSessionStatisticsResponse {
  message_count: number
  total_tokens: number
  total_cost: number
  average_latency: number
  last_agent_used?: string
}

export const chatService = {
  createSession: async (patientId: string, title: string, description?: string): Promise<ApiResponse<ChatSession>> => {
    const response = await apiClient.post<ApiResponse<ChatSession>>('/chat/session', {
      patient_id: patientId,
      title,
      description
    })
    return response.data
  },

  listSessions: async (limit: number = 20, skip: number = 0, includeArchived: boolean = true): Promise<ApiResponse<{ sessions: ChatSession[]; limit: number; skip: number }>> => {
    const response = await apiClient.get<ApiResponse<{ sessions: ChatSession[]; limit: number; skip: number }>>('/chat/sessions', {
      params: { limit, skip, include_archived: includeArchived }
    })
    return response.data
  },

  getSession: async (sessionId: string): Promise<ApiResponse<ChatSession>> => {
    const response = await apiClient.get<ApiResponse<ChatSession>>(`/chat/session/${sessionId}`)
    return response.data
  },

  updateSession: async (
    sessionId: string, 
    payload: { title?: string; pinned?: boolean; archived?: boolean; description?: string }
  ): Promise<ApiResponse<ChatSession>> => {
    const response = await apiClient.patch<ApiResponse<ChatSession>>(`/chat/session/${sessionId}`, payload)
    return response.data
  },

  deleteSession: async (sessionId: string): Promise<ApiResponse<void>> => {
    const response = await apiClient.delete<ApiResponse<void>>(`/chat/session/${sessionId}`)
    return response.data
  },

  getMessages: async (sessionId: string, limit: number = 50, skip: number = 0): Promise<ApiResponse<ChatHistory>> => {
    const response = await apiClient.get<ApiResponse<ChatHistory>>(`/chat/messages/${sessionId}`, {
      params: { limit, skip }
    })
    return response.data
  },

  createMessage: async (payload: {
    session_id: string
    patient_id: string
    role: 'USER' | 'ASSISTANT' | 'SYSTEM'
    content: string
    citations?: any[]
    attachments?: any[]
    token_usage?: Record<string, number>
    latency_ms?: number
    metadata?: Record<string, any>
  }): Promise<ApiResponse<ChatMessage>> => {
    const response = await apiClient.post<ApiResponse<ChatMessage>>('/chat/message', payload)
    return response.data
  },

  getChatStatistics: async (): Promise<ApiResponse<ChatStatistics>> => {
    const response = await apiClient.get<ApiResponse<ChatStatistics>>('/chat/statistics')
    return response.data
  },

  executeMessage: async (sessionId: string, message: string): Promise<ApiResponse<ChatExecutionResponse>> => {
    const response = await apiClient.post<ApiResponse<ChatExecutionResponse>>('/chat/message/execute', {
      session_id: sessionId,
      message
    })
    return response.data
  },

  getSessionStatistics: async (sessionId: string): Promise<ApiResponse<ChatSessionStatisticsResponse>> => {
    const response = await apiClient.get<ApiResponse<ChatSessionStatisticsResponse>>(`/chat/session/${sessionId}/statistics`)
    return response.data
  },

  regenerateMessage: async (sessionId: string): Promise<ApiResponse<ChatExecutionResponse>> => {
    const response = await apiClient.post<ApiResponse<ChatExecutionResponse>>('/chat/message/regenerate', {
      session_id: sessionId
    })
    return response.data
  },

  submitFeedback: async (messageId: string, rating: 'helpful' | 'unhelpful', comment?: string): Promise<ApiResponse<{ success: boolean; message: string }>> => {
    const response = await apiClient.post<ApiResponse<{ success: boolean; message: string }>>('/chat/message/feedback', {
      message_id: messageId,
      rating,
      comment
    })
    return response.data
  },

  getMessageCitations: async (messageId: string): Promise<ApiResponse<CitationInfo[]>> => {
    const response = await apiClient.get<ApiResponse<CitationInfo[]>>(`/chat/message/${messageId}/citations`)
    return response.data
  },

  getFollowupQuestions: async (messageId: string): Promise<ApiResponse<{ questions: string[] }>> => {
    const response = await apiClient.get<ApiResponse<{ questions: string[] }>>(`/chat/message/${messageId}/followups`)
    return response.data
  }
}

export interface CitationInfo {
  document: string
  source: string
  page?: number
  section?: string
  confidence?: number
}

