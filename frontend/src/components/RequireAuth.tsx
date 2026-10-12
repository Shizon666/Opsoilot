import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { Spin } from 'antd'
import { isSupportRole, useAuthStore } from '../store/authStore'
import type { UserRole } from '../types/api'

interface RequireAuthProps {
  roles?: UserRole[]
}

export function RequireAuth({ roles }: RequireAuthProps) {
  const token = useAuthStore((s) => s.token)
  const user = useAuthStore((s) => s.user)
  const hydrated = useAuthStore((s) => s.hydrated)
  const location = useLocation()

  if (!hydrated) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 120 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!token || !user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  if (roles && !roles.includes(user.role)) {
    const fallback = isSupportRole(user.role) ? '/support' : '/agent/chat'
    return <Navigate to={fallback} replace />
  }

  return <Outlet />
}
