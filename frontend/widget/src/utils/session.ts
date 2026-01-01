/**
 * Session management utilities.
 */

const SESSION_KEY = 'chirp_session_id'
const MESSAGES_KEY_PREFIX = 'chirp_messages_'

/**
 * Generate a random UUID v4.
 */
function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

/**
 * Get or create session ID from localStorage.
 */
export function getSessionId(): string {
  try {
    let sessionId = localStorage.getItem(SESSION_KEY)

    if (!sessionId) {
      sessionId = generateUUID()
      localStorage.setItem(SESSION_KEY, sessionId)
    }

    return sessionId
  } catch (error) {
    // Fallback if localStorage is not available
    console.warn('localStorage not available, using temporary session ID')
    return generateUUID()
  }
}

/**
 * Save messages to localStorage.
 */
export function saveMessages(botId: string, messages: any[]): void {
  try {
    const key = `${MESSAGES_KEY_PREFIX}${botId}`
    localStorage.setItem(key, JSON.stringify(messages))
  } catch (error) {
    console.warn('Failed to save messages to localStorage:', error)
  }
}

/**
 * Load messages from localStorage.
 */
export function loadMessages(botId: string): any[] {
  try {
    const key = `${MESSAGES_KEY_PREFIX}${botId}`
    const data = localStorage.getItem(key)
    return data ? JSON.parse(data) : []
  } catch (error) {
    console.warn('Failed to load messages from localStorage:', error)
    return []
  }
}

/**
 * Clear messages from localStorage.
 */
export function clearMessages(botId: string): void {
  try {
    const key = `${MESSAGES_KEY_PREFIX}${botId}`
    localStorage.removeItem(key)
  } catch (error) {
    console.warn('Failed to clear messages from localStorage:', error)
  }
}
