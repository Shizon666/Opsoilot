import { useCallback, useEffect, useState } from 'react'
import { Alert, Button, Card, Descriptions, Input, Spin, Tag, Typography, message } from 'antd'
import { Link, useParams } from 'react-router-dom'
import { getTicket, patchTicket } from '../api/tickets'
import { errorMessage } from '../api/client'
import type { Ticket } from '../types/api'
import { priorityLabel, statusColor, statusLabel } from '../utils/ticketStatus'

const SUPPLEMENT_MARKER = '【用户补充】'

function appendSupplement(description: string, supplement: string): string {
  const base = description.trimEnd()
  const block = `${SUPPLEMENT_MARKER}\n${supplement.trim()}`
  return `${base}\n\n---\n${block}`
}

export function TicketDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [loading, setLoading] = useState(true)
  const [supplement, setSupplement] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const load = useCallback(async () => {
    if (!id) return
    setLoading(true)
    try {
      const data = await getTicket(id)
      setTicket(data)
    } catch (err) {
      setTicket(null)
      message.error(errorMessage(err, '加载详情失败'))
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    void load()
  }, [load])

  const onSubmitSupplement = async () => {
    if (!id || !ticket) return
    const text = supplement.trim()
    if (!text) {
      message.warning('请填写补充说明')
      return
    }
    setSubmitting(true)
    try {
      await patchTicket(id, {
        description: appendSupplement(ticket.description, text),
        status: 'in_progress',
      })
      message.success('已提交，工单已回到处理中')
      setSupplement('')
      await load()
    } catch (err) {
      message.error(errorMessage(err, '提交失败'))
      await load()
    } finally {
      setSubmitting(false)
    }
  }

  if (loading && !ticket) {
    return (
      <div style={{ textAlign: 'center', paddingTop: 80 }}>
        <Spin />
      </div>
    )
  }

  if (!ticket) {
    return (
      <Typography.Paragraph>
        工单不存在或无权查看。<Link to="/my-tickets">返回列表</Link>
      </Typography.Paragraph>
    )
  }

  const waitingUser = ticket.status === 'waiting_user'

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Link to="/my-tickets">← 返回我的工单</Link>
      </div>
      <Typography.Title level={3} style={{ marginTop: 0 }}>
        {ticket.title}
      </Typography.Title>

      {waitingUser ? (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
          message="需要你处理"
          description="IT 支持正在等待你补充信息。请在下方查看说明并提交补充内容。"
        />
      ) : null}

      <Card loading={loading}>
        <Descriptions column={1} bordered size="middle">
          <Descriptions.Item label="单号">{ticket.ticket_no}</Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={statusColor(ticket.status)}>{statusLabel(ticket.status)}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="优先级">{priorityLabel(ticket.priority)}</Descriptions.Item>
          <Descriptions.Item label="描述">
            <Typography.Paragraph style={{ marginBottom: 0, whiteSpace: 'pre-wrap' }}>
              {ticket.description}
            </Typography.Paragraph>
          </Descriptions.Item>
          {ticket.analysis ? (
            <Descriptions.Item label={waitingUser ? '需要你补充' : '分析说明'}>
              <Typography.Paragraph style={{ marginBottom: 0, whiteSpace: 'pre-wrap' }}>
                {ticket.analysis}
              </Typography.Paragraph>
            </Descriptions.Item>
          ) : null}
          <Descriptions.Item label="创建时间">
            {new Date(ticket.created_at).toLocaleString()}
          </Descriptions.Item>
          <Descriptions.Item label="更新时间">
            {new Date(ticket.updated_at).toLocaleString()}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {waitingUser ? (
        <Card title="补充信息" style={{ marginTop: 16 }}>
          {!ticket.analysis ? (
            <Typography.Paragraph type="secondary">
              支持尚未填写具体说明，你仍可补充相关信息后提交。
            </Typography.Paragraph>
          ) : null}
          <Input.TextArea
            rows={4}
            value={supplement}
            onChange={(e) => setSupplement(e.target.value)}
            placeholder="请按上方说明补充信息…"
            maxLength={4000}
            showCount
            disabled={submitting}
          />
          <Button
            type="primary"
            style={{ marginTop: 12 }}
            loading={submitting}
            onClick={() => void onSubmitSupplement()}
          >
            已补充，请继续处理
          </Button>
        </Card>
      ) : (
        <Button style={{ marginTop: 16 }} onClick={() => void load()}>
          刷新
        </Button>
      )}
    </div>
  )
}
