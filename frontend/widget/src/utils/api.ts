/**
 * API client for Chirp backend.
 */

import type { BotConfig, ChatRequest } from '../types'

const DEFAULT_API_URL = 'http://localhost:8000'

/**
 * Fetch bot configuration from API.
 */
export async function fetchBotConfig(
  botId: string,
  apiKey: string,
  apiUrl: string = DEFAULT_API_URL
): Promise<BotConfig> {
  const url = `${apiUrl}/api/public/config/${botId}?api_key=${encodeURIComponent(apiKey)}`

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Invalid bot ID or API key')
    }
    throw new Error(`Failed to fetch bot config: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Send chat message and stream response.
 */
export async function* streamChatResponse(
  request: ChatRequest,
  apiUrl: string = DEFAULT_API_URL
): AsyncGenerator<string, void, unknown> {
  const url = `${apiUrl}/api/chat`

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Invalid bot ID or API key')
    }
    if (response.status === 429) {
      const data = await response.json()
      throw new Error(data.detail || 'Rate limit exceeded')
    }
    throw new Error(`Chat request failed: ${response.statusText}`)
  }

  // Parse SSE stream
  const reader = response.body?.getReader()
  if (!reader) {
    throw new Error('Response body is not readable')
  }

  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()

      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // Split by SSE event boundaries
      const lines = buffer.split('\n')
      buffer = lines.pop() || '' // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6) // Remove 'data: ' prefix

          if (data === '[DONE]') {
            return
          }

          yield data
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}
