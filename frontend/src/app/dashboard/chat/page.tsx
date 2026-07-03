'use client'

import React, { useState, useEffect, useRef } from 'react'
import { useAuthStore } from '@/stores/auth'
import {
  useSessions,
  useSession,
  useMessages,
  useCreateSession,
  useUpdateSession,
  useDeleteSession,
  useCreateMessage,
  useSessionStatistics,
  useRegenerateMessage,
  useSubmitFeedback,
} from '@/hooks/use-chat'
import {
  Plus,
  Pin,
  Archive,
  Trash2,
  Edit2,
  Send,
  Sparkles,
  User,
  Activity,
  Check,
  X,
  MessageSquare,
  Search,
  Code,
  DollarSign,
  Cpu,
  ThumbsUp,
  ThumbsDown,
  RotateCcw,
  Square,
  Copy,
  ChevronDown,
  ChevronRight,
  BookOpen,
} from 'lucide-react'
import { toast } from 'react-hot-toast'
import { useQueryClient } from '@tanstack/react-query'

export default function ChatPage() {
  const { user } = useAuthStore()
  const patientId = user?.id || ''
  const queryClient = useQueryClient()

  // Selected session state
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)
  
  // Search session state
  const [searchQuery, setSearchQuery] = useState('')

  // Developer mode toggle
  const [developerMode, setDeveloperMode] = useState(false)

  // New session inline creation toggle and input
  const [isCreating, setIsCreating] = useState(false)
  const [newSessionTitle, setNewSessionTitle] = useState('')

  // Editing session title state
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null)
  const [editTitleValue, setEditTitleValue] = useState('')

  // Message input state
  const [messageText, setMessageText] = useState('')
  const [messageRole, setMessageRole] = useState<'USER' | 'ASSISTANT' | 'SYSTEM'>('USER')

  // Streaming State
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingText, setStreamingText] = useState('')
  const [streamingAgent, setStreamingAgent] = useState('')
  const abortControllerRef = useRef<AbortController | null>(null)

  // Feedback State
  const [activeFeedbackMessageId, setActiveFeedbackMessageId] = useState<string | null>(null)
  const [feedbackRating, setFeedbackRating] = useState<'helpful' | 'unhelpful' | null>(null)
  const [feedbackComment, setFeedbackComment] = useState('')
  const [submittedFeedbacks, setSubmittedFeedbacks] = useState<Record<string, boolean>>({})

  // Expandable citations state
  const [expandedMessageCitationsId, setExpandedMessageCitationsId] = useState<string | null>(null)

  // Auto-scroll ref
  const bottomRef = useRef<HTMLDivElement | null>(null)

  // TanStack hooks
  const { data: sessions = [], isLoading: loadingSessions } = useSessions(100, 0, true)
  const { data: activeSession } = useSession(selectedSessionId)
  const { data: history = { messages: [] }, isLoading: loadingMessages } = useMessages(selectedSessionId)
  const { data: stats } = useSessionStatistics(selectedSessionId)

  const createSessionMutation = useCreateSession()
  const updateSessionMutation = useUpdateSession()
  const deleteSessionMutation = useDeleteSession()
  const createMessageMutation = useCreateMessage()
  const regenerateMutation = useRegenerateMessage()
  const feedbackMutation = useSubmitFeedback()

  // Filter sessions by search query
  const filteredSessions = sessions.filter(session =>
    session.title.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // Scroll to bottom helper
  const scrollToBottom = () => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  // Scroll on streaming changes or message history updates
  useEffect(() => {
    scrollToBottom()
  }, [history.messages, streamingText, isStreaming])

  // Cleanup abortController on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  // Handle session creation
  const handleCreateSession = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newSessionTitle.trim()) return
    if (!patientId) {
      toast.error('Patient identity not loaded. Please log in again.')
      return
    }

    try {
      const newSession = await createSessionMutation.mutateAsync({
        patientId,
        title: newSessionTitle.trim(),
      })
      setSelectedSessionId(newSession.id)
      setNewSessionTitle('')
      setIsCreating(false)
      toast.success('Chat session created')
    } catch (err: any) {
      toast.error(err.message || 'Failed to create session')
    }
  }

  // Handle session rename
  const handleRenameSession = async (sessionId: string) => {
    if (!editTitleValue.trim()) return
    try {
      await updateSessionMutation.mutateAsync({
        sessionId,
        payload: { title: editTitleValue.trim() },
      })
      setEditingSessionId(null)
      toast.success('Session renamed')
    } catch (err: any) {
      toast.error(err.message || 'Failed to rename session')
    }
  }

  // Toggle Pin session
  const handleTogglePin = async (session: any) => {
    try {
      await updateSessionMutation.mutateAsync({
        sessionId: session.id,
        payload: { pinned: !session.pinned },
      })
      toast.success(session.pinned ? 'Session unpinned' : 'Session pinned')
    } catch (err: any) {
      toast.error(err.message || 'Failed to update pin state')
    }
  }

  // Toggle Archive session
  const handleToggleArchive = async (session: any) => {
    try {
      await updateSessionMutation.mutateAsync({
        sessionId: session.id,
        payload: { archived: !session.archived },
      })
      toast.success(session.archived ? 'Session unarchived' : 'Session archived')
    } catch (err: any) {
      toast.error(err.message || 'Failed to archive session')
    }
  }

  // Handle session delete
  const handleDeleteSession = async (sessionId: string) => {
    if (!confirm('Are you sure you want to delete this conversation? This will soft-delete the session.')) return
    try {
      await deleteSessionMutation.mutateAsync(sessionId)
      if (selectedSessionId === sessionId) {
        setSelectedSessionId(null)
      }
      toast.success('Session deleted')
    } catch (err: any) {
      toast.error(err.message || 'Failed to delete session')
    }
  }

  // Trigger streaming message endpoint via Fetch API
  const handleStartMessageStream = async (text: string) => {
    if (!selectedSessionId) return
    setIsStreaming(true)
    setStreamingText('')
    setStreamingAgent('')

    abortControllerRef.current = new AbortController()

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
      const token = localStorage.getItem('access_token')
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(`${baseUrl}/chat/message/stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          session_id: selectedSessionId,
          message: text
        }),
        signal: abortControllerRef.current.signal
      })

      if (!response.ok) {
        throw new Error(`HTTP Error ${response.status}: Failed to initiate stream.`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      if (!reader) {
        throw new Error('Readable stream not supported.')
      }

      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        
        // Retain last incomplete line in buffer
        buffer = lines.pop() || ''

        for (const line of lines) {
          const cleaned = line.trim()
          if (!cleaned.startsWith('data: ')) continue
          
          const rawJson = cleaned.replace(/^data:\s*/, '')
          try {
            const parsed = JSON.parse(rawJson)
            if (parsed.type === 'token') {
              setStreamingText((prev) => prev + parsed.content)
            } else if (parsed.type === 'metadata') {
              if (parsed.agent_used) {
                setStreamingAgent(parsed.agent_used)
              }
            } else if (parsed.type === 'error') {
              toast.error(parsed.error || 'AI pipeline errored')
              setIsStreaming(false)
              return
            }
          } catch (err) {
            console.error('Failed to parse SSE JSON line:', rawJson, err)
          }
        }
      }
    } catch (err: any) {
      if (err.name === 'AbortError') {
        console.info('Generation aborted by the patient.')
      } else {
        toast.error(err.message || 'Streaming failed')
      }
    } finally {
      setIsStreaming(false)
      setStreamingText('')
      setStreamingAgent('')
      // Invalidate message queries to reload complete messages list from server
      queryClient.invalidateQueries({ queryKey: ['chat', 'messages', selectedSessionId] })
      queryClient.invalidateQueries({ queryKey: ['chat', 'session', selectedSessionId] })
      queryClient.invalidateQueries({ queryKey: ['chat', 'sessions'] })
      queryClient.invalidateQueries({ queryKey: ['chat', 'session-statistics', selectedSessionId] })
    }
  }

  // Handle message post
  const handleSendMessage = async (e: React.FormEvent, customText?: string) => {
    if (e) e.preventDefault()
    const textToSend = customText || messageText
    if (!textToSend.trim() || !selectedSessionId) return

    if (!customText) {
      setMessageText('')
    }

    try {
      if (messageRole === 'USER') {
        // Run AI pipeline with Streaming SSE
        await handleStartMessageStream(textToSend.trim())
      } else {
        // Manual simulation fallback
        await createMessageMutation.mutateAsync({
          session_id: selectedSessionId,
          patient_id: patientId,
          role: messageRole,
          content: textToSend.trim(),
        })
        toast.success('Manual message stored')
      }
    } catch (err: any) {
      toast.error(err.message || 'Execution crashed')
    }
  }

  // Stop current streaming execution
  const stopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      setIsStreaming(false)
      toast.success('AI generation stopped')
    }
  }

  // Trigger Response Regeneration
  const handleRegenerate = async () => {
    if (!selectedSessionId) return
    try {
      toast.loading('Regenerating response...', { id: 'regen' })
      await regenerateMutation.mutateAsync({ sessionId: selectedSessionId })
      toast.success('Response regenerated successfully', { id: 'regen' })
    } catch (err: any) {
      toast.error(err.message || 'Regeneration failed', { id: 'regen' })
    }
  }

  // Submit Rating Feedback
  const handleFeedbackSubmit = async (messageId: string) => {
    if (!feedbackRating) return
    try {
      await feedbackMutation.mutateAsync({
        messageId,
        rating: feedbackRating,
        comment: feedbackComment
      })
      setSubmittedFeedbacks((prev) => ({ ...prev, [messageId]: true }))
      setActiveFeedbackMessageId(null)
      setFeedbackComment('')
      setFeedbackRating(null)
      toast.success('Feedback recorded. Thank you!')
    } catch (err: any) {
      toast.error(err.message || 'Feedback submission failed')
    }
  }

  // Helper to copy content to clipboard
  const handleCopyMessage = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success('Copied to clipboard')
  }

  // Extract the latest assistant message ID in session history to compute followups
  const getLastAssistantMessage = () => {
    const list = history.messages || []
    for (let i = list.length - 1; i >= 0; i--) {
      if (list[i].role === 'ASSISTANT' && !list[i].deleted) {
        return list[i]
      }
    }
    return null
  }

  const lastAssistant = getLastAssistantMessage()

  // Standalone premium markdown rendering with code highlighting, tables, headers, and lists
  const renderMarkdown = (text: string) => {
    const lines = text.split('\n')
    let inCodeBlock = false
    let codeBlockContent: string[] = []
    let renderedElements: React.JSX.Element[] = []

    lines.forEach((line, index) => {
      // Code blocks start/end
      if (line.trim().startsWith('```')) {
        if (inCodeBlock) {
          inCodeBlock = false
          const codeText = codeBlockContent.join('\n')
          renderedElements.push(
            <div key={`code-${index}`} className="relative my-2.5 bg-slate-900 text-slate-100 rounded-xl p-3 font-mono text-xs overflow-x-auto border border-slate-800 shadow-inner">
              <button
                type="button"
                onClick={() => handleCopyMessage(codeText)}
                className="absolute right-2.5 top-2.5 p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-all"
                title="Copy code"
              >
                <Copy className="h-3.5 w-3.5" />
              </button>
              <pre className="pr-10">{codeText}</pre>
            </div>
          )
          codeBlockContent = []
        } else {
          inCodeBlock = true
        }
        return
      }

      if (inCodeBlock) {
        codeBlockContent.push(line)
        return
      }

      // Tables renderer
      if (line.trim().startsWith('|')) {
        if (line.includes('---')) return
        const cells = line.split('|').map(c => c.trim()).filter(Boolean)
        renderedElements.push(
          <div key={`table-row-${index}`} className="flex border-b border-slate-100 py-2 px-3 bg-slate-50/50 text-[11px] font-medium text-slate-600 gap-4 hover:bg-slate-100/50 transition-all">
            {cells.map((cell, cidx) => (
              <div key={cidx} className="flex-1 min-w-0 truncate">{cell}</div>
            ))}
          </div>
        )
        return
      }

      // Custom headers
      if (line.startsWith('### ')) {
        renderedElements.push(<h4 key={index} className="text-xs font-bold text-slate-800 mt-3 mb-1.5 flex items-center gap-1.5"><Sparkles className="h-3.5 w-3.5 text-teal-500" />{line.replace('### ', '')}</h4>)
        return
      }
      if (line.startsWith('## ')) {
        renderedElements.push(<h3 key={index} className="text-sm font-extrabold text-slate-800 mt-4 mb-2">{line.replace('## ', '')}</h3>)
        return
      }

      // Lists
      if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
        renderedElements.push(
          <li key={index} className="ml-4 list-disc text-slate-600 my-1 leading-relaxed">
            {line.trim().replace(/^[-*]\s+/, '')}
          </li>
        )
        return
      }

      // Standard paragraphs
      if (line.trim() !== '') {
        renderedElements.push(<p key={index} className="my-1.5 text-slate-600 leading-relaxed">{line}</p>)
      }
    })

    return renderedElements
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl">
      {/* 1. Left Sidebar: Chat Sessions list */}
      <div className="flex w-80 flex-col border-r border-slate-100 bg-slate-50/50">
        {/* Sidebar Header */}
        <div className="p-4 border-b border-slate-100 bg-white">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-teal-600" />
              <span>Conversations</span>
            </h2>
            <button
              onClick={() => setIsCreating(!isCreating)}
              className="p-1.5 rounded-full bg-teal-50 text-teal-700 hover:bg-teal-100 hover:text-teal-800 transition-colors"
              title="New Session"
            >
              <Plus className="h-4 w-4" />
            </button>
          </div>

          {/* New Session form */}
          {isCreating && (
            <form onSubmit={handleCreateSession} className="mb-3 animate-in fade-in slide-in-from-top duration-200">
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="New session title..."
                  value={newSessionTitle}
                  onChange={(e) => setNewSessionTitle(e.target.value)}
                  className="flex-1 px-3 py-1.5 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-teal-500 bg-slate-50"
                  autoFocus
                />
                <button
                  type="submit"
                  className="px-3 py-1 text-xs font-semibold rounded-lg bg-teal-600 text-white hover:bg-teal-700 transition-colors"
                >
                  Create
                </button>
              </div>
            </form>
          )}

          {/* Search box */}
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-teal-500 bg-slate-50"
            />
          </div>
        </div>

        {/* Sessions list container */}
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          {loadingSessions ? (
            Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="animate-pulse bg-slate-200/50 h-16 rounded-xl w-full mb-2" />
            ))
          ) : filteredSessions.length === 0 ? (
            <div className="text-center py-8 text-slate-400 text-xs">
              No active conversations.
            </div>
          ) : (
            filteredSessions.map((session) => {
              const isSelected = selectedSessionId === session.id
              const isEditing = editingSessionId === session.id

              return (
                <div
                  key={session.id}
                  onClick={() => !isEditing && setSelectedSessionId(session.id)}
                  className={`group relative flex flex-col p-3 rounded-xl cursor-pointer transition-all duration-200 border ${
                    isSelected
                      ? 'bg-white border-teal-200 shadow-md shadow-teal-50/30'
                      : 'bg-transparent border-transparent hover:bg-slate-100 hover:border-slate-200'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    {isEditing ? (
                      <div className="flex items-center gap-1.5 w-full pr-10" onClick={(e) => e.stopPropagation()}>
                        <input
                          type="text"
                          value={editTitleValue}
                          onChange={(e) => setEditTitleValue(e.target.value)}
                          className="flex-1 px-2 py-0.5 text-xs rounded border border-slate-300 focus:ring-1 focus:ring-teal-500"
                        />
                        <button
                          onClick={() => handleRenameSession(session.id)}
                          className="p-0.5 rounded text-green-600 hover:bg-green-50"
                        >
                          <Check className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={() => setEditingSessionId(null)}
                          className="p-0.5 rounded text-red-600 hover:bg-red-50"
                        >
                          <X className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    ) : (
                      <span className="font-semibold text-xs text-slate-700 truncate pr-6 group-hover:text-teal-700 transition-colors">
                        {session.title}
                      </span>
                    )}

                    <div className="flex items-center gap-1">
                      {session.pinned && <Pin className="h-3 w-3 text-amber-500 fill-amber-500" />}
                      {session.archived && <Archive className="h-3 w-3 text-slate-400" />}
                    </div>
                  </div>

                  <div className="flex justify-between items-center text-[10px] text-slate-400">
                    <span>{session.message_count} message{session.message_count !== 1 ? 's' : ''}</span>
                    <span>
                      {new Date(session.last_message_at).toLocaleDateString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </span>
                  </div>

                  {/* Actions overlay menu */}
                  {!isEditing && (
                    <div className="absolute right-2 top-2 hidden group-hover:flex items-center gap-1 bg-white p-1 rounded-lg border border-slate-100 shadow-md">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleTogglePin(session)
                        }}
                        className={`p-1 rounded hover:bg-slate-100 ${session.pinned ? 'text-amber-500' : 'text-slate-400'}`}
                      >
                        <Pin className="h-3 w-3" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleToggleArchive(session)
                        }}
                        className={`p-1 rounded hover:bg-slate-100 ${session.archived ? 'text-indigo-500' : 'text-slate-400'}`}
                      >
                        <Archive className="h-3 w-3" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setEditingSessionId(session.id)
                          setEditTitleValue(session.title)
                        }}
                        className="p-1 rounded hover:bg-slate-100 text-slate-400 hover:text-slate-600"
                      >
                        <Edit2 className="h-3 w-3" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDeleteSession(session.id)
                        }}
                        className="p-1 rounded hover:bg-red-50 text-slate-400 hover:text-red-600"
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </div>
                  )}
                </div>
              )
            })
          )}
        </div>
      </div>

      {/* 2. Right Workspace: Selected Session Conversation */}
      <div className="flex flex-1 flex-col bg-white">
        {selectedSessionId && activeSession ? (
          <>
            {/* Header section with Stats Bar */}
            <div className="flex flex-col p-4 border-b border-slate-100 bg-white">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                    <span>{activeSession.title}</span>
                    {activeSession.pinned && <Pin className="h-3 w-3 text-amber-500 fill-amber-500" />}
                  </h1>
                  <p className="text-[10px] text-slate-400 mt-0.5 font-semibold">
                    Patient: <span className="font-mono text-slate-500">{activeSession.patient_id}</span>
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setDeveloperMode(!developerMode)}
                    className={`flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold rounded-lg border transition-all ${
                      developerMode
                        ? 'border-teal-500 bg-teal-50 text-teal-700'
                        : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    <Code className="h-3.5 w-3.5" />
                    <span>Dev Mode: {developerMode ? 'On' : 'Off'}</span>
                  </button>

                  {/* Regenerate Action */}
                  <button
                    type="button"
                    onClick={handleRegenerate}
                    disabled={regenerateMutation.isPending || isStreaming}
                    className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-50 transition-all"
                    title="Regenerate last assistant message"
                  >
                    <RotateCcw className={`h-3.5 w-3.5 ${regenerateMutation.isPending ? 'animate-spin' : ''}`} />
                    <span>Regenerate</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleTogglePin(activeSession)}
                    className={`flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold rounded-lg border transition-all ${
                      activeSession.pinned
                        ? 'border-amber-200 bg-amber-50 text-amber-700'
                        : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    <Pin className="h-3.5 w-3.5" />
                  </button>

                  <button
                    type="button"
                    onClick={() => handleToggleArchive(activeSession)}
                    className={`flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold rounded-lg border transition-all ${
                      activeSession.archived
                        ? 'border-indigo-200 bg-indigo-50 text-indigo-700'
                        : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    <Archive className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>

              {/* Statistics info-bar */}
              {stats && (
                <div className="flex items-center gap-4 text-[10px] text-slate-500 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-100 mt-2.5">
                  <span className="flex items-center gap-1">
                    <MessageSquare className="h-3.5 w-3.5 text-teal-600" />
                    Messages: <strong className="text-slate-700">{stats.message_count}</strong>
                  </span>
                  <span className="flex items-center gap-1">
                    <Cpu className="h-3.5 w-3.5 text-teal-600" />
                    Tokens: <strong className="text-slate-700">{stats.total_tokens}</strong>
                  </span>
                  <span className="flex items-center gap-1">
                    <DollarSign className="h-3.5 w-3.5 text-teal-600" />
                    Cost: <strong className="text-slate-700">${stats.total_cost.toFixed(4)}</strong>
                  </span>
                  <span className="flex items-center gap-1">
                    <Activity className="h-3.5 w-3.5 text-teal-600" />
                    Avg Latency: <strong className="text-slate-700">{stats.average_latency.toFixed(0)}ms</strong>
                  </span>
                  {stats.last_agent_used && (
                    <span className="ml-auto bg-teal-50 text-teal-700 px-2 py-0.5 rounded border border-teal-100 font-semibold">
                      Agent: {stats.last_agent_used}
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* Conversation Messages area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/30">
              {loadingMessages ? (
                <div className="flex items-center justify-center h-full">
                  <span className="text-xs text-slate-400 animate-pulse">Loading conversation...</span>
                </div>
              ) : history.messages.length === 0 && !isStreaming ? (
                <div className="flex flex-col items-center justify-center h-full text-center max-w-sm mx-auto">
                  <div className="h-10 w-10 rounded-full bg-teal-50 flex items-center justify-center mb-3">
                    <Sparkles className="h-5 w-5 text-teal-600" />
                  </div>
                  <h3 className="text-sm font-bold text-slate-800 mb-1">Nura Consultation Start</h3>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Start streaming queries now. Nura dynamically evaluates diagnostics, prescriptions safety, and medical records.
                  </p>
                </div>
              ) : (
                <>
                  {history.messages.map((message) => {
                    const isUser = message.role === 'USER'
                    const isSystem = message.role === 'SYSTEM'

                    if (isSystem) {
                      return (
                        <div key={message.id} className="flex justify-center">
                          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-50 border border-amber-100 text-[10px] text-amber-700 font-semibold">
                            <Activity className="h-3 w-3" />
                            <span>{message.content}</span>
                          </div>
                        </div>
                      )
                    }

                    const citationsList = message.citations || []
                    const messageMetadata = message.metadata || {}
                    const agent = messageMetadata.agent || null
                    const hasCitationsExpanded = expandedMessageCitationsId === message.id
                    const isFeedbackSub = submittedFeedbacks[message.id] || false

                    return (
                      <div key={message.id} className={`flex gap-3 max-w-[78%] ${isUser ? 'ml-auto flex-row-reverse' : ''}`}>
                        {/* Avatar */}
                        <div className={`h-8 w-8 rounded-full flex items-center justify-center flex-shrink-0 border shadow-sm ${
                          isUser ? 'bg-slate-100 border-slate-200' : 'bg-teal-50 border-teal-200'
                        }`}>
                          {isUser ? <User className="h-4 w-4 text-slate-600" /> : <Sparkles className="h-4 w-4 text-teal-600" />}
                        </div>

                        {/* Bubble */}
                        <div className="flex flex-col max-w-full">
                          <div className={`px-4 py-2.5 rounded-2xl text-xs leading-relaxed shadow-sm relative group border ${
                            isUser
                              ? 'bg-teal-600 text-white rounded-tr-none border-teal-600'
                              : 'bg-white border-slate-150 text-slate-700 rounded-tl-none'
                          }`}>
                            {isUser ? (
                              <p className="whitespace-pre-line font-medium">{message.content}</p>
                            ) : (
                              <div>{renderMarkdown(message.content)}</div>
                            )}

                            {/* Citations expandable widget below bubbles */}
                            {!isUser && citationsList.length > 0 && (
                              <div className="mt-3 pt-2.5 border-t border-slate-100">
                                <button
                                  type="button"
                                  onClick={() => setExpandedMessageCitationsId(hasCitationsExpanded ? null : message.id)}
                                  className="flex items-center gap-1 text-[10px] font-bold text-slate-500 hover:text-teal-600 transition-all focus:outline-none"
                                >
                                  {hasCitationsExpanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
                                  <BookOpen className="h-3.5 w-3.5 text-teal-600" />
                                  <span>Sources & Citations ({citationsList.length})</span>
                                </button>
                                
                                {hasCitationsExpanded && (
                                  <div className="mt-2 space-y-1.5 animate-in fade-in duration-200">
                                    {citationsList.map((cit: any, cidx: number) => (
                                      <div key={cidx} className="bg-slate-50 border border-slate-100 rounded-lg p-2 font-mono text-[9px] text-slate-600">
                                        <div className="flex justify-between items-center mb-0.5">
                                          <span className="font-semibold text-teal-700">[{cidx + 1}] Source: {cit.source || cit.collection || 'Document'}</span>
                                          {cit.score !== undefined && (
                                            <span className="bg-teal-50 text-teal-800 px-1 rounded font-bold">Confidence: {(cit.score * 100).toFixed(0)}%</span>
                                          )}
                                        </div>
                                        {cit.document_id && <div className="truncate">Doc ID: {cit.document_id}</div>}
                                        {cit.page_number !== undefined && <div>Page: {cit.page_number}</div>}
                                        {cit.section && <div>Section: {cit.section}</div>}
                                      </div>
                                    ))}
                                  </div>
                                )}
                              </div>
                            )}

                            {/* Action links inside assistant message bubbles (Copy / Feedback / Rating) */}
                            {!isUser && (
                              <div className="absolute right-2 bottom-2 hidden group-hover:flex items-center gap-1.5 bg-white border border-slate-150 p-1.5 rounded-lg shadow-md animate-in fade-in duration-150">
                                <button
                                  type="button"
                                  onClick={() => handleCopyMessage(message.content)}
                                  className="p-1 rounded hover:bg-slate-50 text-slate-400 hover:text-slate-600 transition-all"
                                  title="Copy response text"
                                >
                                  <Copy className="h-3 w-3" />
                                </button>

                                {/* Rating Feedback Controls */}
                                {!isFeedbackSub && (
                                  <>
                                    <button
                                      type="button"
                                      onClick={() => {
                                        setActiveFeedbackMessageId(message.id)
                                        setFeedbackRating('helpful')
                                      }}
                                      className="p-1 rounded hover:bg-green-50 text-slate-400 hover:text-green-600 transition-all"
                                      title="Helpful"
                                    >
                                      <ThumbsUp className="h-3 w-3" />
                                    </button>
                                    <button
                                      type="button"
                                      onClick={() => {
                                        setActiveFeedbackMessageId(message.id)
                                        setFeedbackRating('unhelpful')
                                      }}
                                      className="p-1 rounded hover:bg-red-50 text-slate-400 hover:text-red-600 transition-all"
                                      title="Not Helpful"
                                    >
                                      <ThumbsDown className="h-3 w-3" />
                                    </button>
                                  </>
                                )}
                              </div>
                            )}
                          </div>

                          {/* Metadata row under assistant bubble */}
                          <div className={`flex flex-wrap gap-2 mt-1 text-[9px] text-slate-400 ${isUser ? 'justify-end' : 'justify-start'}`}>
                            <span>
                              {new Date(message.created_at).toLocaleTimeString(undefined, {
                                hour: '2-digit',
                                minute: '2-digit',
                              })}
                            </span>

                            {!isUser && agent && (
                              <span className="font-bold text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200/50">
                                agent: {agent}
                              </span>
                            )}

                            {!isUser && isFeedbackSub && (
                              <span className="text-green-600 font-bold bg-green-50 px-1.5 py-0.5 rounded border border-green-150/50 flex items-center gap-0.5">
                                <Check className="h-2.5 w-2.5" /> Feedback submitted
                              </span>
                            )}

                            {!isUser && developerMode && (
                              <>
                                {message.latency_ms && (
                                  <span className="bg-slate-100 text-indigo-600 px-1.5 py-0.5 rounded border border-slate-200/50 font-semibold">
                                    latency: {message.latency_ms}ms
                                  </span>
                                )}
                                {message.token_usage && (
                                  <span className="bg-slate-100 text-amber-600 px-1.5 py-0.5 rounded border border-slate-200/50 font-mono">
                                    tokens: {message.token_usage.total_tokens || 0}
                                  </span>
                                )}
                                {messageMetadata.cost !== undefined && (
                                  <span className="bg-slate-100 text-emerald-600 px-1.5 py-0.5 rounded border border-slate-200/50 font-semibold">
                                    cost: ${messageMetadata.cost.toFixed(4)}
                                  </span>
                                )}
                              </>
                            )}
                          </div>

                          {/* Inline Feedback Drawer (rating review input form) */}
                          {!isUser && activeFeedbackMessageId === message.id && (
                            <div className="mt-2 p-3 bg-slate-50 border border-slate-150 rounded-xl max-w-sm space-y-2 animate-in slide-in-from-top duration-200">
                              <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-700">
                                {feedbackRating === 'helpful' ? (
                                  <ThumbsUp className="h-3.5 w-3.5 text-green-600" />
                                ) : (
                                  <ThumbsDown className="h-3.5 w-3.5 text-red-600" />
                                )}
                                <span>Add optional feedback comment</span>
                              </div>
                              <textarea
                                rows={2}
                                value={feedbackComment}
                                onChange={(e) => setFeedbackComment(e.target.value)}
                                placeholder="What went well or could be improved?..."
                                className="w-full px-2.5 py-1.5 text-[10px] rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-teal-500 bg-white"
                              />
                              <div className="flex gap-2 justify-end">
                                <button
                                  type="button"
                                  onClick={() => {
                                    setActiveFeedbackMessageId(null)
                                    setFeedbackRating(null)
                                  }}
                                  className="px-2 py-1 text-[9px] font-bold rounded bg-slate-200 text-slate-600 hover:bg-slate-300"
                                >
                                  Cancel
                                </button>
                                <button
                                  type="button"
                                  onClick={() => handleFeedbackSubmit(message.id)}
                                  className="px-2 py-1 text-[9px] font-bold rounded bg-teal-600 text-white hover:bg-teal-700"
                                >
                                  Submit
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </>
              )}

              {/* Streaming Real-Time Bubble with blinking cursor */}
              {isStreaming && streamingText && (
                <div className="flex gap-3 max-w-[78%] animate-in fade-in duration-200">
                  <div className="h-8 w-8 rounded-full bg-teal-50 border border-teal-200 flex items-center justify-center flex-shrink-0 shadow-sm animate-pulse">
                    <Sparkles className="h-4 w-4 text-teal-600" />
                  </div>
                  <div className="flex flex-col">
                    <div className="px-4 py-2.5 rounded-2xl bg-white border border-slate-150 text-slate-700 rounded-tl-none text-xs leading-relaxed shadow-sm">
                      <div>{renderMarkdown(streamingText)}</div>
                      <span className="inline-block w-1.5 h-3.5 ml-0.5 bg-teal-600 animate-pulse" />
                    </div>
                    {streamingAgent && (
                      <div className="mt-1 text-[9px] text-slate-400 font-bold">
                        agent: {streamingAgent}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Loader indicator before chunks arrive */}
              {isStreaming && !streamingText && (
                <div className="flex gap-3 max-w-[75%] animate-in fade-in duration-200">
                  <div className="h-8 w-8 rounded-full bg-teal-50 border border-teal-200 flex items-center justify-center flex-shrink-0 shadow-sm animate-pulse">
                    <Sparkles className="h-4 w-4 text-teal-600" />
                  </div>
                  <div className="flex flex-col">
                    <div className="px-4 py-2.5 rounded-2xl bg-white border border-slate-150 text-slate-400 rounded-tl-none text-xs flex items-center gap-1.5">
                      <span className="h-1.5 w-1.5 bg-teal-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="h-1.5 w-1.5 bg-teal-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="h-1.5 w-1.5 bg-teal-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      <span className="ml-1 text-[10px] text-slate-400 font-semibold animate-pulse">Nura is computing...</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Suggested Follow-up Questions badges */}
              {!isStreaming && lastAssistant && !lastAssistant.deleted && (
                <FollowUpQuestionsSection
                  messageId={lastAssistant.id}
                  onQuestionClick={(q) => handleSendMessage(null as any, q)}
                />
              )}

              <div ref={bottomRef} />
            </div>

            {/* Bottom input area */}
            <div className="p-4 border-t border-slate-100 bg-white">
              <form onSubmit={handleSendMessage} className="space-y-3">
                <div className="flex items-center gap-2">
                  <textarea
                    rows={2}
                    value={messageText}
                    onChange={(e) => setMessageText(e.target.value)}
                    placeholder="Ask Nura about diagnostics, prescriptions, safety, or appointments..."
                    disabled={isStreaming}
                    className="flex-1 px-3 py-2.5 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-1 focus:ring-teal-500 bg-slate-50 resize-none placeholder-slate-400 disabled:opacity-50"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault()
                        handleSendMessage(e)
                      }
                    }}
                  />
                  
                  <div className="flex flex-col gap-2">
                    <select
                      value={messageRole}
                      onChange={(e) => setMessageRole(e.target.value as any)}
                      className="px-2 py-1 text-[10px] rounded border border-slate-200 bg-slate-50 font-semibold text-slate-600 focus:outline-none"
                      disabled={isStreaming}
                    >
                      <option value="USER">Patient (User)</option>
                      <option value="ASSISTANT">Manual Nura (Assistant)</option>
                      <option value="SYSTEM">Manual Event (System)</option>
                    </select>

                    {isStreaming ? (
                      <button
                        type="button"
                        onClick={stopGeneration}
                        className="flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl bg-red-600 text-white font-bold text-xs hover:bg-red-700 transition-all shadow-md shadow-red-600/10"
                      >
                        <Square className="h-3.5 w-3.5 fill-white" />
                        <span>Stop</span>
                      </button>
                    ) : (
                      <button
                        type="submit"
                        disabled={!messageText.trim() || isStreaming}
                        className="flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl bg-teal-600 text-white font-bold text-xs hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md shadow-teal-600/10"
                      >
                        <Send className="h-3.5 w-3.5" />
                        <span>Send</span>
                      </button>
                    )}
                  </div>
                </div>
              </form>
            </div>
          </>
        ) : (
          /* Empty/Welcome state */
          <div className="flex flex-col items-center justify-center h-full p-8 text-center max-w-md mx-auto">
            <div className="h-16 w-16 rounded-3xl bg-gradient-to-tr from-teal-500 to-emerald-400 text-white flex items-center justify-center mb-6 shadow-lg shadow-teal-500/20 animate-bounce">
              <Sparkles className="h-8 w-8" />
            </div>
            <h1 className="text-xl font-extrabold text-slate-800 mb-2">Nura Conversational AI</h1>
            <p className="text-xs text-slate-400 leading-relaxed mb-6">
              Start a streaming consultation session now. Enforces clinical pipelines with retrieval, validation checks, and automatic title generation.
            </p>
            <button
              onClick={() => setIsCreating(true)}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-teal-600 text-white font-bold text-xs hover:bg-teal-700 hover:scale-[1.02] active:scale-[0.98] transition-all shadow-md shadow-teal-600/10"
            >
              <Plus className="h-4 w-4" />
              <span>New Conversation</span>
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

// Dedicated child component to fetch and render suggested questions reactively
function FollowUpQuestionsSection({
  messageId,
  onQuestionClick
}: {
  messageId: string
  onQuestionClick: (q: string) => void
}) {
  const { useFollowupQuestions } = require('@/hooks/use-chat')
  const { data: questions = [], isLoading } = useFollowupQuestions(messageId)

  if (isLoading || questions.length === 0) return null

  return (
    <div className="mt-3 p-3 bg-teal-50/40 border border-teal-100/50 rounded-xl space-y-2 animate-in fade-in slide-in-from-bottom duration-300">
      <span className="text-[10px] font-extrabold text-teal-800 uppercase tracking-wider flex items-center gap-1.5">
        <Sparkles className="h-3.5 w-3.5 text-teal-600" /> Suggested Follow-ups:
      </span>
      <div className="flex flex-wrap gap-2">
        {questions.map((question: string, index: number) => (
          <button
            key={index}
            type="button"
            onClick={() => onQuestionClick(question)}
            className="text-left px-3 py-1.5 text-[10px] font-bold text-teal-700 bg-white border border-teal-200 rounded-lg hover:bg-teal-50 hover:border-teal-300 active:scale-95 transition-all shadow-sm"
          >
            {question}
          </button>
        ))}
      </div>
    </div>
  )
}
