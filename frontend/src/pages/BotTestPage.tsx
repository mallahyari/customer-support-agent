/**
 * Bot test page - test chatbot with live preview.
 */

import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { botApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

export function BotTestPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data: bot, isLoading } = useQuery({
    queryKey: ['bot', id],
    queryFn: () => botApi.get(id!),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading bot...</p>
        </div>
      </div>
    )
  }

  if (!bot) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">Bot not found</p>
        <Button onClick={() => navigate('/dashboard')} className="mt-4">
          Back to Dashboard
        </Button>
      </div>
    )
  }

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
        <h2 className="text-2xl font-bold text-gray-900">Test: {bot.name}</h2>
        <p className="mt-1 text-sm text-gray-600">
          Test your chatbot with live preview
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Widget Preview */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Live Preview</h3>
          <div className="bg-gray-100 rounded-lg p-8 min-h-[500px] relative">
            <p className="text-center text-gray-500 py-12">
              Widget preview will be displayed here
            </p>
            <p className="text-center text-sm text-gray-400 mt-4">
              Install the widget on your website to test it live
            </p>
          </div>
        </Card>

        {/* Embed Code */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Embed Code</h3>

          <div className="space-y-4">
            <div>
              <Label className="text-sm font-medium text-gray-700">
                Script Tag
              </Label>
              <div className="mt-2 bg-gray-900 rounded-lg p-4 overflow-x-auto">
                <code className="text-sm text-green-400 font-mono whitespace-pre">
{`<script src="https://your-domain.com/widget.js"></script>
<script>
  ChirpWidget.init({
    botId: '${bot.id}',
    apiKey: '${bot.api_key}',
    apiUrl: 'http://localhost:8000'
  })
</script>`}
                </code>
              </div>
              <Button
                onClick={() => {
                  const code = `<script src="https://your-domain.com/widget.js"></script>\n<script>\n  ChirpWidget.init({\n    botId: '${bot.id}',\n    apiKey: '${bot.api_key}',\n    apiUrl: 'http://localhost:8000'\n  })\n</script>`
                  navigator.clipboard.writeText(code)
                }}
                variant="outline"
                size="sm"
                className="mt-2"
              >
                Copy Code
              </Button>
            </div>

            <div>
              <Label className="text-sm font-medium text-gray-700">
                Bot Information
              </Label>
              <dl className="mt-2 space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-gray-600">Bot ID:</dt>
                  <dd className="font-mono text-gray-900">{bot.id}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-600">API Key:</dt>
                  <dd className="font-mono text-gray-900">{bot.api_key}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-600">Messages:</dt>
                  <dd className="text-gray-900">
                    {bot.message_count} / {bot.message_limit}
                  </dd>
                </div>
              </dl>
            </div>

            <div>
              <Button
                onClick={() => navigate(`/dashboard/bots/${bot.id}`)}
                variant="outline"
                className="w-full"
              >
                Edit Bot Settings
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}

function Label({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={className}>{children}</div>
}
