import { apiClient, unwrapData } from './client'
import type {
  ApiEnvelope,
  CreateTicketBody,
  CreateTicketResult,
  PatchTicketResult,
  Ticket,
  TicketListData,
  TicketStatus,
} from '../types/api'

export async function listTickets(params?: {
  page?: number
  page_size?: number
  status?: string
}): Promise<TicketListData> {
  const res = await apiClient.get<ApiEnvelope<TicketListData>>('/tickets', { params })
  return unwrapData(res.data)
}

export async function createTicket(body: CreateTicketBody): Promise<CreateTicketResult> {
  const res = await apiClient.post<ApiEnvelope<CreateTicketResult>>('/tickets', body)
  return unwrapData(res.data)
}

export async function getTicket(id: string): Promise<Ticket> {
  const res = await apiClient.get<ApiEnvelope<Ticket>>(`/tickets/${id}`)
  return unwrapData(res.data)
}

export async function patchTicketStatus(
  id: string,
  status: TicketStatus,
): Promise<PatchTicketResult> {
  const res = await apiClient.patch<ApiEnvelope<PatchTicketResult>>(`/tickets/${id}`, { status })
  return unwrapData(res.data)
}
