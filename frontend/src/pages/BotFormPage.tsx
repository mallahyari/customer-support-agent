/**
 * Bot form page - create/edit bot configuration.
 */

import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { botApi, type BotCreate, type BotUpdate } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Card } from '@/components/ui/card'
import { ChatWidgetPreview } from '@/components/ChatWidgetPreview'

export function BotFormPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isEditMode = Boolean(id)
  const [isTraining, setIsTraining] = useState(false)
  const [trainingMessage, setTrainingMessage] = useState<string | null>(null)
  const [isUploadingAvatar, setIsUploadingAvatar] = useState(false)
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null)
  const [selectedAvatarFile, setSelectedAvatarFile] = useState<File | null>(null)

  // Helper to convert relative avatar URL to absolute
  const getAbsoluteAvatarUrl = useCallback((url: string | null | undefined): string | null => {
    if (!url) return null
    if (url.startsWith('http')) return url
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    return `${API_URL}${url}`
  }, [])

  const [formData, setFormData] = useState<{
    name: string
    welcome_message: string
    accent_color: string
    position: 'bottom-right' | 'bottom-left' | 'bottom-center'
    show_button_text: boolean
    button_text: string
    message_limit: number
    source_type?: 'url' | 'text'
    source_content?: string
  }>({
    name: '',
    welcome_message: 'Hi! How can I help you today?',
    accent_color: '#3B82F6',
    position: 'bottom-right',
    show_button_text: true,
    button_text: 'Chat with us',
    message_limit: 1000,
  })

  const { data: bot } = useQuery({
    queryKey: ['bot', id],
    queryFn: () => botApi.get(id!),
    enabled: isEditMode,
  })

  useEffect(() => {
    if (bot) {
      setFormData({
        name: bot.name,
        welcome_message: bot.welcome_message,
        accent_color: bot.accent_color,
        position: bot.position,
        show_button_text: bot.show_button_text,
        button_text: bot.button_text,
        message_limit: bot.message_limit,
        source_type: bot.source_type || undefined,
        source_content: bot.source_content || undefined,
      })
      // Sync avatar preview with bot data, converting to absolute URL
      setAvatarPreview(getAbsoluteAvatarUrl(bot.avatar_url))
    }
  }, [bot, getAbsoluteAvatarUrl])

  const createMutation = useMutation({
    mutationFn: (data: BotCreate) => botApi.create(data),
    onSuccess: async (newBot) => {
      queryClient.invalidateQueries({ queryKey: ['bots'] })

      // Upload avatar if one was selected
      if (selectedAvatarFile) {
        try {
          await botApi.uploadAvatar(newBot.id, selectedAvatarFile)
          queryClient.invalidateQueries({ queryKey: ['bots'] })
        } catch (error: any) {
          console.error('Failed to upload avatar after bot creation:', error)
          // Continue anyway - avatar can be added later
        }
      }

      // If source data is provided, automatically train the bot
      if (newBot.source_type && newBot.source_content) {
        await trainBot(newBot.id)
      } else {
        navigate('/dashboard')
      }
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: BotUpdate) => botApi.update(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bots'] })
      queryClient.invalidateQueries({ queryKey: ['bot', id] })
      setTrainingMessage(null)
    },
  })

  async function trainBot(botId: string) {
    setIsTraining(true)
    setTrainingMessage('Training bot... This may take a minute.')

    try {
      const result = await botApi.ingest(botId)

      setTrainingMessage(result.message)

      // Redirect after a short delay to show success message
      setTimeout(() => {
        navigate('/dashboard')
      }, 2000)
    } catch (error: any) {
      setTrainingMessage(`Training failed: ${error.message || 'Unknown error'}`)
    } finally {
      setIsTraining(false)
    }
  }

  async function handleTrainBot() {
    if (!id || !formData.source_type || !formData.source_content) {
      setTrainingMessage('Please select a source type and provide content first.')
      return
    }

    // Save first if there are changes, then train
    if (formData.source_type && formData.source_content) {
      await updateMutation.mutateAsync(formData)
      await trainBot(id)
    }
  }

  async function handleAvatarUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return

    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file')
      return
    }

    // Validate file size (max 500KB)
    if (file.size > 500 * 1024) {
      alert('Image must be smaller than 500KB')
      return
    }

    // In create mode, store the file and preview it
    if (!isEditMode) {
      setSelectedAvatarFile(file)
      // Create preview URL
      const previewUrl = URL.createObjectURL(file)
      setAvatarPreview(previewUrl)
      return
    }

    // In edit mode, upload immediately
    setIsUploadingAvatar(true)
    try {
      const updatedBot = await botApi.uploadAvatar(id!, file)

      // Update preview with absolute URL
      setAvatarPreview(getAbsoluteAvatarUrl(updatedBot.avatar_url))

      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['bot', id] })
      queryClient.invalidateQueries({ queryKey: ['bots'] })
    } catch (error: any) {
      alert(`Failed to upload avatar: ${error.message}`)
    } finally {
      setIsUploadingAvatar(false)
    }
  }

  async function handleAvatarDelete() {
    // In create mode, just clear the selected file and preview
    if (!isEditMode) {
      setSelectedAvatarFile(null)
      setAvatarPreview(null)
      return
    }

    // In edit mode, delete from server
    if (!id || !bot?.avatar_url) return

    if (!confirm('Are you sure you want to remove the avatar?')) return

    setIsUploadingAvatar(true)
    try {
      await botApi.deleteAvatar(id)
      setAvatarPreview(null)

      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['bot', id] })
      queryClient.invalidateQueries({ queryKey: ['bots'] })
    } catch (error: any) {
      alert(`Failed to delete avatar: ${error.message}`)
    } finally {
      setIsUploadingAvatar(false)
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    if (isEditMode) {
      updateMutation.mutate(formData)
    } else {
      createMutation.mutate(formData)
    }
  }

  const isLoading = createMutation.isPending || updateMutation.isPending || isTraining

  return (
    <div>
      <div className="mb-6">
        <Button
          onClick={() => navigate('/dashboard')}
          variant="outline"
          size="sm"
          className="mb-4"
        >
          ← Back to Bots
        </Button>
        <h2 className="text-2xl font-bold text-gray-900">
          {isEditMode ? 'Edit Bot' : 'Create New Bot'}
        </h2>
        <p className="mt-1 text-sm text-gray-600">
          Configure your chatbot settings and appearance with live preview
        </p>
      </div>

      {/* Split Layout: Form on left, Preview on right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Form (scrollable) */}
        <div className="lg:col-span-7">
          <form onSubmit={handleSubmit} className="space-y-6">
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Basic Settings</h3>

          <div className="space-y-4">
            <div>
              <Label htmlFor="name">Bot Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                placeholder="My Support Bot"
                required
                className="mt-1"
              />
            </div>

            <div>
              <Label htmlFor="welcome_message">Welcome Message</Label>
              <Textarea
                id="welcome_message"
                value={formData.welcome_message}
                onChange={(e) =>
                  setFormData({ ...formData, welcome_message: e.target.value })
                }
                placeholder="Hi! How can I help you today?"
                rows={3}
                className="mt-1"
              />
            </div>

            <div>
              <Label htmlFor="message_limit">Message Limit</Label>
              <Input
                id="message_limit"
                type="number"
                value={formData.message_limit}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    message_limit: parseInt(e.target.value),
                  })
                }
                min={1}
                required
                className="mt-1"
              />
              <p className="text-xs text-gray-500 mt-1">
                Maximum number of messages this bot can handle
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Appearance</h3>

          <div className="space-y-4">
            <div>
              <Label htmlFor="accent_color">Accent Color</Label>
              <div className="flex items-center space-x-2 mt-1">
                <input
                  id="accent_color"
                  type="color"
                  value={formData.accent_color}
                  onChange={(e) =>
                    setFormData({ ...formData, accent_color: e.target.value })
                  }
                  className="h-10 w-20"
                />
                <Input
                  value={formData.accent_color}
                  onChange={(e) =>
                    setFormData({ ...formData, accent_color: e.target.value })
                  }
                  placeholder="#3B82F6"
                  className="flex-1"
                />
              </div>
            </div>

            <div>
              <Label>Avatar {!isEditMode && '(Optional)'}</Label>
              <div className="mt-2">
                {avatarPreview ? (
                  <div className="flex items-center space-x-4">
                    <img
                      key={avatarPreview}
                      src={avatarPreview}
                      alt="Bot avatar"
                      className="w-16 h-16 rounded-full object-cover border-2 border-gray-200"
                      onError={() => {
                        console.error('Failed to load avatar:', avatarPreview)
                      }}
                    />
                    <div className="flex flex-col space-y-2">
                      <label className="cursor-pointer">
                        <input
                          type="file"
                          accept="image/*"
                          onChange={handleAvatarUpload}
                          className="hidden"
                          disabled={isUploadingAvatar}
                        />
                        <span className="inline-flex items-center px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50 transition-colors">
                          {isUploadingAvatar ? 'Uploading...' : 'Change Avatar'}
                        </span>
                      </label>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={handleAvatarDelete}
                        disabled={isUploadingAvatar}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        Remove Avatar
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div>
                    <label className="cursor-pointer">
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleAvatarUpload}
                        className="hidden"
                        disabled={isUploadingAvatar}
                      />
                      <div className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">
                        {isUploadingAvatar ? 'Uploading...' : 'Upload Avatar'}
                      </div>
                    </label>
                    <p className="text-xs text-gray-500 mt-2">
                      Upload an image (max 500KB). Will be resized to 64x64px.
                    </p>
                  </div>
                )}
              </div>
            </div>

            <div>
              <Label htmlFor="button_text">Button Text</Label>
              <Input
                id="button_text"
                value={formData.button_text}
                onChange={(e) =>
                  setFormData({ ...formData, button_text: e.target.value })
                }
                placeholder="Chat with us"
                className="mt-1"
              />
            </div>

            <div>
              <Label>Position</Label>
              <div className="grid grid-cols-3 gap-2 mt-1">
                {(['bottom-left', 'bottom-center', 'bottom-right'] as const).map(
                  (pos) => (
                    <button
                      key={pos}
                      type="button"
                      onClick={() => setFormData({ ...formData, position: pos })}
                      className={`px-4 py-2 text-sm rounded border transition-colors ${
                        formData.position === pos
                          ? 'border-blue-600 bg-blue-50 text-blue-700'
                          : 'border-gray-300 hover:border-gray-400'
                      }`}
                    >
                      {pos.replace('-', ' ')}
                    </button>
                  )
                )}
              </div>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Training Data</h3>

          <div className="space-y-4">
            <div>
              <Label>Source Type</Label>
              <div className="grid grid-cols-2 gap-2 mt-1">
                {(['url', 'text'] as const).map((type) => (
                  <button
                    key={type}
                    type="button"
                    onClick={() =>
                      setFormData({ ...formData, source_type: type, source_content: '' })
                    }
                    className={`px-4 py-2 text-sm rounded border transition-colors ${
                      formData.source_type === type
                        ? 'border-blue-600 bg-blue-50 text-blue-700'
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    {type === 'url' ? 'Website URL' : 'Direct Text'}
                  </button>
                ))}
              </div>
            </div>

            {formData.source_type === 'url' && (
              <div>
                <Label htmlFor="source_content">Website URL</Label>
                <Input
                  id="source_content"
                  type="url"
                  value={formData.source_content || ''}
                  onChange={(e) =>
                    setFormData({ ...formData, source_content: e.target.value })
                  }
                  placeholder="https://example.com/help"
                  className="mt-1"
                />
                <p className="text-xs text-gray-500 mt-1">
                  The bot will scrape and learn from this URL (max 10,000 words)
                </p>
              </div>
            )}

            {formData.source_type === 'text' && (
              <div>
                <Label htmlFor="source_content">Training Text</Label>
                <Textarea
                  id="source_content"
                  value={formData.source_content || ''}
                  onChange={(e) =>
                    setFormData({ ...formData, source_content: e.target.value })
                  }
                  placeholder="Paste your content here..."
                  rows={8}
                  className="mt-1 font-mono text-sm"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Paste the text content you want the bot to learn from
                </p>
              </div>
            )}

            {isEditMode && formData.source_type && formData.source_content && (
              <div>
                <Button
                  type="button"
                  onClick={handleTrainBot}
                  disabled={isTraining || updateMutation.isPending}
                  className="w-full"
                >
                  {isTraining ? 'Training...' : 'Train Bot Now'}
                </Button>
                <p className="text-xs text-gray-500 mt-1">
                  Click to re-train the bot with the current content
                </p>
              </div>
            )}

            {trainingMessage && (
              <div
                className={`p-3 rounded text-sm ${
                  trainingMessage.includes('failed')
                    ? 'bg-red-50 text-red-700 border border-red-200'
                    : 'bg-green-50 text-green-700 border border-green-200'
                }`}
              >
                {trainingMessage}
              </div>
            )}
          </div>
        </Card>

        <div className="flex justify-end space-x-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/dashboard')}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={isLoading}>
            {isTraining
              ? 'Training...'
              : isLoading
              ? 'Saving...'
              : isEditMode
              ? 'Update Bot'
              : 'Create Bot'}
          </Button>
        </div>
        {!isEditMode && formData.source_type && formData.source_content && (
          <p className="text-xs text-gray-500 mt-2 text-right">
            Bot will be trained automatically after creation
          </p>
        )}
      </form>
        </div>

        {/* Right Column: Live Preview (sticky) */}
        <div className="lg:col-span-5">
          <div className="sticky top-6">
            <ChatWidgetPreview
              botName={formData.name || 'My Bot'}
              welcomeMessage={formData.welcome_message}
              accentColor={formData.accent_color}
              position={formData.position}
              showButtonText={formData.show_button_text}
              buttonText={formData.button_text}
              avatarUrl={avatarPreview || getAbsoluteAvatarUrl(bot?.avatar_url)}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
