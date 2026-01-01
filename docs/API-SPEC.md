# API Specification

Complete reference for all backend endpoints with request/response examples.

---

## Authentication

### Admin Routes (`/api/admin/*`, `/api/auth/*`)
- **Method:** Session-based (cookies)
- **Flow:**
  1. User sends credentials to `/api/auth/login`
  2. Backend validates, creates session token (UUID)
  3. Returns session cookie: `session_token` (HttpOnly, Secure if HTTPS)
  4. Subsequent requests include cookie automatically
  5. Backend validates session on each request

### Widget Routes (`/api/public/*`, `/api/chat`)
- **Method:** API key in request body
- **Flow:**
  1. Widget sends `api_key` + `bot_id` in JSON body
  2. Backend validates `api_key` matches `bots.api_key` for that `bot_id`
  3. Returns 401 if invalid

---

## Endpoints

### 1. Authentication

#### `POST /api/auth/login`
**Purpose:** Admin login  
**Auth:** None  
**Request:**
```json
{
  "username": "admin",
  "password": "secure-password"
}
```
**Response (200):**
```json
{
  "message": "Login successful",
  "username": "admin"
}
```
- Sets cookie: `session_token=<uuid>; HttpOnly; Secure; Max-Age=604800` (7 days)

**Response (401):**
```json
{
  "detail": "Invalid username or password"
}
```

#### `POST /api/auth/logout`
**Purpose:** Clear session  
**Auth:** Session required  
**Response (200):**
```json
{
  "message": "Logged out successfully"
}
```
- Clears `session_token` cookie

---

### 2. Bot Management (Admin)

