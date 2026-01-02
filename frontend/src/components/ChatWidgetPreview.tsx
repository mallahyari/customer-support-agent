/**
 * Live preview of the chat widget for bot configuration.
 * Shows real-time updates as user modifies bot settings.
 */

import { useState } from 'react'

interface ChatWidgetPreviewProps {
  botName: string
  welcomeMessage: string
  accentColor: string
  position: 'bottom-right' | 'bottom-left' | 'bottom-center'
  showButtonText: boolean
  buttonText: string
  avatarUrl?: string | null
}

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export function ChatWidgetPreview({
  botName,
  welcomeMessage,
  accentColor,
  position,
  showButtonText,
  buttonText,
  avatarUrl,
}: ChatWidgetPreviewProps) {
  const [isOpen, setIsOpen] = useState(false)

  // Sample conversation for preview
  const messages: Message[] = [
    { role: 'assistant', content: welcomeMessage },
    { role: 'user', content: 'What are your business hours?' },
    {
      role: 'assistant',
      content: 'We are open Monday-Friday, 9 AM to 5 PM EST. How can I help you today?',
    },
  ]

  // Position classes
  const positionClasses = {
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'bottom-center': 'bottom-4 left-1/2 -translate-x-1/2',
  }

  const chatPositionClasses = {
    'bottom-right': 'bottom-24 right-4',
    'bottom-left': 'bottom-24 left-4',
    'bottom-center': 'bottom-24 left-1/2 -translate-x-1/2',
  }

  return (
    <div className="relative w-full h-[600px] bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg border border-gray-200 overflow-hidden">
      {/* Preview label */}
      <div className="absolute top-4 left-4 bg-white px-3 py-1.5 rounded-full shadow-sm border border-gray-200">
        <span className="text-xs font-medium text-gray-600">Live Preview</span>
      </div>

      {/* Sample website content */}
      <div className="absolute inset-0 p-8 pt-16">
        <div className="max-w-2xl mx-auto space-y-4">
          <div className="h-8 bg-white/50 rounded w-1/3"></div>
          <div className="h-4 bg-white/30 rounded w-2/3"></div>
          <div className="h-4 bg-white/30 rounded w-1/2"></div>
          <div className="h-4 bg-white/30 rounded w-3/4"></div>
        </div>
      </div>

      {/* Chat Window */}
      {isOpen && (
        <div
          className={`absolute ${chatPositionClasses[position]} w-[350px] h-[500px] bg-white rounded-lg shadow-2xl flex flex-col border border-gray-200 z-10`}
        >
          {/* Header */}
          <div
            className="px-4 py-3 rounded-t-lg flex items-center justify-between"
            style={{ backgroundColor: accentColor }}
          >
            <div className="flex items-center space-x-3">
              {avatarUrl ? (
                <img
                  key={avatarUrl}
                  src={avatarUrl}
                  alt={botName}
                  className="w-8 h-8 rounded-full object-cover bg-white/20"
                  onError={() => {
                    console.error('Failed to load avatar in header preview:', avatarUrl)
                  }}
                />
              ) : (
                <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center text-white font-semibold">
                  {botName ? botName.charAt(0).toUpperCase() : 'B'}
                </div>
              )}
              <span className="font-semibold text-white">{botName || 'Bot'}</span>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-white hover:bg-white/20 rounded p-1 transition-colors"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    message.role === 'user'
                      ? 'text-white'
                      : 'bg-white text-gray-800 border border-gray-200'
                  }`}
                  style={
                    message.role === 'user' ? { backgroundColor: accentColor } : undefined
                  }
                >
                  <p className="text-sm">{message.content}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Input */}
          <div className="p-4 border-t border-gray-200 bg-white rounded-b-lg">
            <div className="flex items-center space-x-2">
              <input
                type="text"
                placeholder="Type a message..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-opacity-50"
                disabled
              />
              <button
                className="p-2 rounded-lg text-white transition-colors"
                style={{ backgroundColor: accentColor }}
                disabled
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Chat Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`absolute ${positionClasses[position]} shadow-xl rounded-full flex items-center space-x-2 transition-transform hover:scale-105`}
        style={{ backgroundColor: accentColor }}
      >
        {showButtonText ? (
          <div className="flex items-center space-x-2 px-5 py-3">
            {avatarUrl && (
              <img
                key={avatarUrl}
                src={avatarUrl}
                alt={botName}
                className="w-6 h-6 rounded-full object-cover"
                onError={() => console.error('Failed to load avatar in button (text mode):', avatarUrl)}
              />
            )}
            <span className="text-white font-medium">{buttonText}</span>
            <svg
              className="w-5 h-5 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
          </div>
        ) : (
          <div className="w-14 h-14 flex items-center justify-center">
            {avatarUrl ? (
              <img
                key={avatarUrl}
                src={avatarUrl}
                alt={botName}
                className="w-10 h-10 rounded-full object-cover"
                onError={() => console.error('Failed to load avatar in button (icon mode):', avatarUrl)}
              />
            ) : (
              <svg
                className="w-7 h-7 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
            )}
          </div>
        )}
      </button>
    </div>
  )
}
