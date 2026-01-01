/**
 * Widget configuration and API types.
 */

export interface WidgetConfig {
  botId: string
  apiKey: string
  apiUrl?: string // Optional custom API URL, defaults to production
}

export interface BotConfig {
  id: string
  name: string
  welcome_message: string
  avatar_url: string | null
  accent_color: string
  position: 'bottom-right' | 'bottom-left' | 'bottom-center'
  show_button_text: boolean
  button_text: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}

export interface ChatRequest {
  bot_id: string
  api_key: string
  session_id: string
  message: string
}

export interface WidgetState {
  isOpen: boolean
  isLoading: boolean
  messages: Message[]
  botConfig: BotConfig | null
  sessionId: string
  error: string | null
}
