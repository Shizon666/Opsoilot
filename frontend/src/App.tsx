import { ConfigProvider } from 'antd'
import { BrowserRouter } from 'react-router-dom'
import { useEffect } from 'react'
import { AppRouter } from './router'
import { useAuthStore } from './store/authStore'

function App() {
  const hydrate = useAuthStore((s) => s.hydrate)

  useEffect(() => {
    void hydrate()
  }, [hydrate])

  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#1677ff',
          borderRadius: 6,
        },
      }}
    >
      <BrowserRouter>
        <AppRouter />
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
