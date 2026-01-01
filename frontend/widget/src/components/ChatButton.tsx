/**
 * Chat launcher button component.
 */

import type { BotConfig } from '../types'

interface ChatButtonProps {
  botConfig: BotConfig
  onClick: () => void
}

export default function ChatButton({ botConfig, onClick }: ChatButtonProps) {
  const position = botConfig.position || 'bottom-right'
  const accentColor = botConfig.accent_color || '#3B82F6'
  const showText = botConfig.show_button_text
  const buttonText = botConfig.button_text || 'Chat with us'
  const avatarUrl = botConfig.avatar_url

  // Position styles
  const positionStyles: Record<string, React.CSSProperties> = {
    'bottom-right': { bottom: '20px', right: '20px' },
    'bottom-left': { bottom: '20px', left: '20px' },
    'bottom-center': { bottom: '20px', left: '50%', transform: 'translateX(-50%)' },
  }

  const buttonStyle: React.CSSProperties = {
    position: 'fixed',
    ...positionStyles[position],
    backgroundColor: accentColor,
    color: '#ffffff',
    border: 'none',
    borderRadius: showText ? '24px' : '50%',
    width: showText ? 'auto' : '56px',
    height: '56px',
    padding: showText ? '0 20px' : '0',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    cursor: 'pointer',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
    fontSize: '16px',
    fontWeight: '600',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    zIndex: 999999,
    transition: 'transform 0.2s, box-shadow 0.2s',
  }

  const avatarStyle: React.CSSProperties = {
    width: showText ? '24px' : '40px',
    height: showText ? '24px' : '40px',
    borderRadius: '50%',
    objectFit: 'cover',
  }

  // Chat icon component
  const ChatIcon = () => (
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
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  )

  return (
    <button
      style={buttonStyle}
      onClick={onClick}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = showText ? 'scale(1.05)' : 'scale(1.1)'
        e.currentTarget.style.boxShadow = '0 6px 16px rgba(0, 0, 0, 0.2)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = position === 'bottom-center' ? 'translateX(-50%)' : 'scale(1)'
        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)'
      }}
      aria-label="Open chat"
    >
      {showText ? (
        // Button with text: show avatar (if available) + text + chat icon
        <>
          {avatarUrl && <img src={avatarUrl} alt={botConfig.name} style={avatarStyle} />}
          <span>{buttonText}</span>
          <ChatIcon />
        </>
      ) : (
        // Button without text: show avatar (if available) or chat icon
        avatarUrl ? (
          <img src={avatarUrl} alt={botConfig.name} style={avatarStyle} />
        ) : (
          <ChatIcon />
        )
      )}
    </button>
  )
}
