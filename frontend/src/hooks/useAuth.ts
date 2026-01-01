/**
 * Authentication hook for managing login state.
 */

import { useState, useEffect } from 'react'
import { authApi } from '@/lib/api'

export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    checkAuth()
  }, [])

  async function checkAuth() {
    try {
      const authenticated = await authApi.checkAuth()
      setIsAuthenticated(authenticated)
    } catch (error) {
      setIsAuthenticated(false)
    } finally {
      setIsLoading(false)
    }
  }

  async function login(username: string, password: string) {
    await authApi.login(username, password)
    setIsAuthenticated(true)
  }

  async function logout() {
    await authApi.logout()
    setIsAuthenticated(false)
  }

  return {
    isAuthenticated,
    isLoading,
    login,
    logout,
    checkAuth,
  }
}
