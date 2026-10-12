import axios, { AxiosError } from 'axios'
import type { ApiEnvelope } from '../types/api'

const TOKEN_KEY = 'opspilot_token'

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setStoredToken(token: string | null): void {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token)
  } else {
    localStorage.removeItem(TOKEN_KEY)
  }
}

export class ApiError extends Error {
  code: number
  httpStatus: number

  constructor(code: number, message: string, httpStatus: number) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.httpStatus = httpStatus
  }
}

export const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use((config) => {
  const token = getStoredToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
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

export function unwrapData<T>(envelope: ApiEnvelope<T>): T {
  return envelope.data
}

export function errorMessage(err: unknown, fallback = '操作失败'): string {
  if (err instanceof ApiError) {
    return err.message || fallback
  }
  if (err instanceof Error) {
    return err.message || fallback
  }
  return fallback
}
