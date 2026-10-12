import { useEffect, useState } from 'react'
import { Select, Space, Table, Tag, Typography, message } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { Link } from 'react-router-dom'
import { listTickets } from '../api/tickets'
import { errorMessage } from '../api/client'
import type { Ticket } from '../types/api'
import { priorityLabel, statusColor, statusLabel } from '../utils/ticketStatus'

export function SupportTicketsPage() {
  const [items, setItems] = useState<Ticket[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const [loading, setLoading] = useState(false)
  const pageSize = 20

  const load = async (nextPage: number, status?: string) => {
    setLoading(true)
    try {
      const data = await listTickets({
        page: nextPage,
        page_size: pageSize,
        status: status || undefined,
      })
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
    void load(1, statusFilter)
  }, [statusFilter])

  const columns: ColumnsType<Ticket> = [
    {
      title: '单号',
      dataIndex: 'ticket_no',
      width: 180,
      render: (v: string, row) => <Link to={`/support/tickets/${row.id}`}>{v}</Link>,
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
          工单工作台
        </Typography.Title>
        <Select
          allowClear
          placeholder="按状态筛选"
          style={{ width: 180 }}
          value={statusFilter}
          onChange={(v) => setStatusFilter(v)}
          options={[
            { value: 'open', label: '待处理' },
            { value: 'assigned', label: '已分配' },
            { value: 'in_progress', label: '处理中' },
            { value: 'waiting_user', label: '等待用户' },
            { value: 'resolved', label: '已解决' },
            { value: 'closed', label: '已关闭' },
          ]}
        />
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
          onChange: (p) => void load(p, statusFilter),
        }}
        locale={{ emptyText: '暂无工单' }}
      />
    </div>
  )
}
