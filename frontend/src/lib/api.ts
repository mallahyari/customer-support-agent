/**
 * API client for Chirp dashboard.
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface Bot {
  id: string
  name: string
  welcome_message: string
  avatar_url: string | null
  accent_color: string
  position: 'bottom-right' | 'bottom-left' | 'bottom-center'
  show_button_text: boolean
  button_text: string
  source_type: 'url' | 'text' | null
  source_content: string | null
  api_key: string
  message_count: number
  message_limit: number
  created_at: string
  updated_at: string
}

interface BotCreate {
  name: string
  welcome_message?: string
  accent_color?: string
  position?: 'bottom-right' | 'bottom-left' | 'bottom-center'
  show_button_text?: boolean
  button_text?: string
  source_type?: 'url' | 'text'
  source_content?: string
  message_limit?: number
}

interface BotUpdate extends Partial<BotCreate> {}

interface IngestRequest {
  source_type: 'url' | 'text'
  source_content: string
}

class ApiError extends Error {
  status: number
  data?: any

  constructor(message: string, status: number, data?: any) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const response = await fetch(`${API_URL}${url}`, {
    ...options,
    credentials: 'include', // Include cookies for session auth
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new ApiError(
      data.detail || response.statusText,
      response.status,
      data
    )
  }

  return response
}

// Auth API
export const authApi = {
  async login(username: string, password: string): Promise<void> {
    await fetchWithAuth('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    })
  },

  async logout(): Promise<void> {
    await fetchWithAuth('/api/auth/logout', {
      method: 'POST',
    })
  },

  async checkAuth(): Promise<boolean> {
    try {
      await fetchWithAuth('/api/admin/bots', {
        method: 'GET',
      })
      return true
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        return false
      }
      throw error
    }
  },
}

// Bot API
export const botApi = {
  async list(): Promise<Bot[]> {
    const response = await fetchWithAuth('/api/admin/bots')
    return response.json()
  },

  async get(id: string): Promise<Bot> {
    const response = await fetchWithAuth(`/api/admin/bots/${id}`)
    return response.json()
  },

  async create(data: BotCreate): Promise<Bot> {
    const response = await fetchWithAuth('/api/admin/bots', {
      method: 'POST',
      body: JSON.stringify(data),
    })
    return response.json()
  },

  async update(id: string, data: BotUpdate): Promise<Bot> {
    const response = await fetchWithAuth(`/api/admin/bots/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
    return response.json()
  },

  async delete(id: string): Promise<void> {
    await fetchWithAuth(`/api/admin/bots/${id}`, {
      method: 'DELETE',
    })
  },

  async uploadAvatar(id: string, file: File): Promise<Bot> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${API_URL}/api/admin/bots/${id}/avatar`, {
      method: 'POST',
      credentials: 'include',
      body: formData,
    })

    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      throw new ApiError(data.detail || response.statusText, response.status, data)
    }

    return response.json()
  },

  async deleteAvatar(id: string): Promise<Bot> {
    const response = await fetchWithAuth(`/api/admin/bots/${id}/avatar`, {
      method: 'DELETE',
    })
    return response.json()
  },

  async regenerateApiKey(id: string): Promise<Bot> {
    const response = await fetchWithAuth(`/api/admin/bots/${id}/regenerate-key`, {
      method: 'POST',
    })
    return response.json()
  },

  async ingest(id: string): Promise<{ message: string }> {
    const response = await fetchWithAuth(`/api/admin/bots/${id}/ingest`, {
      method: 'POST',
    })
    return response.json()
  },
}

export type { Bot, BotCreate, BotUpdate, IngestRequest }
export { ApiError }
