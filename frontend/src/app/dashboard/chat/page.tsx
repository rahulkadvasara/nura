'use client'

import { useState } from 'react'
import { useAuthStore } from '@/stores/auth'
import {
  useSessions,
  useSession,
  useMessages,
  useCreateSession,
  useUpdateSession,
  useDeleteSession,
  useCreateMessage,
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
} from 'lucide-react'
import { toast } from 'react-hot-toast'

export default function ChatPage() {
  const { user } = useAuthStore()
  const patientId = user?.id || ''

  // Selected session state
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)
  
  // Search session state
  const [searchQuery, setSearchQuery] = useState('')

  // New session inline creation toggle and input
  const [isCreating, setIsCreating] = useState(false)
  const [newSessionTitle, setNewSessionTitle] = useState('')

  // Editing session title state
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null)
  const [editTitleValue, setEditTitleValue] = useState('')

  // Message input state
  const [messageText, setMessageText] = useState('')
  const [messageRole, setMessageRole] = useState<'USER' | 'ASSISTANT' | 'SYSTEM'>('USER')

  // TanStack hooks
  const { data: sessions = [], isLoading: loadingSessions } = useSessions(100, 0, true)
  const { data: activeSession } = useSession(selectedSessionId)
  const { data: history = { messages: [] }, isLoading: loadingMessages } = useMessages(selectedSessionId)

  const createSessionMutation = useCreateSession()
  const updateSessionMutation = useUpdateSession()
  const deleteSessionMutation = useDeleteSession()
  const createMessageMutation = useCreateMessage()

  // Filter sessions by search query
  const filteredSessions = sessions.filter(session =>
    session.title.toLowerCase().includes(searchQuery.toLowerCase())
  )

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

  // Handle message post
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!messageText.trim() || !selectedSessionId) return

    try {
      await createMessageMutation.mutateAsync({
        session_id: selectedSessionId,
        patient_id: patientId,
        role: messageRole,
        content: messageText.trim(),
      })
      setMessageText('')
      toast.success('Message logged')
    } catch (err: any) {
      toast.error(err.message || 'Failed to log message')
    }
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl">
      {/* 1. Left Sidebar: Chat History */}
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

          {/* New Session Input Form */}
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

          {/* Search Input */}
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search chat sessions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-teal-500 bg-slate-50"
            />
          </div>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          {loadingSessions ? (
            // Skeleton Loader
            Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="animate-pulse bg-slate-200/50 h-16 rounded-xl w-full mb-2" />
            ))
          ) : filteredSessions.length === 0 ? (
            <div className="text-center py-8 text-slate-400 text-xs">
              No chat sessions found.
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
                    {/* Editable Title */}
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

                    {/* Icons/Badges */}
                    <div className="flex items-center gap-1">
                      {session.pinned && <Pin className="h-3 w-3 text-amber-500 fill-amber-500" />}
                      {session.archived && <Archive className="h-3 w-3 text-slate-400" />}
                    </div>
                  </div>

                  {/* Metadata and Excerpt */}
                  <div className="flex justify-between items-center text-[10px] text-slate-400">
                    <span>
                      {session.message_count} message{session.message_count !== 1 ? 's' : ''}
                    </span>
                    <span>
                      {new Date(session.last_message_at).toLocaleDateString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                  </div>

                  {/* Hover Actions Menu */}
                  {!isEditing && (
                    <div className="absolute right-2 top-2 hidden group-hover:flex items-center gap-1 bg-white p-1 rounded-lg border border-slate-100 shadow-md">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleTogglePin(session)
                        }}
                        className={`p-1 rounded hover:bg-slate-100 ${
                          session.pinned ? 'text-amber-500' : 'text-slate-400'
                        }`}
                        title={session.pinned ? 'Unpin Session' : 'Pin Session'}
                      >
                        <Pin className="h-3 w-3" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleToggleArchive(session)
                        }}
                        className={`p-1 rounded hover:bg-slate-100 ${
                          session.archived ? 'text-indigo-500' : 'text-slate-400'
                        }`}
                        title={session.archived ? 'Unarchive Session' : 'Archive Session'}
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
                        title="Rename Session"
                      >
                        <Edit2 className="h-3 w-3" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDeleteSession(session.id)
                        }}
                        className="p-1 rounded hover:bg-red-50 text-slate-400 hover:text-red-600"
                        title="Delete Session"
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

      {/* 2. Right Column: Conversation Workspace */}
      <div className="flex flex-1 flex-col bg-white">
        {selectedSessionId && activeSession ? (
          <>
            {/* Conversation Header */}
            <div className="flex items-center justify-between p-4 border-b border-slate-100 bg-white">
              <div>
                <h1 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                  <span>{activeSession.title}</span>
                  {activeSession.pinned && <Pin className="h-3 w-3 text-amber-500 fill-amber-500" />}
                </h1>
                <p className="text-[10px] text-slate-400">
                  Patient ID: <span className="font-mono text-slate-500">{activeSession.patient_id}</span>
                </p>
              </div>

              {/* Header Action Buttons */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleTogglePin(activeSession)}
                  className={`flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold rounded-lg border transition-all ${
                    activeSession.pinned
                      ? 'border-amber-200 bg-amber-50 text-amber-700'
                      : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <Pin className="h-3.5 w-3.5" />
                  <span>{activeSession.pinned ? 'Pinned' : 'Pin'}</span>
                </button>

                <button
                  onClick={() => handleToggleArchive(activeSession)}
                  className={`flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold rounded-lg border transition-all ${
                    activeSession.archived
                      ? 'border-indigo-200 bg-indigo-50 text-indigo-700'
                      : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <Archive className="h-3.5 w-3.5" />
                  <span>{activeSession.archived ? 'Archived' : 'Archive'}</span>
                </button>

                <button
                  onClick={() => handleDeleteSession(activeSession.id)}
                  className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold rounded-lg border border-red-200 bg-red-50/50 text-red-600 hover:bg-red-50 transition-all"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  <span>Delete</span>
                </button>
              </div>
            </div>

            {/* Conversation Message List */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/30">
              {loadingMessages ? (
                <div className="flex items-center justify-center h-full">
                  <span className="text-xs text-slate-400 animate-pulse">Loading message history...</span>
                </div>
              ) : history.messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center max-w-sm mx-auto">
                  <div className="h-10 w-10 rounded-full bg-teal-50 flex items-center justify-center mb-3">
                    <Sparkles className="h-5 w-5 text-teal-600" />
                  </div>
                  <h3 className="text-sm font-bold text-slate-800 mb-1">Infrastructure Configured</h3>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    This chat session is fully set up in MongoDB. Write a message below to test storing it in the database.
                  </p>
                </div>
              ) : (
                history.messages.map((message) => {
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

                  return (
                    <div
                      key={message.id}
                      className={`flex gap-3 max-w-[75%] ${isUser ? 'ml-auto flex-row-reverse' : ''}`}
                    >
                      {/* Avatar */}
                      <div
                        className={`h-8 w-8 rounded-full flex items-center justify-center flex-shrink-0 border shadow-sm ${
                          isUser ? 'bg-slate-100 border-slate-200' : 'bg-teal-50 border-teal-200'
                        }`}
                      >
                        {isUser ? (
                          <User className="h-4 w-4 text-slate-600" />
                        ) : (
                          <Sparkles className="h-4 w-4 text-teal-600" />
                        )}
                      </div>

                      {/* Bubble */}
                      <div className="flex flex-col">
                        <div
                          className={`px-4 py-2.5 rounded-2xl text-xs leading-relaxed shadow-sm transition-all ${
                            isUser
                              ? 'bg-teal-600 text-white rounded-tr-none'
                              : 'bg-white border border-slate-150 text-slate-700 rounded-tl-none'
                          }`}
                        >
                          <p className="whitespace-pre-line">{message.content}</p>
                        </div>
                        <span className={`text-[9px] text-slate-400 mt-1 ${isUser ? 'text-right' : ''}`}>
                          {new Date(message.created_at).toLocaleTimeString(undefined, {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                      </div>
                    </div>
                  )
                })
              )}
            </div>

            {/* Bottom Input Area */}
            <div className="p-4 border-t border-slate-100 bg-white">
              <form onSubmit={handleSendMessage} className="space-y-3">
                <div className="flex items-center gap-2">
                  <textarea
                    rows={2}
                    value={messageText}
                    onChange={(e) => setMessageText(e.target.value)}
                    placeholder="Type your message here..."
                    className="flex-1 px-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-1 focus:ring-teal-500 bg-slate-50 resize-none"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault()
                        handleSendMessage(e)
                      }
                    }}
                  />
                  
                  {/* Action controls */}
                  <div className="flex flex-col gap-2">
                    {/* Role dropdown simulation */}
                    <select
                      value={messageRole}
                      onChange={(e) => setMessageRole(e.target.value as any)}
                      className="px-2 py-1 text-[10px] rounded border border-slate-200 bg-slate-50 font-semibold text-slate-600 focus:outline-none"
                      title="Sender Role (Simulation)"
                    >
                      <option value="USER">Patient (User)</option>
                      <option value="ASSISTANT">Nura (Assistant)</option>
                      <option value="SYSTEM">System (Event)</option>
                    </select>

                    <button
                      type="submit"
                      disabled={!messageText.trim() || createMessageMutation.isPending}
                      className="flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl bg-teal-600 text-white font-bold text-xs hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                      <Send className="h-3.5 w-3.5" />
                      <span>Send</span>
                    </button>
                  </div>
                </div>
              </form>
            </div>
          </>
        ) : (
          /* Welcome Screen Area */
          <div className="flex flex-col items-center justify-center h-full p-8 text-center max-w-md mx-auto">
            <div className="h-16 w-16 rounded-3xl bg-gradient-to-tr from-teal-500 to-emerald-400 text-white flex items-center justify-center mb-6 shadow-lg shadow-teal-500/20 animate-bounce">
              <Sparkles className="h-8 w-8" />
            </div>
            <h1 className="text-xl font-extrabold text-slate-800 mb-2">Nura Conversational AI</h1>
            <p className="text-xs text-slate-400 leading-relaxed mb-6">
              Welcome to the conversational center. Here you can start a persistent chat session to review medical diagnostics, explore treatment safety, and track appointments.
            </p>
            <button
              onClick={() => setIsCreating(true)}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-teal-600 text-white font-bold text-xs hover:bg-teal-700 hover:scale-[1.02] active:scale-[0.98] transition-all shadow-md shadow-teal-600/10"
            >
              <Plus className="h-4 w-4" />
              <span>Create New Chat Session</span>
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
