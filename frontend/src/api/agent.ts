import axios, { AxiosError } from 'axios'
import { ApiError, getStoredToken, unwrapData } from './client'
import type {
  AgentChatData,
  AgentChatRequest,
  AgentResumeRequest,
  AgentStreamEvent,
  ApiEnvelope,
} from '../types/api'

/** Separate client: Agent path is /agent/* (not under /api/v1); LLM needs longer timeout. */
const agentClient = axios.create({
  baseURL: '/',
  timeout: 120_000,
  headers: {
    'Content-Type': 'application/json',
  },
})

agentClient.interceptors.request.use((config) => {
  const token = getStoredToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

agentClient.interceptors.response.use(
  (response) => {
    const body = response.data as ApiEnvelope<unknown>
    if (body && typeof body.code === 'number' && body.code !== 0) {
      return Promise.reject(new ApiError(body.code, body.message || 'request failed', response.status))
    }
    return response
  },
  (error: AxiosError<ApiEnvelope<unknown>>) => {
    if (error.response?.data && typeof error.response.data.code === 'number') {
      const { code, message } = error.response.data
      return Promise.reject(new ApiError(code, message || 'request failed', error.response.status))
    }
    return Promise.reject(
      new ApiError(50001, error.message || 'network error', error.response?.status || 0),
    )
  },
)

export async function postAgentChat(body: AgentChatRequest): Promise<AgentChatData> {
  const res = await agentClient.post<ApiEnvelope<AgentChatData>>('/agent/chat', body)
  return unwrapData(res.data)
}

export async function postAgentResume(body: AgentResumeRequest): Promise<AgentChatData> {
  const res = await agentClient.post<ApiEnvelope<AgentChatData>>('/agent/chat/resume', body)
  return unwrapData(res.data)
}

function streamHttpError(status: number, body: unknown): ApiError {
  const rec = body && typeof body === 'object' ? (body as Record<string, unknown>) : null
  const detail = rec?.detail
  const detailRec = detail && typeof detail === 'object' ? (detail as Record<string, unknown>) : null
  const codeRaw = detailRec?.code ?? rec?.code
  const msgRaw = detailRec?.message ?? rec?.message
  const code = typeof codeRaw === 'number' ? codeRaw : status === 401 ? 40101 : status === 403 ? 40301 : 50001
  const msg = typeof msgRaw === 'string' && msgRaw ? msgRaw : 'request failed'
  return new ApiError(code, msg, status)
}

async function rejectIfHttpError(res: Response): Promise<void> {
  if (res.ok) return
  const ct = res.headers.get('content-type') || ''
  if (ct.includes('application/json')) {
    try {
      throw streamHttpError(res.status, await res.json())
    } catch (err) {
      if (err instanceof ApiError) throw err
    }
  }
  const text = await res.text().catch(() => '')
  throw new ApiError(
    res.status === 401 ? 40101 : res.status === 403 ? 40301 : 50001,
    text || res.statusText || 'request failed',
    res.status,
  )
}

function dispatchSseBlock(block: string, onEvent: (event: AgentStreamEvent) => void): void {
  const dataLines: string[] = []
  for (const line of block.split('\n')) {
    if (line.startsWith('data:')) {
      dataLines.push(line.slice(5).trimStart())
    }
  }
  if (!dataLines.length) return
  const payload = dataLines.join('\n').trim()
  if (!payload) return
  try {
    const parsed = JSON.parse(payload) as AgentStreamEvent
    if (parsed && typeof parsed.type === 'string') onEvent(parsed)
  } catch {
    // skip malformed frame
  }
}

function consumeSseBuffer(buffer: string, onEvent: (event: AgentStreamEvent) => void): string {
  const normalized = buffer.replace(/\r\n/g, '\n')
  let rest = normalized
  while (true) {
    const idx = rest.indexOf('\n\n')
    if (idx < 0) return rest
    dispatchSseBlock(rest.slice(0, idx), onEvent)
    rest = rest.slice(idx + 2)
  }
}

export async function streamAgentChat(
  body: AgentChatRequest,
  onEvent: (event: AgentStreamEvent) => void,
): Promise<void> {
  const token = getStoredToken()
  let res: Response
  try {
    res = await fetch('/agent/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(body),
    })
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'network error'
    throw new ApiError(50001, msg, 0)
  }

  await rejectIfHttpError(res)
  if (!res.body) {
    throw new ApiError(50001, 'empty stream', res.status)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    buffer = consumeSseBuffer(buffer, onEvent)
  }
  buffer += decoder.decode()
  buffer = consumeSseBuffer(buffer, onEvent)
  if (buffer.trim()) {
    dispatchSseBlock(buffer, onEvent)
  }
}
