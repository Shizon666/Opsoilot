import type {
  AgentChatMetadata,
  AgentPermissionCard,
  AgentTicketCard,
  AgentToolResult,
} from '../types/api'

function asRecord(value: unknown): Record<string, unknown> | null {
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    return value as Record<string, unknown>
  }
  return null
}

function str(value: unknown): string | undefined {
  if (typeof value === 'string' && value.trim()) return value
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  return undefined
}

/** Tool result payload is usually { ok, data } after _safe_json. */
function unwrapToolData(raw: unknown): Record<string, unknown> | null {
  const root = asRecord(raw)
  if (!root) return null
  if (root.ok === false) return null
  const data = asRecord(root.data)
  if (data) return data
  // Already a business object (no ok wrapper)
  if ('ticket_no' in root || 'items' in root || 'resource_type' in root || 'id' in root) {
    return root
  }
  return null
}

function toTicketCard(
  item: Record<string, unknown>,
  args?: Record<string, unknown>,
): AgentTicketCard | null {
  const ticket_no = str(item.ticket_no)
  const id = str(item.id)
  const title = str(item.title) ?? str(args?.title)
  const status = str(item.status)
  const priority = str(item.priority) ?? str(args?.priority)
  if (!ticket_no && !id && !title && !status) return null
  return { ticket_no, id, title, status, priority }
}

function toPermissionCard(
  item: Record<string, unknown>,
  args?: Record<string, unknown>,
): AgentPermissionCard | null {
  const resourceType = str(item.resource_type) ?? str(args?.resource_type)
  const resourceName = str(item.resource_name) ?? str(args?.resource_name)
  const resource =
    resourceType && resourceName
      ? `${resourceType} / ${resourceName}`
      : resourceName || resourceType || str(item.resource)
  const level = str(item.permission_level) ?? str(args?.permission_level) ?? str(item.permission)
  const status = str(item.status)
  if (!resource && !level && !status) return null
  return { resource: resource || '—', level, status }
}

function collectFromTool(tr: AgentToolResult): {
  tickets: AgentTicketCard[]
  permissions: AgentPermissionCard[]
} {
  const tickets: AgentTicketCard[] = []
  const permissions: AgentPermissionCard[] = []
  const tool = tr.tool || ''
  const args = asRecord(tr.args) ?? undefined
  const data = unwrapToolData(tr.result)
  if (!data) return { tickets, permissions }

  if (tool === 'get_my_tickets' || tool === 'get_tickets') {
    const items = Array.isArray(data.items) ? data.items : []
    for (const row of items) {
      const rec = asRecord(row)
      if (!rec) continue
      const card = toTicketCard(rec)
      if (card) tickets.push(card)
    }
  } else if (tool === 'create_ticket') {
    const card = toTicketCard(data, args)
    if (card) tickets.push(card)
  } else if (tool === 'get_my_permissions') {
    const items = Array.isArray(data.items) ? data.items : []
    for (const row of items) {
      const rec = asRecord(row)
      if (!rec) continue
      const card = toPermissionCard(rec)
      if (card) permissions.push(card)
    }
  } else if (tool === 'create_permission') {
    const card = toPermissionCard(data, args)
    if (card) permissions.push(card)
  }

  return { tickets, permissions }
}

export function parseAgentCards(metadata?: AgentChatMetadata | null): {
  tickets: AgentTicketCard[]
  permissions: AgentPermissionCard[]
} {
  const tickets: AgentTicketCard[] = []
  const permissions: AgentPermissionCard[] = []
  const results = metadata?.tool_results
  if (!Array.isArray(results)) return { tickets, permissions }

  for (const tr of results) {
    if (!tr || typeof tr !== 'object') continue
    const parsed = collectFromTool(tr)
    tickets.push(...parsed.tickets)
    permissions.push(...parsed.permissions)
  }
  return { tickets, permissions }
}
