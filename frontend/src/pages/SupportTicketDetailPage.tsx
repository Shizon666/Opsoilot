import { useCallback, useEffect, useState } from 'react'
import {
  Button,
  Card,
  Descriptions,
  Input,
  Modal,
  Space,
  Spin,
  Tag,
  Typography,
  message,
} from 'antd'
import { Link, useParams } from 'react-router-dom'
import { getTicket, patchTicketStatus } from '../api/tickets'
import { errorMessage } from '../api/client'
import type { Ticket, TicketStatus } from '../types/api'
import { getStatusActions, priorityLabel, statusColor, statusLabel } from '../utils/ticketStatus'

export function SupportTicketDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [loading, setLoading] = useState(true)
  const [acting, setActing] = useState(false)
  const [waitModalOpen, setWaitModalOpen] = useState(false)
  const [waitNote, setWaitNote] = useState('')

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

  const applyStatus = async (nextStatus: TicketStatus, analysis?: string) => {
    if (!id) return
    setActing(true)
    try {
      await patchTicketStatus(
        id,
        nextStatus,
        analysis !== undefined ? { analysis } : undefined,
      )
      message.success('状态已更新')
      setWaitModalOpen(false)
      setWaitNote('')
      await load()
    } catch (err) {
      message.error(errorMessage(err, '状态更新失败'))
      await load()
    } finally {
      setActing(false)
    }
  }

  const onAction = (nextStatus: TicketStatus) => {
    if (nextStatus === 'waiting_user') {
      setWaitNote(ticket?.analysis?.trim() || '')
      setWaitModalOpen(true)
      return
    }
    void applyStatus(nextStatus)
  }

  const onConfirmWait = () => {
    const note = waitNote.trim()
    if (!note) {
      message.warning('请填写需要用户补充的内容')
      return
    }
    void applyStatus('waiting_user', note)
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
        工单不存在或无权查看。<Link to="/support">返回工作台</Link>
      </Typography.Paragraph>
    )
  }

  const actions = getStatusActions(ticket.status)

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Link to="/support">← 返回工作台</Link>
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
          {ticket.analysis ? (
            <Descriptions.Item label="待用户处理 / 分析说明">
              <Typography.Paragraph style={{ marginBottom: 0, whiteSpace: 'pre-wrap' }}>
                {ticket.analysis}
              </Typography.Paragraph>
            </Descriptions.Item>
          ) : null}
          <Descriptions.Item label="创建人 ID">{ticket.creator_id}</Descriptions.Item>
          <Descriptions.Item label="处理人 ID">
            {ticket.assignee_id || '—'}
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {new Date(ticket.created_at).toLocaleString()}
          </Descriptions.Item>
          <Descriptions.Item label="更新时间">
            {new Date(ticket.updated_at).toLocaleString()}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="状态操作" style={{ marginTop: 16 }}>
        {actions.length === 0 ? (
          <Typography.Text type="secondary">当前状态无可推进操作。</Typography.Text>
        ) : (
          <Space wrap>
            {actions.map((action) => (
              <Button
                key={action.nextStatus}
                type="primary"
                loading={acting}
                onClick={() => onAction(action.nextStatus)}
              >
                {action.label}
              </Button>
            ))}
          </Space>
        )}
        <Typography.Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
          「等待用户」需填写说明；用户补充后工单会回到处理中。
        </Typography.Paragraph>
      </Card>

      <Modal
        title="等待用户处理"
        open={waitModalOpen}
        onOk={onConfirmWait}
        onCancel={() => {
          if (!acting) {
            setWaitModalOpen(false)
            setWaitNote('')
          }
        }}
        confirmLoading={acting}
        okText="确认等待用户"
        destroyOnClose
      >
        <Typography.Paragraph type="secondary">
          请说明需要用户补充或确认的内容，用户将在「我的工单」中看到并回复。
        </Typography.Paragraph>
        <Input.TextArea
          rows={4}
          value={waitNote}
          onChange={(e) => setWaitNote(e.target.value)}
          placeholder="例如：请提供报错截图、发生时间、是否可复现…"
          maxLength={2000}
          showCount
        />
      </Modal>
    </div>
  )
}
