import { Layout, Menu, Button, Typography, Space, theme } from 'antd'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { isSupportRole, useAuthStore } from '../store/authStore'

const { Header, Content } = Layout

export function AppLayout() {
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  const navigate = useNavigate()
  const location = useLocation()
  const { token: themeToken } = theme.useToken()

  const support = isSupportRole(user?.role)

  const selectedKey = (() => {
    if (location.pathname.startsWith('/support')) return 'support'
    if (location.pathname.startsWith('/services')) return 'services'
    if (location.pathname.startsWith('/agent/chat')) return 'agent-chat'
    if (location.pathname.startsWith('/tickets/new')) return 'create'
    if (location.pathname.startsWith('/my-tickets') || location.pathname.startsWith('/tickets/')) {
      return 'my-tickets'
    }
    return ''
  })()

  const menuItems = support
    ? [
        { key: 'support', label: <Link to="/support">工单工作台</Link> },
        { key: 'services', label: <Link to="/services">服务状态</Link> },
      ]
    : [
        { key: 'agent-chat', label: <Link to="/agent/chat">IT Agent</Link> },
        { key: 'services', label: <Link to="/services">服务状态</Link> },
        { key: 'my-tickets', label: <Link to="/my-tickets">我的工单</Link> },
        { key: 'create', label: <Link to="/tickets/new">创建工单</Link> },
      ]

  const onLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 24,
          background: themeToken.colorBgContainer,
          borderBottom: `1px solid ${themeToken.colorBorderSecondary}`,
          paddingInline: 24,
        }}
      >
        <Typography.Title level={4} style={{ margin: 0, whiteSpace: 'nowrap' }}>
          OpsPilot
        </Typography.Title>
        <Menu
          mode="horizontal"
          selectedKeys={selectedKey ? [selectedKey] : []}
          items={menuItems}
          style={{ flex: 1, minWidth: 0, border: 'none' }}
        />
        <Space>
          <Typography.Text type="secondary">
            {user?.name}（{user?.role}）
          </Typography.Text>
          <Button onClick={onLogout}>退出</Button>
        </Space>
      </Header>
      <Content style={{ padding: 24, maxWidth: 1100, width: '100%', margin: '0 auto' }}>
        <Outlet />
      </Content>
    </Layout>
  )
}
