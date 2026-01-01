/**
 * Dashboard layout with navigation and header.
 */

import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/button'

export function DashboardLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { logout } = useAuth()

  async function handleLogout() {
    try {
      await logout()
      navigate('/login')
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  const isActive = (path: string) => location.pathname === path

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">🐦 Chirp</h1>
              <nav className="ml-10 flex space-x-8">
                <button
                  onClick={() => navigate('/dashboard')}
                  className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    isActive('/dashboard')
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                >
                  Bots
                </button>
              </nav>
            </div>

            <div className="flex items-center space-x-4">
              <Button
                onClick={handleLogout}
                variant="outline"
                size="sm"
              >
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  )
}
