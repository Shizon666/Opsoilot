import { useEffect, useState } from 'react'
import { Space, Table, Tag, Typography, message } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { listServices } from '../api/services'
import { errorMessage } from '../api/client'
import type { Service } from '../types/api'

function healthColor(status: string): string {
  if (status === 'HEALTHY') return 'success'
  if (status === 'DEGRADED') return 'warning'
  if (status === 'DOWN') return 'error'
  return 'default'
}

export function ServiceStatusPage() {
  const [items, setItems] = useState<Service[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const data = await listServices()
        setItems(data.items || [])
      } catch (err) {
        message.error(errorMessage(err, '加载服务状态失败'))
      } finally {
        setLoading(false)
      }
    }
    void load()
  }, [])

  const columns: ColumnsType<Service> = [
    { title: 'code', dataIndex: 'code', width: 180 },
    { title: 'name', dataIndex: 'name', ellipsis: true },
    {
      title: 'health_status',
      dataIndex: 'health_status',
      width: 140,
      render: (v: string) => <Tag color={healthColor(v)}>{v || '—'}</Tag>,
    },
    {
      title: 'health_summary',
      dataIndex: 'health_summary',
      ellipsis: true,
      render: (v: string | null | undefined) => v || '—',
    },
    {
      title: 'last_checked_at',
      dataIndex: 'last_checked_at',
      width: 200,
      render: (v: string | null | undefined) => (v ? new Date(v).toLocaleString() : '—'),
    },
  ]

  return (
    <div>
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 16 }}>
        <Typography.Title level={3} style={{ margin: 0 }}>
          服务状态
        </Typography.Title>
      </Space>
      <Table
        rowKey="id"
        loading={loading}
        columns={columns}
        dataSource={items}
        pagination={false}
        locale={{ emptyText: '暂无服务' }}
      />
    </div>
  )
}
