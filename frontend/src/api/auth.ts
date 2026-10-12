import { apiClient, unwrapData } from './client'
import type { ApiEnvelope, AuthUser, LoginData } from '../types/api'

export async function login(username: string, password: string): Promise<LoginData> {
  const res = await apiClient.post<ApiEnvelope<LoginData>>('/auth/login', {
    username,
    password,
  })
  return unwrapData(res.data)
}

export async function fetchMe(): Promise<AuthUser> {
  const res = await apiClient.get<ApiEnvelope<AuthUser>>('/users/me')
  return unwrapData(res.data)
}
