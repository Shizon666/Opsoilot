import { useEffect, useRef, useState } from 'react'
import { Button, Card, Input, Space, Tag, Typography, message } from 'antd'
import { postAgentResume, streamAgentChat } from '../api/agent'
import { errorMessage } from '../api/client'
import type { AgentChatData, AgentPermissionCard, AgentTicketCard } from '../types/api'
import {
  type ChatMessage,
  selectThreadMessages,
  useAgentChatStore,
} from '../store/agentChatStore'
import { parseAgentCards } from '../utils/parseAgentCards'
import { getOrCreateThreadId } from '../utils/threadId'
import { priorityLabel, statusColor, statusLabel } from '../utils/ticketStatus'

function TicketCards({ items }: { items: AgentTicketCard[] }) {
  if (!items.length) return null
  return (
    <Space direction="vertical" size={8} style={{ width: '100%', marginTop: 8 }}>
      {items.map((t, i) => (
        <Card
          key={`${t.ticket_no || t.id || 't'}-${i}`}
          size="small"
          title="Ticket"
          styles={{ body: { paddingBlock: 12 } }}
        >
          <Typography.Paragraph style={{ marginBottom: 4 }}>
            编号：{t.ticket_no || t.id || '—'}
          </Typography.Paragraph>
          <Typography.Paragraph style={{ marginBottom: 4 }}>
            标题：{t.title || '—'}
          </Typography.Paragraph>
          <Typography.Paragraph style={{ marginBottom: 4 }}>
            状态：{t.status ? <Tag color={statusColor(t.status)}>{statusLabel(t.status)}</Tag> : '—'}
          </Typography.Paragraph>
          <Typography.Paragraph style={{ marginBottom: 0 }}>
            优先级：{t.priority ? priorityLabel(t.priority) : '—'}
          </Typography.Paragraph>
        </Card>
      ))}
    </Space>
  )
}

function PermissionCards({ items }: { items: AgentPermissionCard[] }) {
  if (!items.length) return null
  return (
    <Space direction="vertical" size={8} style={{ width: '100%', marginTop: 8 }}>
      {items.map((p, i) => (
        <Card
          key={`${p.resource}-${p.level || ''}-${i}`}
          size="small"
          title="Permission"
          styles={{ body: { paddingBlock: 12 } }}
        >
          <Typography.Paragraph style={{ marginBottom: 4 }}>资源：{p.resource}</Typography.Paragraph>
          <Typography.Paragraph style={{ marginBottom: 4 }}>等级：{p.level || '—'}</Typography.Paragraph>
          <Typography.Paragraph style={{ marginBottom: 0 }}>状态：{p.status || '—'}</Typography.Paragraph>
        </Card>
      ))}
    </Space>
  )
}

function assistantFromChat(data: AgentChatData): ChatMessage {
  const pending = Boolean(data.pending && data.confirmation)
  const { tickets, permissions } = pending
    ? { tickets: [] as AgentTicketCard[], permissions: [] as AgentPermissionCard[] }
    : parseAgentCards(data.metadata)
  return {
    id: data.message_id || `a_${Date.now()}`,
    role: 'assistant',
    text: data.message || '（无回复内容）',
    tickets,
    permissions,
    pending,
    confirmation: pending ? data.confirmation : null,
  }
}

function formatConfirmArgs(args: Record<string, unknown> | undefined): string {
  if (!args || !Object.keys(args).length) return '（无参数）'
  return Object.entries(args)
    .map(([k, v]) => `${k}：${typeof v === 'string' ? v : JSON.stringify(v)}`)
    .join('\n')
}

