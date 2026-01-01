/**
 * Bot form page - create/edit bot configuration.
 */

import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { botApi, type BotCreate, type BotUpdate } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Card } from '@/components/ui/card'

export function BotFormPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isEditMode = Boolean(id)

  const [formData, setFormData] = useState<{
    name: string
    welcome_message: string
    accent_color: string
    position: 'bottom-right' | 'bottom-left' | 'bottom-center'
    show_button_text: boolean
    button_text: string
    message_limit: number
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
      })
    }
  }, [bot])

  const createMutation = useMutation({
    mutationFn: (data: BotCreate) => botApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bots'] })
      navigate('/dashboard')
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: BotUpdate) => botApi.update(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bots'] })
      queryClient.invalidateQueries({ queryKey: ['bot', id] })
      navigate('/dashboard')
    },
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    if (isEditMode) {
      updateMutation.mutate(formData)
    } else {
      createMutation.mutate(formData)
    }
  }

  const isLoading = createMutation.isPending || updateMutation.isPending

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
          Configure your chatbot settings and appearance
        </p>
      </div>

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

        <div className="flex justify-end space-x-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/dashboard')}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={isLoading}>
            {isLoading
              ? 'Saving...'
              : isEditMode
              ? 'Update Bot'
              : 'Create Bot'}
          </Button>
        </div>
      </form>
    </div>
  )
}
