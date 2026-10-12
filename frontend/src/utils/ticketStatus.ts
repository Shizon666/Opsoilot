import type { TicketPriority, TicketStatus } from '../types/api'

/** UI-only next-action hints. Backend Service state machine is the authority. */
export interface StatusAction {
  label: string
  nextStatus: TicketStatus
}

const STATUS_ACTIONS: Record<TicketStatus, StatusAction[]> = {
  open: [{ label: '认领', nextStatus: 'assigned' }],
  assigned: [{ label: '开始处理', nextStatus: 'in_progress' }],
  in_progress: [
    { label: '等待用户', nextStatus: 'waiting_user' },
    { label: '标记解决', nextStatus: 'resolved' },
  ],
  waiting_user: [{ label: '继续处理', nextStatus: 'in_progress' }],
  resolved: [{ label: '关闭', nextStatus: 'closed' }],
  closed: [],
}

export function getStatusActions(status: TicketStatus): StatusAction[] {
  return STATUS_ACTIONS[status] ?? []
}

const STATUS_LABEL: Record<TicketStatus, string> = {
  open: '待处理',
  assigned: '已分配',
  in_progress: '处理中',
  waiting_user: '等待用户',
  resolved: '已解决',
  closed: '已关闭',
}

const PRIORITY_LABEL: Record<TicketPriority, string> = {
  low: '低',
  medium: '中',
  high: '高',
  urgent: '紧急',
}

export function statusLabel(status: string): string {
  return STATUS_LABEL[status as TicketStatus] ?? status
}

export function priorityLabel(priority: string): string {
  return PRIORITY_LABEL[priority as TicketPriority] ?? priority
}

export function statusColor(
  status: string,
): 'default' | 'processing' | 'success' | 'warning' | 'error' {
  switch (status) {
    case 'open':
      return 'warning'
    case 'assigned':
    case 'in_progress':
      return 'processing'
    case 'waiting_user':
      return 'default'
    case 'resolved':
      return 'success'
    case 'closed':
      return 'default'
    default:
      return 'default'
  }
}
