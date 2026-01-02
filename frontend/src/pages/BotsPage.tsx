/**
 * Bots list page - displays all bots with quick actions.
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { botApi, type Bot } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'

// Helper to convert relative avatar URL to absolute
const getAbsoluteAvatarUrl = (url: string | null | undefined): string | null => {
  if (!url) return null
  if (url.startsWith('http')) return url
  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  return `${API_URL}${url}`
}

export function BotsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [botToDelete, setBotToDelete] = useState<Bot | null>(null)

  const { data: bots, isLoading } = useQuery({
    queryKey: ['bots'],
    queryFn: botApi.list,
  })

  const deleteMutation = useMutation({
    mutationFn: botApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bots'] })
      setDeleteDialogOpen(false)
      setBotToDelete(null)
    },
  })

  function handleDelete(bot: Bot) {
    setBotToDelete(bot)
    setDeleteDialogOpen(true)
  }

  function confirmDelete() {
    if (botToDelete) {
      deleteMutation.mutate(botToDelete.id)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading bots...</p>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Your Bots</h2>
          <p className="mt-1 text-sm text-gray-600">
            Manage your AI chatbots and embed them on your website
          </p>
        </div>

        <Button onClick={() => navigate('/dashboard/bots/new')}>
          Create New Bot
        </Button>
      </div>

      {!bots || bots.length === 0 ? (
        <Card className="p-12 text-center">
          <div className="mx-auto w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mb-4">
            <svg
              className="w-12 h-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No bots yet
          </h3>
          <p className="text-gray-600 mb-6">
            Get started by creating your first chatbot
          </p>
          <Button onClick={() => navigate('/dashboard/bots/new')}>
            Create Your First Bot
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {bots.map((bot) => (
            <BotCard
              key={bot.id}
              bot={bot}
              onEdit={() => navigate(`/dashboard/bots/${bot.id}`)}
              onTest={() => navigate(`/dashboard/bots/${bot.id}/test`)}
              onDelete={() => handleDelete(bot)}
            />
          ))}
        </div>
      )}

      {/* Delete confirmation dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Bot</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{botToDelete?.name}"? This action
              cannot be undone and will remove all associated data.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDelete} variant="destructive">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

interface BotCardProps {
  bot: Bot
  onEdit: () => void
  onTest: () => void
  onDelete: () => void
}

function BotCard({ bot, onEdit, onTest, onDelete }: BotCardProps) {
  const usagePercent = (bot.message_count / bot.message_limit) * 100
  const avatarUrl = getAbsoluteAvatarUrl(bot.avatar_url)

  return (
    <Card className="p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          {avatarUrl ? (
            <img
              src={avatarUrl}
              alt={bot.name}
              className="w-12 h-12 rounded-full object-cover"
              onError={() => {
                console.error('Failed to load bot avatar in card:', avatarUrl)
              }}
            />
          ) : (
            <div
              className="w-12 h-12 rounded-full flex items-center justify-center text-white text-xl font-bold"
              style={{ backgroundColor: bot.accent_color }}
            >
              {bot.name.charAt(0).toUpperCase()}
            </div>
          )}
          <div>
            <h3 className="font-semibold text-gray-900">{bot.name}</h3>
            <Badge variant="secondary" className="mt-1">
              {bot.source_type || 'Not trained'}
            </Badge>
          </div>
        </div>
      </div>

      <p className="text-sm text-gray-600 mb-4 line-clamp-2">
        {bot.welcome_message || 'No welcome message set'}
      </p>

      {/* Usage meter */}
      <div className="mb-4">
        <div className="flex justify-between text-xs text-gray-600 mb-1">
          <span>Usage</span>
          <span>
            {bot.message_count.toLocaleString()} / {bot.message_limit.toLocaleString()}
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${
              usagePercent >= 90
                ? 'bg-red-500'
                : usagePercent >= 70
                ? 'bg-yellow-500'
                : 'bg-green-500'
            }`}
            style={{ width: `${Math.min(usagePercent, 100)}%` }}
          />
        </div>
      </div>

      {/* Actions */}
      <div className="grid grid-cols-3 gap-2">
        <Button onClick={onEdit} variant="outline" size="sm">
          Edit
        </Button>
        <Button onClick={onTest} variant="outline" size="sm">
          Test
        </Button>
        <Button onClick={onDelete} variant="outline" size="sm">
          Delete
        </Button>
      </div>
    </Card>
  )
}
