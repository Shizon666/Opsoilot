import { Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from '../components/AppLayout'
import { RequireAuth } from '../components/RequireAuth'
import { LoginPage } from '../pages/LoginPage'
import { MyTicketsPage } from '../pages/MyTicketsPage'
import { CreateTicketPage } from '../pages/CreateTicketPage'
import { TicketDetailPage } from '../pages/TicketDetailPage'
import { SupportTicketsPage } from '../pages/SupportTicketsPage'
import { SupportTicketDetailPage } from '../pages/SupportTicketDetailPage'
import { AgentChatPage } from '../pages/AgentChatPage'
import { ServiceStatusPage } from '../pages/ServiceStatusPage'
import { isSupportRole, useAuthStore } from '../store/authStore'

function HomeRedirect() {
  const user = useAuthStore((s) => s.user)
  if (!user) return <Navigate to="/login" replace />
  return <Navigate to={isSupportRole(user.role) ? '/support' : '/agent/chat'} replace />
}

export function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route element={<RequireAuth />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<HomeRedirect />} />
          <Route path="/services" element={<ServiceStatusPage />} />

          <Route element={<RequireAuth roles={['employee']} />}>
            <Route path="/my-tickets" element={<MyTicketsPage />} />
            <Route path="/tickets/new" element={<CreateTicketPage />} />
            <Route path="/tickets/:id" element={<TicketDetailPage />} />
            <Route path="/agent/chat" element={<AgentChatPage />} />
          </Route>

          <Route element={<RequireAuth roles={['it_support', 'admin']} />}>
            <Route path="/support" element={<SupportTicketsPage />} />
            <Route path="/support/tickets/:id" element={<SupportTicketDetailPage />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
