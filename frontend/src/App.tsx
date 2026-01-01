import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { LoginPage } from '@/pages/LoginPage'
import { DashboardLayout } from '@/components/DashboardLayout'
import { BotsPage } from '@/pages/BotsPage'
import { BotFormPage } from '@/pages/BotFormPage'
import { BotTestPage } from '@/pages/BotTestPage'
import { ProtectedRoute } from '@/components/ProtectedRoute'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<BotsPage />} />
            <Route path="bots/new" element={<BotFormPage />} />
            <Route path="bots/:id" element={<BotFormPage />} />
            <Route path="bots/:id/test" element={<BotTestPage />} />
          </Route>

          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
