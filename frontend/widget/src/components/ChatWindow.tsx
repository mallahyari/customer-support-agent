/**
 * Chat window component.
 */

import type { BotConfig, Message } from '../types'
import MessageList from './MessageList'
import MessageInput from './MessageInput'

interface ChatWindowProps {
  botConfig: BotConfig
  messages: Message[]
  onClose: () => void
  onSendMessage: (message: string) => void
}

export default function ChatWindow({
  botConfig,
  messages,
  onClose,
  onSendMessage,
}: ChatWindowProps) {
  const accentColor = botConfig.accent_color || '#3B82F6'
  const position = botConfig.position || 'bottom-right'

  // Position styles
  const positionStyles: Record<string, React.CSSProperties> = {
    'bottom-right': { bottom: '20px', right: '20px' },
    'bottom-left': { bottom: '20px', left: '20px' },
    'bottom-center': { bottom: '20px', left: '50%', transform: 'translateX(-50%)' },
  }

  const containerStyle: React.CSSProperties = {
    position: 'fixed',
    ...positionStyles[position],
    width: '380px',
    maxWidth: 'calc(100vw - 40px)',
    height: '600px',
    maxHeight: 'calc(100vh - 40px)',
    backgroundColor: '#ffffff',
    borderRadius: '12px',
    boxShadow: '0 8px 24px rgba(0, 0, 0, 0.15)',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    zIndex: 999999,
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  }

  const headerStyle: React.CSSProperties = {
    backgroundColor: accentColor,
    color: '#ffffff',
    padding: '16px 20px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexShrink: 0,
  }

  const headerContentStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  }

  const avatarStyle: React.CSSProperties = {
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '20px',
  }

  const nameStyle: React.CSSProperties = {
    fontSize: '16px',
    fontWeight: '600',
    margin: 0,
  }

  const closeButtonStyle: React.CSSProperties = {
    background: 'none',
    border: 'none',
    color: '#ffffff',
    cursor: 'pointer',
    padding: '4px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    opacity: 0.8,
    transition: 'opacity 0.2s',
  }

  return (
    <div style={containerStyle}>
      {/* Header */}
      <div style={headerStyle}>
        <div style={headerContentStyle}>
          {botConfig.avatar_url ? (
            <img
              src={botConfig.avatar_url}
              alt={botConfig.name}
              style={{ ...avatarStyle, objectFit: 'cover' }}
            />
          ) : (
            <div style={avatarStyle}>
              {botConfig.name.charAt(0).toUpperCase()}
            </div>
          )}
          <h3 style={nameStyle}>{botConfig.name}</h3>
        </div>

        <button
          style={closeButtonStyle}
          onClick={onClose}
          onMouseEnter={(e) => {
            e.currentTarget.style.opacity = '1'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.opacity = '0.8'
          }}
          aria-label="Close chat"
        >
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      {/* Messages */}
      <MessageList
        messages={messages}
        botConfig={botConfig}
      />

      {/* Input */}
      <MessageInput onSendMessage={onSendMessage} />
    </div>
  )
}
