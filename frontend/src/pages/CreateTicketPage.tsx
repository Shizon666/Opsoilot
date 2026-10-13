import { useEffect, useState } from 'react'
import { Button, Card, Form, Input, Select, Typography, message } from 'antd'
import { useNavigate } from 'react-router-dom'
import { createTicket } from '../api/tickets'
import { listServices } from '../api/services'
import { errorMessage } from '../api/client'
import type { Service, TicketPriority } from '../types/api'
import { serviceOptionLabel } from '../utils/serviceLabels'

interface CreateForm {
  title: string
  description: string
  priority: TicketPriority
  service_id: string
}

export function CreateTicketPage() {
  const [loading, setLoading] = useState(false)
  const [services, setServices] = useState<Service[]>([])
  const [servicesLoading, setServicesLoading] = useState(false)
  const [form] = Form.useForm<CreateForm>()
  const navigate = useNavigate()

  useEffect(() => {
    const load = async () => {
      setServicesLoading(true)
      try {
        const data = await listServices()
        const items = (data.items || [])
          .filter((s) => s.status === 'ACTIVE')
          // Keep business systems first; "其他类型" (GENERAL_IT) last for explicit catch-all.
          .slice()
          .sort((a, b) => {
            const rank = (code: string) => (code === 'GENERAL_IT' ? 1 : 0)
            return rank(a.code) - rank(b.code) || a.code.localeCompare(b.code)
          })
        setServices(items)
        // Never default to GENERAL_IT / 其他类型 — only preselect a known business service.
        const checkout = items.find((s) => s.code === 'CHECKOUT_API')
        if (checkout) {
          form.setFieldsValue({ service_id: checkout.id })
        }
      } catch (err) {
        message.error(errorMessage(err, '加载服务列表失败'))
      } finally {
        setServicesLoading(false)
      }
    }
    void load()
  }, [form])

  const onFinish = async (values: CreateForm) => {
    setLoading(true)
    try {
      const result = await createTicket({
        title: values.title.trim(),
        description: values.description.trim(),
        priority: values.priority,
        service_id: values.service_id,
      })
      message.success('工单已创建')
      navigate(`/tickets/${result.id}`, { replace: true })
    } catch (err) {
      message.error(errorMessage(err, '创建失败'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <Typography.Title level={3}>创建工单</Typography.Title>
      <Typography.Paragraph type="secondary">
        请选择出问题的业务系统；若不属于收银台 / 登录认证 / 订单处理，请选「其他类型」，并简要说明现象。
      </Typography.Paragraph>
      <Card>
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          initialValues={{ priority: 'medium' }}
          style={{ maxWidth: 640 }}
        >
          <Form.Item
            label="问题类型 / 系统"
            name="service_id"
            rules={[{ required: true, message: '请选择问题类型或系统' }]}
            extra="能对应到具体业务系统请优先选系统；VPN、设备、软件安装等请选「其他类型」。"
          >
            <Select
              loading={servicesLoading}
              placeholder="请选择问题类型或系统"
              options={services.map((s) => ({
                value: s.id,
                label: serviceOptionLabel(s.code, s.name),
              }))}
              showSearch
              optionFilterProp="label"
            />
          </Form.Item>
          <Form.Item
            label="问题标题"
            name="title"
            rules={[
              { required: true, message: '请填写问题标题' },
              { max: 200, message: '标题最多 200 字' },
            ]}
          >
            <Input placeholder="例如：收银台无法下单，页面报错" />
          </Form.Item>
          <Form.Item
            label="详细说明"
            name="description"
            rules={[{ required: true, message: '请填写详细说明' }]}
          >
            <Input.TextArea
              rows={5}
              placeholder="请说明：什么时候开始、出现什么报错或现象、影响哪些人/业务"
            />
          </Form.Item>
          <Form.Item
            label="紧急程度"
            name="priority"
            rules={[{ required: true, message: '请选择紧急程度' }]}
          >
            <Select
              options={[
                { value: 'low', label: '低 — 可稍后处理' },
                { value: 'medium', label: '中 — 影响日常工作' },
                { value: 'high', label: '高 — 影响较多用户或业务' },
                { value: 'urgent', label: '紧急 — 业务大面积中断' },
              ]}
            />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              提交工单
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}
