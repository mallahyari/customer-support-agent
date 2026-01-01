/**
 * Main chat widget component.
 */

import { useEffect, useState } from 'react'
import type { WidgetConfig, WidgetState, Message } from '../types'
import { fetchBotConfig, streamChatResponse } from '../utils/api'
import { getSessionId, loadMessages, saveMessages } from '../utils/session'
import ChatButton from './ChatButton'
import ChatWindow from './ChatWindow'

interface ChatWidgetProps {
  config: WidgetConfig
}

export default function ChatWidget({ config }: ChatWidgetProps) {
  const [state, setState] = useState<WidgetState>({
    isOpen: false,
    isLoading: true,
    messages: [],
    botConfig: null,
    sessionId: getSessionId(),
    error: null,
  })

  // Load bot configuration on mount
  useEffect(() => {
    async function loadConfig() {
      try {
        const botConfig = await fetchBotConfig(
          config.botId,
          config.apiKey,
          config.apiUrl
        )

        // Load saved messages from localStorage
        const savedMessages = loadMessages(config.botId)

        setState((prev) => ({
          ...prev,
          botConfig,
          messages: savedMessages,
          isLoading: false,
          error: null,
        }))
      } catch (error) {
        console.error('Failed to load bot config:', error)
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: error instanceof Error ? error.message : 'Failed to load bot configuration',
        }))
      }
    }

    loadConfig()
  }, [config.botId, config.apiKey, config.apiUrl])

  // Save messages to localStorage whenever they change
  useEffect(() => {
    if (state.messages.length > 0) {
      saveMessages(config.botId, state.messages)
    }
  }, [state.messages, config.botId])

  const toggleOpen = () => {
    setState((prev) => ({ ...prev, isOpen: !prev.isOpen }))
  }

  const sendMessage = async (content: string) => {
    if (!state.botConfig || !content.trim()) return

    // Add user message and assistant placeholder in one update
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: content.trim(),
      timestamp: Date.now(),
    }

    const assistantMessageId = `assistant-${Date.now()}`
    let assistantContent = ''

    setState((prev) => ({
      ...prev,
      messages: [
        ...prev.messages,
        userMessage,
        {
          id: assistantMessageId,
          role: 'assistant',
          content: '',
          timestamp: Date.now(),
        },
      ],
    }))

    try {
      // Stream response from API
      const stream = streamChatResponse(
        {
          bot_id: config.botId,
          api_key: config.apiKey,
          session_id: state.sessionId,
          message: content.trim(),
        },
        config.apiUrl
      )

      for await (const token of stream) {
        assistantContent += token

        // Update assistant message with new content
        setState((prev) => ({
          ...prev,
          messages: prev.messages.map((msg) =>
            msg.id === assistantMessageId
              ? { ...msg, content: assistantContent }
              : msg
          ),
        }))
      }
    } catch (error) {
      console.error('Chat error:', error)

      // Update assistant message with error
      const errorMessage = error instanceof Error ? error.message : 'Failed to send message'

      setState((prev) => ({
        ...prev,
        messages: prev.messages.map((msg) =>
          msg.id === assistantMessageId
            ? { ...msg, content: `Error: ${errorMessage}` }
            : msg
        ),
      }))
    }
  }

  if (state.isLoading) {
    return null // Don't render until config is loaded
  }

  if (state.error || !state.botConfig) {
    console.error('Widget error:', state.error)
    return null // Don't render if there's an error
  }

  return (
    <>
      {!state.isOpen && (
        <ChatButton
          botConfig={state.botConfig}
          onClick={toggleOpen}
        />
      )}

      {state.isOpen && (
        <ChatWindow
          botConfig={state.botConfig}
          messages={state.messages}
          onClose={toggleOpen}
          onSendMessage={sendMessage}
        />
      )}
    </>
  )
}
