/** Aligns with current Go Backend response shapes (not API.md illustrations). */

export type UserRole = 'employee' | 'it_support' | 'admin'

export type TicketStatus =
  | 'open'
  | 'assigned'
  | 'in_progress'
  | 'waiting_user'
  | 'resolved'
  | 'closed'

export type TicketPriority = 'low' | 'medium' | 'high' | 'urgent'

export interface ApiEnvelope<T> {
  code: number
  message: string
  data: T
}

export interface AuthUser {
  id: string
  username: string
  name: string
  role: UserRole
  /** Phase 12 employee context — not an authz claim */
  department?: string
  position?: string
  employee_level?: string
}

export interface LoginData {
  token: string
  expires_in: number
  user: AuthUser
}

export interface Ticket {
  id: string
  ticket_no: string
  title: string
  description: string
  status: TicketStatus
  priority: TicketPriority
  creator_id: string
  assignee_id?: string | null
  service_id: string
  /** Support note when waiting on user (or general analysis summary). */
  analysis?: string | null
  created_at: string
  updated_at: string
}

export interface PatchTicketBody {
  title?: string
  description?: string
  priority?: TicketPriority
  status?: TicketStatus
  assignee_id?: string
  analysis?: string
  resolution?: string
}

export interface TicketListData {
  items: Ticket[]
  total: number
  page: number
  page_size: number
}

export type ServiceHealthStatus = 'HEALTHY' | 'DEGRADED' | 'DOWN'

export interface Service {
  id: string
  code: string
  name: string
  description?: string | null
  category: string
  status: string
  health_status: ServiceHealthStatus | string
  health_summary?: string | null
  last_checked_at?: string | null
}

export interface ServiceListData {
  items: Service[]
}

export interface CreateTicketResult {
  id: string
  status: TicketStatus
}

export interface PatchTicketResult {
  id: string
  status: TicketStatus
}

export interface CreateTicketBody {
  title: string
  description: string
  priority: TicketPriority
  /** Required ACTIVE service UUID (Go Create rejects missing / inactive). */
  service_id: string
}

/** POST /agent/chat — aligns with agent/app/main.py + docs/API.md §14.1 */
export interface AgentChatRequest {
  thread_id: string
  message: string
}

export interface AgentResumeRequest {
  thread_id: string
  action: 'approve' | 'reject'
}

export interface AgentConfirmation {
  thread_id: string
  tool: string
  tool_call_id: string
  args: Record<string, unknown>
}

export interface AgentToolResult {
  tool: string
  args?: Record<string, unknown>
  result?: unknown
}

export interface AgentChatMetadata {
  tools_called?: string[]
  mode?: string
  user_id?: string
  role?: string
  request_id?: string
  pending?: boolean
  confirmation?: AgentConfirmation
  tool_results?: AgentToolResult[]
  [key: string]: unknown
}

export interface AgentChatData {
  thread_id: string
  message_id: string
  message: string
  pending?: boolean
  confirmation?: AgentConfirmation | null
  metadata?: AgentChatMetadata | null
}

/** POST /agent/chat/stream — one object; `type` discriminates. Aligns with agent/app/graph/stream.py */
export type AgentStreamEvent = {
  type: 'start' | 'token' | 'tool_start' | 'tool_end' | 'confirmation' | 'error' | 'done'
  thread_id?: string
  message_id?: string
  request_id?: string
  content?: string
  tool?: string
  tool_call_id?: string
  ok?: boolean
  args?: Record<string, unknown>
  code?: number
  message?: string
  pending?: boolean
  confirmation?: AgentConfirmation | null
  metadata?: AgentChatMetadata | null
}

/** UI card extracted from metadata.tool_results (Ticket shape). */
export interface AgentTicketCard {
  ticket_no?: string
  id?: string
  title?: string
  status?: string
  priority?: string
}

/** UI card extracted from metadata.tool_results (Permission shape). */
export interface AgentPermissionCard {
  resource: string
  level?: string
  status?: string
}
