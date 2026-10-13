import { useCallback, useEffect, useState } from 'react'
import {
  Button,
  Form,
  Input,
  Modal,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { listServices, patchService } from '../api/services'
import { errorMessage } from '../api/client'
import type { Service, ServiceHealthStatus } from '../types/api'
import { isSupportRole, useAuthStore } from '../store/authStore'
import {
  healthStatusColor,
  healthStatusLabel,
  serviceDisplayName,
  serviceHint,
} from '../utils/serviceLabels'

const HEALTH_OPTIONS: { value: ServiceHealthStatus; label: string }[] = [
  { value: 'HEALTHY', label: '正常' },
  { value: 'DEGRADED', label: '异常 / 降级' },
  { value: 'DOWN', label: '不可用' },
]

interface EditFormValues {
  health_status: ServiceHealthStatus
  health_summary?: string
}

export function ServiceStatusPage() {
  const user = useAuthStore((s) => s.user)
  const canEdit = isSupportRole(user?.role)

  const [items, setItems] = useState<Service[]>([])
  const [loading, setLoading] = useState(false)
  const [editing, setEditing] = useState<Service | null>(null)
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm<EditFormValues>()

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await listServices()
      setItems(data.items || [])
    } catch (err) {
      message.error(errorMessage(err, '加载服务状态失败'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const openEdit = (row: Service) => {
    setEditing(row)
    form.setFieldsValue({
      health_status: (row.health_status as ServiceHealthStatus) || 'HEALTHY',
      health_summary: row.health_summary || '',
    })
  }

  const closeEdit = () => {
    setEditing(null)
    form.resetFields()
  }

  const onSave = async () => {
    if (!editing) return
    try {
      const values = await form.validateFields()
      setSaving(true)
      const updated = await patchService(editing.id, {
        health_status: values.health_status,
        health_summary: (values.health_summary || '').trim() || null,
      })
      setItems((prev) => prev.map((s) => (s.id === updated.id ? { ...s, ...updated } : s)))
      message.success('服务状态已更新')
      closeEdit()
    } catch (err) {
      if (err && typeof err === 'object' && 'errorFields' in err) return
      message.error(errorMessage(err, '更新失败'))
    } finally {
      setSaving(false)
    }
  }

  const columns: ColumnsType<Service> = [
    {
      title: '服务',
      dataIndex: 'code',
      width: 220,
      render: (code: string, row) => (
        <div>
          <div>{serviceDisplayName(code, row.name)}</div>
          {serviceHint(code) ? (
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              {serviceHint(code)}
            </Typography.Text>
          ) : null}
        </div>
      ),
    },
    {
      title: '当前状态',
      dataIndex: 'health_status',
      width: 140,
      render: (v: string) => (
        <Tag color={healthStatusColor(v)}>{healthStatusLabel(v)}</Tag>
      ),
    },
    {
      title: '情况说明',
      dataIndex: 'health_summary',
      ellipsis: true,
      render: (v: string | null | undefined) => v || '暂无说明',
    },
    {
      title: '最近检查时间',
      dataIndex: 'last_checked_at',
      width: 200,
      render: (v: string | null | undefined) =>
        v ? new Date(v).toLocaleString('zh-CN') : '暂无',
    },
  ]

  if (canEdit) {
    columns.push({
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_, row) => (
        <Button type="link" style={{ padding: 0 }} onClick={() => openEdit(row)}>
          修改
        </Button>
      ),
    })
  }

  return (
    <div>
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 16 }}>
        <div>
          <Typography.Title level={3} style={{ margin: 0 }}>
            服务状态
          </Typography.Title>
          <Typography.Text type="secondary">
            {canEdit
              ? '可手动更新各业务系统健康状态（模拟），员工侧与 Agent 会看到最新结果。'
              : '查看各业务系统当前是否正常，方便报障时对照。仅 IT 支持 / 管理员可修改。'}
          </Typography.Text>
        </div>
      </Space>
      <Table
        rowKey="id"
        loading={loading}
        columns={columns}
        dataSource={items}
        pagination={false}
        locale={{ emptyText: '暂无服务数据' }}
      />

      <Modal
        title={
          editing
            ? `修改状态 · ${serviceDisplayName(editing.code, editing.name)}`
            : '修改服务状态'
        }
        open={!!editing}
        onCancel={closeEdit}
        onOk={() => void onSave()}
        confirmLoading={saving}
        destroyOnClose
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="health_status"
            label="健康状态"
            rules={[{ required: true, message: '请选择状态' }]}
          >
            <Select options={HEALTH_OPTIONS} />
          </Form.Item>
          <Form.Item name="health_summary" label="情况说明">
            <Input.TextArea rows={3} placeholder="例如：收银台 5xx 升高，支付超时增多" maxLength={500} showCount />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
