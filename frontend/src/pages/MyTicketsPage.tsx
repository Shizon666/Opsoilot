import { useEffect, useState } from 'react'
import { Button, Space, Table, Tag, Typography, message } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { Link, useNavigate } from 'react-router-dom'
import { listTickets } from '../api/tickets'
import { errorMessage } from '../api/client'
import type { Ticket } from '../types/api'
import { priorityLabel, statusColor, statusLabel } from '../utils/ticketStatus'

export function MyTicketsPage() {
  const [items, setItems] = useState<Ticket[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const pageSize = 20

  const load = async (nextPage: number) => {
    setLoading(true)
    try {
      const data = await listTickets({ page: nextPage, page_size: pageSize })
      setItems(data.items || [])
      setTotal(data.total)
      setPage(data.page)
    } catch (err) {
      message.error(errorMessage(err, '加载工单失败'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load(1)
  }, [])

  const columns: ColumnsType<Ticket> = [
    {
      title: '单号',
      dataIndex: 'ticket_no',
      width: 180,
      render: (v: string, row) => <Link to={`/tickets/${row.id}`}>{v}</Link>,
    },
    { title: '标题', dataIndex: 'title', ellipsis: true },
    {
      title: '状态',
      dataIndex: 'status',
      width: 120,
      render: (v: string) => <Tag color={statusColor(v)}>{statusLabel(v)}</Tag>,
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      width: 100,
      render: (v: string) => priorityLabel(v),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 200,
      render: (v: string) => new Date(v).toLocaleString(),
    },
  ]

  return (
    <div>
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 16 }}>
        <Typography.Title level={3} style={{ margin: 0 }}>
          我的工单
        </Typography.Title>
        <Button type="primary" onClick={() => navigate('/tickets/new')}>
          创建工单
        </Button>
      </Space>
      <Table
        rowKey="id"
        loading={loading}
        columns={columns}
        dataSource={items}
        pagination={{
          current: page,
          pageSize,
          total,
          onChange: (p) => void load(p),
        }}
        locale={{ emptyText: '暂无工单，点击右上角创建' }}
      />
    </div>
  )
}