#### `GET /api/admin/bots`
**Purpose:** List all bots  
**Auth:** Session required  
**Response (200):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Support Bot",
    "welcome_message": "Hi! How can I help?",
    "avatar_url": "/api/public/avatar/550e8400-e29b-41d4-a716-446655440000",
    "accent_color": "#3B82F6",
    "position": "bottom-right",
    "show_button_text": false,
    "button_text": "Chat with us",
    "source_type": "url",
    "source_content": "https://example.com/faq",
    "message_count": 450,
    "message_limit": 1000,
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-20T14:22:00Z"
  }
]
```

#### `POST /api/admin/bots`
**Purpose:** Create new bot  
**Auth:** Session required  
**Request:**
```json
{
  "name": "Help Bot",
  "welcome_message": "Hello! Ask me anything.",
  "accent_color": "#FF5733",
  "position": "bottom-left",
  "show_button_text": true,
  "button_text": "Need help?",
  "source_type": "text",
  "source_content": "Our return policy is 30 days. We ship worldwide.",
  "message_limit": 500
}
```
**Response (201):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "name": "Help Bot",
  "api_key": "770e8400-e29b-41d4-a716-446655440002",
  "message": "Bot created successfully. Training will start in background."
}
```
- Backend triggers ingestion in background task (don't wait for completion)

#### `GET /api/admin/bots/{bot_id}`
**Purpose:** Get single bot details  
**Auth:** Session required  
**Response (200):** Same as item in list above

**Response (404):**
```json
{
  "detail": "Bot not found"
}
```

#### `PUT /api/admin/bots/{bot_id}`
**Purpose:** Update bot configuration  
**Auth:** Session required  
**Request:** (All fields optional)
```json
{
  "name": "Updated Name",
  "welcome_message": "New greeting",
  "accent_color": "#00FF00",
  "position": "bottom-center",
  "show_button_text": false,
  "message_limit": 2000
}
```
**Response (200):**
```json
{
  "message": "Bot updated successfully"
}
```

#### `DELETE /api/admin/bots/{bot_id}`
**Purpose:** Delete bot (also removes from ChromaDB)  
**Auth:** Session required  
**Response (200):**
```json
{
  "message": "Bot deleted successfully"
}
```
- Must cascade delete: conversations, messages, avatar file, ChromaDB chunks

---

### 3. Content Ingestion

#### `POST /api/admin/bots/{bot_id}/ingest`
**Purpose:** Train/re-train bot with content  
**Auth:** Session required  
**Request:** (No body, uses `source_type` and `source_content` from bot record)  
**Response (202):**
```json
{
  "message": "Ingestion started",
  "bot_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing"
}
```
**Background Process:**
1. If `source_type == "url"`: Scrape website (max 10K words)
2. If `source_type == "text"`: Use `source_content` directly
3. Chunk text (500 tokens, 50 overlap)
4. Generate embeddings (OpenAI `text-embedding-3-small`)
5. Clear old chunks from ChromaDB for this `bot_id`
6. Store new chunks in ChromaDB with metadata: `{"bot_id": "...", "chunk_index": 0}`
7. Update `bots.updated_at`

**Response (400) if scraping fails:**
```json
{
  "detail": "Failed to scrape URL: Connection timeout"
}
```

---

### 4. Avatar Management

#### `POST /api/admin/bots/{bot_id}/avatar`
**Purpose:** Upload bot avatar  
**Auth:** Session required  
**Request:** `multipart/form-data`
```
POST /api/admin/bots/550e8400-e29b-41d4-a716-446655440000/avatar
Content-Type: multipart/form-data

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="logo.png"
Content-Type: image/png

<binary image data>
------WebKitFormBoundary--
```
**Response (200):**
```json
{
  "message": "Avatar uploaded successfully",
  "avatar_url": "/api/public/avatar/550e8400-e29b-41d4-a716-446655440000"
}
```
**Processing:**
1. Validate file type (PNG, JPG, JPEG, GIF)
2. Check file size (max 500KB)
3. Resize to 64x64px (center crop)
4. Save to `./data/uploads/avatars/{bot_id}_{timestamp}.png`
5. Delete old avatar if exists
6. Update `bots.avatar_url`

**Response (400):**
```json
{
  "detail": "File too large. Max size: 500KB"
}
```

#### `DELETE /api/admin/bots/{bot_id}/avatar`
**Purpose:** Remove avatar  
**Auth:** Session required  
**Response (200):**
```json
{
  "message": "Avatar deleted successfully"
}
```

#### `GET /api/public/avatar/{bot_id}`
**Purpose:** Serve avatar image  
**Auth:** None  
**Response (200):** Binary image file (PNG)  
**Response (404):** If no avatar uploaded

---

### 5. API Key Management

#### `POST /api/admin/bots/{bot_id}/regenerate-key`
**Purpose:** Generate new API key for widget  
**Auth:** Session required  
**Response (200):**
```json
{
  "api_key": "880e8400-e29b-41d4-a716-446655440003",
  "message": "New API key generated. Update your widget embed code."
}
```
- Invalidates old key immediately

---

### 6. Widget Configuration

#### `GET /api/public/config/{bot_id}`
**Purpose:** Get widget configuration (called by widget on load)  
**Auth:** API key required (query param: `?api_key=...`)  
**Request:**
```
GET /api/public/config/550e8400-e29b-41d4-a716-446655440000?api_key=770e8400-e29b-41d4-a716-446655440002
```
**Response (200):**
```json
{
  "name": "Support Bot",
  "welcome_message": "Hi! How can I help?",
  "avatar_url": "/api/public/avatar/550e8400-e29b-41d4-a716-446655440000",
  "accent_color": "#3B82F6",
  "position": "bottom-right",
  "show_button_text": false,
  "button_text": "Chat with us"
}
```

**Response (401):**
```json
{
  "detail": "Invalid API key"
}
```

---

### 7. Chat (Main Endpoint)

#### `POST /api/chat`
**Purpose:** Send message, get AI response  
**Auth:** API key in body  
**Request:**
```json
{
  "bot_id": "550e8400-e29b-41d4-a716-446655440000",
  "api_key": "770e8400-e29b-41d4-a716-446655440002",
  "session_id": "client-session-abc123",
  "message": "What is your return policy?",
  "conversation_history": [
    {
      "role": "user",
      "content": "Hi"
    },
    {
      "role": "assistant",
      "content": "Hello! How can I help you today?"
    }
  ]
}
```

**Response (200):** Server-Sent Events (SSE) stream
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

data: {"type": "token", "content": "Our"}

data: {"type": "token", "content": " return"}

data: {"type": "token", "content": " policy"}

data: {"type": "token", "content": " is"}

data: {"type": "token", "content": " 30"}

data: {"type": "token", "content": " days"}

data: {"type": "token", "content": "."}

data: {"type": "done"}

```

**Logic:**
1. **Validate API key:** Check `api_key` matches `bots.api_key`
2. **Check rate limits:**
   - Bot-level: `message_count < message_limit`
   - Session-level: Max 10 messages/minute per `session_id`
3. **Find or create conversation:** Use `session_id` to track conversation
4. **Save user message:** Store in `messages` table
5. **Retrieve context:**
   - Embed user's question (OpenAI embeddings)
   - Query ChromaDB: Top 3 chunks where `metadata.bot_id == bot_id`
   - Filter by similarity > 0.7
6. **Generate response:**
   - Build prompt with retrieved chunks + last 10 messages
   - Call OpenAI `gpt-4o-mini` with streaming
   - Stream tokens back as SSE
7. **Save assistant message:** Store complete response
8. **Increment counter:** `bots.message_count += 1`

**Prompt Template:**
```
You are a helpful customer support assistant for {bot_name}.

Context from knowledge base:
{chunk_1}
{chunk_2}
{chunk_3}

Conversation history:
{last_10_messages}

User question: {current_message}

Instructions:
- Answer using ONLY the context provided above
- Be helpful, concise, and friendly
- If the answer isn't in the context, say "I don't have that information in my knowledge base. Please contact us directly for help with this."
- Do not make up information
```

**Response (401):**
```json
{
  "detail": "Invalid API key for this bot"
}
```

**Response (429):**
```json
{
  "detail": "Monthly message limit reached for this bot. Please contact the website owner."
}
```

**Response (429) for session rate limit:**
```json
{
  "detail": "Too many requests. Please wait a moment before sending another message."
}
```

---

## Error Codes Reference

| Status | Code | Description |
|--------|------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created |
| 202 | Accepted | Background task started |
| 400 | Bad Request | Validation error (invalid input) |
| 401 | Unauthorized | Invalid credentials or API key |
| 403 | Forbidden | Valid auth but no permission |
| 404 | Not Found | Resource doesn't exist |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error (log and investigate) |

---

## Rate Limiting Rules

### Admin Routes
- **Limit:** 100 requests/minute per IP
- **Scope:** All `/api/admin/*` and `/api/auth/*` routes
- **Action on exceed:** Return 429

### Chat Endpoint
- **Bot-level limit:** Check `message_count < message_limit`
- **Session-level limit:** 10 messages/minute per `session_id`
- **Implementation:** Use in-memory cache (e.g., Python dict with timestamps) or Redis

### Config Endpoint
- **Limit:** 60 requests/minute per `bot_id`
- **Prevents:** Widget spamming config endpoint

---

## CORS Configuration

### Admin Routes (`/api/admin/*`, `/api/auth/*`)
- **Allowed Origins:** Frontend dashboard URL only (e.g., `http://localhost:3000` in dev)
- **Credentials:** Allow (needed for session cookies)
- **Methods:** GET, POST, PUT, DELETE, OPTIONS

### Widget Routes (`/api/public/*`, `/api/chat`)
- **Allowed Origins:** `*` (widget needs to work on any domain)
- **Credentials:** Not required
- **Methods:** GET, POST, OPTIONS
- **Exposed Headers:** `Content-Type`

**FastAPI CORS Middleware Example:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For /api/public/* and /api/chat
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## WebSocket Alternative (Optional)

If SSE doesn't work well, chat can use WebSocket instead:

#### `WS /api/chat/ws`
**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/chat/ws?bot_id=xxx&api_key=yyy&session_id=zzz');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'token') {
    appendToken(data.content);
  }
};

ws.send(JSON.stringify({
  message: "What is your return policy?",
  conversation_history: [...]
}));
```

**Message Format (Server → Client):**
```json
{"type": "token", "content": "word"}
{"type": "done"}
{"type": "error", "message": "Rate limit exceeded"}
```

---

## Sample cURL Commands

**Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' \
  -c cookies.txt
```

**Create Bot:**
```bash
curl -X POST http://localhost:8000/api/admin/bots \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "Test Bot",
    "welcome_message": "Hi there!",
    "source_type": "text",
    "source_content": "We ship worldwide. Returns are free."
  }'
```

**Chat:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "bot_id": "550e8400-e29b-41d4-a716-446655440000",
    "api_key": "770e8400-e29b-41d4-a716-446655440002",
    "session_id": "test-session",
    "message": "What are your shipping options?",
    "conversation_history": []
  }'
```

---

## Testing Checklist

After implementing endpoints:
- [ ] Can login with correct credentials
- [ ] Login fails with wrong password
- [ ] Can create bot (returns `bot_id` and `api_key`)
- [ ] Can list all bots (returns array)
- [ ] Can update bot configuration
- [ ] Can delete bot (removes from DB and ChromaDB)
- [ ] Can upload avatar (file validation works)
- [ ] Can trigger ingestion (background task starts)
- [ ] Can get widget config with valid API key
- [ ] Widget config fails with invalid API key
- [ ] Can send chat message (get streaming response)
- [ ] Chat fails if message limit exceeded
- [ ] Chat fails if session rate limit hit
- [ ] Logout clears session cookie

---

**Use this spec to implement each endpoint systematically. Test with cURL or Postman before integrating with frontend.**
