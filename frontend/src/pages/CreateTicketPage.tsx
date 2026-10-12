import { useState } from 'react'
import { Button, Card, Form, Input, Select, Typography, message } from 'antd'
import { useNavigate } from 'react-router-dom'
import { createTicket } from '../api/tickets'
import { errorMessage } from '../api/client'
import type { TicketPriority } from '../types/api'

interface CreateForm {
  title: string
  description: string
  priority: TicketPriority
}

export function CreateTicketPage() {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const onFinish = async (values: CreateForm) => {
    setLoading(true)
    try {
      const result = await createTicket({
        title: values.title.trim(),
        description: values.description.trim(),
        priority: values.priority,
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
      <Card>
        <Form
          layout="vertical"
          onFinish={onFinish}
          initialValues={{ priority: 'medium' }}
          style={{ maxWidth: 640 }}
        >
          <Form.Item
            label="标题"
            name="title"
            rules={[
              { required: true, message: '请输入标题' },
              { max: 200, message: '标题最多 200 字' },
            ]}
          >
            <Input placeholder="简要描述问题" />
          </Form.Item>
          <Form.Item
            label="描述"
            name="description"
            rules={[{ required: true, message: '请输入描述' }]}
          >
            <Input.TextArea rows={5} placeholder="补充现象、环境与期望" />
          </Form.Item>
          <Form.Item
            label="优先级"
            name="priority"
            rules={[{ required: true, message: '请选择优先级' }]}
          >
            <Select
              options={[
                { value: 'low', label: '低' },
                { value: 'medium', label: '中' },
                { value: 'high', label: '高' },
                { value: 'urgent', label: '紧急' },
              ]}
            />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              提交
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}
