import { create } from 'zustand'
import { fetchMe, login as loginApi } from '../api/auth'
import { getStoredToken, setStoredToken } from '../api/client'
import type { AuthUser, UserRole } from '../types/api'
import { useAgentChatStore } from './agentChatStore'
import { clearStoredThreadId } from '../utils/threadId'

function clearAgentSession() {
  clearStoredThreadId()
  useAgentChatStore.getState().clearAll()
}

interface AuthState {
  token: string | null
  user: AuthUser | null
  hydrated: boolean
  login: (username: string, password: string) => Promise<AuthUser>
  logout: () => void
  hydrate: () => Promise<void>
  isSupport: () => boolean
}

function isSupportRole(role: UserRole | undefined): boolean {
  return role === 'it_support' || role === 'admin'
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: getStoredToken(),
  user: null,
  hydrated: false,

  login: async (username, password) => {
    const data = await loginApi(username, password)
    clearAgentSession()
    setStoredToken(data.token)
    set({ token: data.token, user: data.user })
    return data.user
  },

  logout: () => {
    clearAgentSession()
    setStoredToken(null)
    set({ token: null, user: null })
  },

  hydrate: async () => {
    const token = getStoredToken()
    if (!token) {
      set({ token: null, user: null, hydrated: true })
      return
    }
    try {
      const user = await fetchMe()
      set({ token, user, hydrated: true })
    } catch {
      setStoredToken(null)
      set({ token: null, user: null, hydrated: true })
    }
  },

  isSupport: () => isSupportRole(get().user?.role),
}))

export { isSupportRole }
