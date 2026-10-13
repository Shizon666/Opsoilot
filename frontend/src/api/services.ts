import { apiClient, unwrapData } from './client'
import type { ApiEnvelope, Service, ServiceHealthStatus, ServiceListData } from '../types/api'

export async function listServices(): Promise<ServiceListData> {
  const res = await apiClient.get<ApiEnvelope<ServiceListData>>('/services')
  return unwrapData(res.data)
}

export interface PatchServiceBody {
  health_status?: ServiceHealthStatus
  health_summary?: string | null
  last_checked_at?: string
}

/** PATCH /services/:id — IT_SUPPORT / ADMIN only (backend enforces). */
export async function patchService(id: string, body: PatchServiceBody): Promise<Service> {
  const res = await apiClient.patch<ApiEnvelope<Service>>(`/services/${id}`, body)
  return unwrapData(res.data)
}
