/**
 * Message input component.
 */

import { useState, KeyboardEvent } from 'react'

interface MessageInputProps {
  onSendMessage: (message: string) => void
}

export default function MessageInput({ onSendMessage }: MessageInputProps) {
  const [input, setInput] = useState('')

  const handleSend = () => {
    if (input.trim()) {
      onSendMessage(input)
      setInput('')
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const containerStyle: React.CSSProperties = {
    padding: '16px 20px',
    borderTop: '1px solid #e5e7eb',
    backgroundColor: '#ffffff',
    display: 'flex',
    gap: '12px',
    flexShrink: 0,
  }

  const textareaStyle: React.CSSProperties = {
    flex: 1,
    border: '1px solid #d1d5db',
    borderRadius: '8px',
    padding: '10px 12px',
    fontSize: '14px',
    fontFamily: 'inherit',
    resize: 'none',
    outline: 'none',
    lineHeight: '1.5',
    maxHeight: '100px',
  }

  const buttonStyle: React.CSSProperties = {
    backgroundColor: '#3B82F6',
    color: '#ffffff',
    border: 'none',
    borderRadius: '8px',
    padding: '10px 16px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'background-color 0.2s',
    flexShrink: 0,
  }

  return (
    <div style={containerStyle}>
      <textarea
        style={textareaStyle}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type your message..."
        rows={1}
        onFocus={(e) => {
          e.currentTarget.style.borderColor = '#3B82F6'
        }}
        onBlur={(e) => {
          e.currentTarget.style.borderColor = '#d1d5db'
        }}
      />
      <button
        style={buttonStyle}
        onClick={handleSend}
        disabled={!input.trim()}
        onMouseEnter={(e) => {
          if (input.trim()) {
            e.currentTarget.style.backgroundColor = '#2563eb'
          }
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = '#3B82F6'
        }}
        aria-label="Send message"
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <line x1="22" y1="2" x2="11" y2="13" />
          <polygon points="22 2 15 22 11 13 2 9 22 2" />
        </svg>
      </button>
    </div>
  )
}
