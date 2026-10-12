import { useEffect, useState } from 'react'
import { Button, Card, Form, Input, Typography, message } from 'antd'
import { Navigate, useNavigate } from 'react-router-dom'
import { errorMessage } from '../api/client'
import { isSupportRole, useAuthStore } from '../store/authStore'

interface LoginForm {
  username: string
  password: string
}

export function LoginPage() {
  const login = useAuthStore((s) => s.login)
  const token = useAuthStore((s) => s.token)
  const user = useAuthStore((s) => s.user)
  const hydrated = useAuthStore((s) => s.hydrated)
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (hydrated && token && user) {
      navigate(isSupportRole(user.role) ? '/support' : '/agent/chat', { replace: true })
    }
  }, [hydrated, token, user, navigate])

  if (hydrated && token && user) {
    return <Navigate to={isSupportRole(user.role) ? '/support' : '/agent/chat'} replace />
  }

  const onFinish = async (values: LoginForm) => {
    setLoading(true)
    try {
      const loggedIn = await login(values.username.trim(), values.password)
      message.success('登录成功')
      navigate(isSupportRole(loggedIn.role) ? '/support' : '/agent/chat', { replace: true })
    } catch (err) {
      message.error(errorMessage(err, '登录失败'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 24,
        background: '#f5f5f5',
      }}
    >
      <Card style={{ width: 400 }} title="OpsPilot 登录">
        <Typography.Paragraph type="secondary" style={{ marginTop: 0 }}>
          演示账号：demo@opspilot.local / support@opspilot.local
          <br />
          密码：password123
        </Typography.Paragraph>
        <Form layout="vertical" onFinish={onFinish} requiredMark={false}>
          <Form.Item
            label="用户名"
            name="username"
            rules={[{ required: true, message: '请输入用户名（邮箱）' }]}
          >
            <Input placeholder="email" autoComplete="username" />
          </Form.Item>
          <Form.Item
            label="密码"
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password placeholder="password" autoComplete="current-password" />
          </Form.Item>
          <Button type="primary" htmlType="submit" block loading={loading}>
            登录
          </Button>
        </Form>
      </Card>
    </div>
  )
}
