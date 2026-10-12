/** Same-tab Agent Chat thread_id. sessionStorage is per-tab; not a history store. */

export const THREAD_STORAGE_KEY = 'opspilot_thread_id'

function newThreadId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return `thread_${crypto.randomUUID()}`
  }
  return `thread_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`
}

export function clearStoredThreadId(): void {
  try {
    sessionStorage.removeItem(THREAD_STORAGE_KEY)
  } catch {
    /* ignore quota / private mode */
  }
}

export function getOrCreateThreadId(): string {
  try {
    const existing = (sessionStorage.getItem(THREAD_STORAGE_KEY) || '').trim()
    if (existing) return existing
    const id = newThreadId()
    sessionStorage.setItem(THREAD_STORAGE_KEY, id)
    return id
  } catch {
    return newThreadId()
  }
}
