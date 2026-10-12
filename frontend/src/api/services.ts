import { apiClient, unwrapData } from './client'
import type { ApiEnvelope, ServiceListData } from '../types/api'

export async function listServices(): Promise<ServiceListData> {
  const res = await apiClient.get<ApiEnvelope<ServiceListData>>('/services')
  return unwrapData(res.data)
}
