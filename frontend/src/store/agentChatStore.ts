import { create } from 'zustand'
import type { AgentConfirmation, AgentPermissionCard, AgentTicketCard } from '../types/api'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  text: string
  tickets?: AgentTicketCard[]
  permissions?: AgentPermissionCard[]
  pending?: boolean
  confirmation?: AgentConfirmation | null
}

type MessagesUpdater = ChatMessage[] | ((prev: ChatMessage[]) => ChatMessage[])

interface AgentChatState {
  byThread: Record<string, ChatMessage[]>
  setMessages: (threadId: string, next: MessagesUpdater) => void
  clearAll: () => void
}

const EMPTY: ChatMessage[] = []

export function selectThreadMessages(threadId: string) {
  return (s: AgentChatState) => s.byThread[threadId] ?? EMPTY
}

export const useAgentChatStore = create<AgentChatState>((set) => ({
  byThread: {},

  setMessages: (threadId, next) => {
    set((s) => {
      const prev = s.byThread[threadId] ?? EMPTY
      const messages = typeof next === 'function' ? next(prev) : next
      return { byThread: { ...s.byThread, [threadId]: messages } }
    })
  },

  clearAll: () => set({ byThread: {} }),
}))
