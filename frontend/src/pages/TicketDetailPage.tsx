import { useCallback, useEffect, useState } from 'react'
import { Button, Card, Descriptions, Spin, Tag, Typography, message } from 'antd'
import { Link, useParams } from 'react-router-dom'
import { getTicket } from '../api/tickets'
import { errorMessage } from '../api/client'
import type { Ticket } from '../types/api'
import { priorityLabel, statusColor, statusLabel } from '../utils/ticketStatus'

export function TicketDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [loading, setLoading] = useState(true)

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

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Link to="/my-tickets">← 返回我的工单</Link>
      </div>
      <Typography.Title level={3} style={{ marginTop: 0 }}>
        {ticket.title}
      </Typography.Title>
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
          <Descriptions.Item label="创建时间">
            {new Date(ticket.created_at).toLocaleString()}
          </Descriptions.Item>
          <Descriptions.Item label="更新时间">
            {new Date(ticket.updated_at).toLocaleString()}
          </Descriptions.Item>
        </Descriptions>
      </Card>
      <Button style={{ marginTop: 16 }} onClick={() => void load()}>
        刷新
      </Button>
    </div>
  )
}
