# Chirp Widget

Embeddable chat widget for Chirp chatbot platform.

## Features

- 🎨 Customizable styling (accent color, position, button text)
- 🔒 Shadow DOM isolation (no CSS conflicts)
- 💬 Real-time SSE streaming responses
- 💾 Conversation persistence via localStorage
- 📱 Responsive design
- ⚡ Lightweight bundle (~154KB, ~50KB gzipped)

## Development

```bash
# Install dependencies
npm install

# Development mode with hot reload
npm run dev

# Build production bundle
npm run build

# Type checking
npm run type-check
```

## Integration

### Method 1: Script Tag Initialization

```html
<script src="https://your-domain.com/widget.js"></script>
<script>
  ChirpWidget.init({
    botId: 'your-bot-id',
    apiKey: 'your-api-key',
    apiUrl: 'https://your-api.com' // Optional, defaults to localhost:8000
  })
</script>
```

### Method 2: Data Attributes (Auto-Initialize)

```html
<script
  src="https://your-domain.com/widget.js"
  data-chirp-bot-id="your-bot-id"
  data-chirp-api-key="your-api-key"
  data-chirp-api-url="https://your-api.com"
></script>
```

The widget will automatically initialize on `DOMContentLoaded` when data attributes are present.

## Configuration

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `botId` | string | Yes | - | Bot UUID from backend |
| `apiKey` | string | Yes | - | Bot API key for authentication |
| `apiUrl` | string | No | `http://localhost:8000` | Backend API URL |

## Customization

The widget appearance is configured via the bot settings in the backend:

- **Accent Color**: Button and message bubble color
- **Position**: `bottom-right`, `bottom-left`, or `bottom-center`
- **Button Text**: Custom text for the launcher button
- **Show Button Text**: Toggle text visibility on launcher
- **Welcome Message**: Initial greeting shown in empty chat
- **Avatar**: Bot avatar image (64x64px)

## API Integration

The widget communicates with the backend API:

1. **GET** `/api/public/config/{bot_id}?api_key=xxx`
   - Fetches bot configuration on load
   - Returns name, welcome message, styling, etc.

2. **POST** `/api/chat`
   - Sends messages and streams responses via SSE
   - Body: `{ bot_id, api_key, session_id, message }`

## Browser Support

- Chrome/Edge 88+
- Firefox 78+
- Safari 14+
- Any browser with Shadow DOM and ES2020 support

## Architecture

### Shadow DOM Isolation

The widget uses Shadow DOM to prevent CSS conflicts with the host page:

```
<div id="chirp-widget-root">
  #shadow-root
    <style>...</style>
    <div id="chirp-widget-app">
      <ChatWidget />
    </div>
</div>
```

### State Management

- **Session ID**: Generated UUID stored in localStorage
- **Messages**: Persisted to localStorage per bot
- **Configuration**: Fetched from API on mount

### Component Structure

```
index.tsx              # Entry point with Shadow DOM setup
├── ChatWidget.tsx     # Main container with state management
    ├── ChatButton.tsx # Floating launcher button
    └── ChatWindow.tsx # Chat interface
        ├── MessageList.tsx   # Message display with auto-scroll
        └── MessageInput.tsx  # Text input with send button
```

## Testing

### Local Testing

1. Build the widget:
   ```bash
   npm run build
   ```

2. Start the backend server:
   ```bash
   cd backend
   uvicorn main:app --reload --port 8000
   ```

3. Create a test bot and get credentials

4. Update `demo.html` with your bot ID and API key

5. Open `demo.html` in a browser

### Production Testing

Deploy `dist/widget.js` to your CDN and integrate on your website.

## Bundle Analysis

- **React**: Core framework
- **React DOM**: Rendering
- **TypeScript**: Type safety
- **Vite**: Build tool with library mode

The bundle is compiled as a single IIFE (Immediately Invoked Function Expression) with all dependencies inlined for easy embedding.

## License

MIT
