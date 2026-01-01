/**
 * Message list component with auto-scroll.
 */

import { useEffect, useRef } from 'react'
import type { BotConfig, Message } from '../types'

interface MessageListProps {
  messages: Message[]
  botConfig: BotConfig
}

export default function MessageList({ messages, botConfig }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const containerStyle: React.CSSProperties = {
    flex: 1,
    overflowY: 'auto',
    padding: '20px',
    backgroundColor: '#f9fafb',
  }

  const welcomeStyle: React.CSSProperties = {
    textAlign: 'center',
    color: '#6b7280',
    fontSize: '14px',
    marginBottom: '20px',
  }

  return (
    <div style={containerStyle} ref={containerRef}>
      {/* Welcome message */}
      {messages.length === 0 && (
        <div style={welcomeStyle}>
          <p>{botConfig.welcome_message || 'Hi! How can I help you today?'}</p>
        </div>
      )}

      {/* Messages */}
      {messages.map((message) => (
        <MessageBubble
          key={message.id}
          message={message}
          botConfig={botConfig}
        />
      ))}

      {/* Auto-scroll anchor */}
      <div ref={messagesEndRef} />
    </div>
  )
}

interface MessageBubbleProps {
  message: Message
  botConfig: BotConfig
}

function MessageBubble({ message, botConfig }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  const accentColor = botConfig.accent_color || '#3B82F6'

  const bubbleContainerStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: isUser ? 'flex-end' : 'flex-start',
    marginBottom: '12px',
  }

  const bubbleStyle: React.CSSProperties = {
    maxWidth: '80%',
    padding: '10px 14px',
    borderRadius: '12px',
    fontSize: '14px',
    lineHeight: '1.5',
    wordWrap: 'break-word',
    backgroundColor: isUser ? accentColor : '#ffffff',
    color: isUser ? '#ffffff' : '#1f2937',
    boxShadow: isUser ? 'none' : '0 1px 2px rgba(0, 0, 0, 0.05)',
  }

  return (
    <div style={bubbleContainerStyle}>
      <div style={bubbleStyle}>
        {message.content || (
          <span style={{ opacity: 0.5 }}>Thinking...</span>
        )}
      </div>
    </div>
  )
}