export function AgentChatPage() {
  const [threadId] = useState(getOrCreateThreadId)
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [resuming, setResuming] = useState(false)
  const messages = useAgentChatStore(selectThreadMessages(threadId))
  const setMessages = useAgentChatStore((s) => s.setMessages)
  const bottomRef = useRef<HTMLDivElement>(null)
  const pending = messages.some((m) => m.pending)
  const busy = sending || resuming

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, sending, resuming])

  const send = async () => {
    const text = input.trim()
    if (!text || busy || pending) return

    const userMsg: ChatMessage = {
      id: `u_${Date.now()}`,
      role: 'user',
      text,
    }
    const assistantId = `a_${Date.now()}`
    const assistantMsg: ChatMessage = {
      id: assistantId,
      role: 'assistant',
      text: '',
    }
    setMessages(threadId, (prev) => [...prev, userMsg, assistantMsg])
    setInput('')
    setSending(true)

    const failBubble = (errText: string) => {
      setMessages(threadId, (prev) =>
        prev.map((m) => (m.id === assistantId ? { ...m, text: errText, pending: false, confirmation: null } : m)),
      )
    }

    try {
      await streamAgentChat({ thread_id: threadId, message: text }, (ev) => {
        if (ev.type === 'token' && ev.content) {
          setMessages(threadId, (prev) =>
            prev.map((m) => (m.id === assistantId ? { ...m, text: m.text + ev.content } : m)),
          )
          return
        }
        if (ev.type === 'confirmation') {
          setMessages(threadId, (prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    pending: true,
                    confirmation: {
                      thread_id: ev.thread_id || threadId,
                      tool: ev.tool || '',
                      tool_call_id: ev.tool_call_id || '',
                      args: ev.args && typeof ev.args === 'object' ? ev.args : {},
                    },
                  }
                : m,
            ),
          )
          return
        }
        if (ev.type === 'error') {
          const errText = `请求失败：${ev.message || '未知错误'}`
          failBubble(errText)
          message.error(ev.message || 'Agent 请求失败')
          return
        }
        if (ev.type === 'done') {
          const isPending = Boolean(ev.pending && ev.confirmation)
          const { tickets, permissions } = isPending
            ? { tickets: [] as AgentTicketCard[], permissions: [] as AgentPermissionCard[] }
            : parseAgentCards(ev.metadata)
          setMessages(threadId, (prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    text: ev.message || '（无回复内容）',
                    tickets,
                    permissions,
                    pending: isPending,
                    confirmation: isPending ? ev.confirmation : null,
                  }
                : m,
            ),
          )
        }
      })
    } catch (err) {
      message.error(errorMessage(err, 'Agent 请求失败'))
      failBubble(`请求失败：${errorMessage(err, '未知错误')}`)
    } finally {
      setSending(false)
    }
  }

  const resume = async (action: 'approve' | 'reject') => {
    if (resuming || !pending) return
    setResuming(true)
    try {
      const data = await postAgentResume({ thread_id: threadId, action })
      const next = assistantFromChat(data)
      setMessages(threadId, (prev) => {
        const idx = [...prev].reverse().findIndex((m) => m.pending)
        if (idx < 0) return [...prev, next]
        const at = prev.length - 1 - idx
        const copy = [...prev]
        copy[at] = { ...next, id: copy[at].id }
        return copy
      })
    } catch (err) {
      message.error(errorMessage(err, '确认请求失败'))
    } finally {
      setResuming(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 140px)' }}>
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 16 }}>
        <Typography.Title level={3} style={{ margin: 0 }}>
          IT Agent
        </Typography.Title>
        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
          thread: {threadId.slice(0, 24)}…
        </Typography.Text>
      </Space>

      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: 16,
          background: '#fafafa',
          border: '1px solid #f0f0f0',
          borderRadius: 8,
          marginBottom: 16,
        }}
      >
        {messages.length === 0 && (
          <Typography.Paragraph type="secondary" style={{ margin: 0 }}>
            试试：「下单一直 502，checkout 付不了款，帮我创建工单」「我的工单有哪些」
          </Typography.Paragraph>
        )}
        <Space direction="vertical" size={12} style={{ width: '100%' }}>
          {messages.map((m) => (
            <div
              key={m.id}
              style={{
                display: 'flex',
                justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start',
              }}
            >
              <div
                style={{
                  maxWidth: '85%',
                  padding: '10px 14px',
                  borderRadius: 8,
                  background: m.role === 'user' ? '#1677ff' : '#fff',
                  color: m.role === 'user' ? '#fff' : 'inherit',
                  border: m.role === 'assistant' ? '1px solid #f0f0f0' : undefined,
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                <Typography.Text style={{ color: 'inherit' }}>{m.text}</Typography.Text>
                {m.role === 'assistant' && m.pending && m.confirmation && (
                  <div style={{ marginTop: 8 }}>
                    <Typography.Paragraph style={{ marginBottom: 4 }}>
                      待确认：{m.confirmation.tool}
                    </Typography.Paragraph>
                    <Typography.Paragraph
                      style={{ marginBottom: 8, whiteSpace: 'pre-wrap' }}
                    >
                      {formatConfirmArgs(m.confirmation.args)}
                    </Typography.Paragraph>
                    <Space>
                      <Button
                        type="primary"
                        size="small"
                        loading={resuming}
                        disabled={resuming}
                        onClick={() => void resume('approve')}
                      >
                        确认提交
                      </Button>
                      <Button
                        size="small"
                        loading={resuming}
                        disabled={resuming}
                        onClick={() => void resume('reject')}
                      >
                        取消
                      </Button>
                    </Space>
                  </div>
                )}
                {m.role === 'assistant' && !m.pending && (
                  <>
                    <TicketCards items={m.tickets || []} />
                    <PermissionCards items={m.permissions || []} />
                  </>
                )}
              </div>
            </div>
          ))}
          {sending && (
            <Typography.Text type="secondary">Agent 思考中…</Typography.Text>
          )}
        </Space>
        <div ref={bottomRef} />
      </div>

      <Space.Compact style={{ width: '100%' }}>
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onPressEnter={(e) => {
            if (!e.shiftKey) {
              e.preventDefault()
              void send()
            }
          }}
          placeholder={pending ? '请先确认或取消当前提交' : '输入消息，Enter 发送'}
          disabled={busy || pending}
          maxLength={4000}
        />
        <Button
          type="primary"
          onClick={() => void send()}
          loading={sending}
          disabled={!input.trim() || busy || pending}
        >
          发送
        </Button>
      </Space.Compact>
    </div>
  )
}
