# Implementation Plan

A structured plan to build the Chirp AI chatbot widget from the current state to a fully functional MVP.

---

## Current State Assessment

### What Exists
- **Frontend:** Basic React + Vite setup with Shadcn/UI components configured
- **Backend:** Empty `app/` directory, requirements.txt with dependencies
- **Documentation:** Comprehensive PRD, API spec, and quick-start guide
- **Environment:** Python 3.13, uv package manager, .env with API keys

### What Needs to Be Built
- Complete backend API with FastAPI
- Database models and migrations
- Qdrant vector store integration
- Content ingestion pipeline (scraping, chunking, embedding)
- Chat engine with RAG and SSE streaming
- Frontend dashboard (login, bot management, preview)
- Embeddable widget with Shadow DOM
- Docker deployment configuration

---

## Phase 1: Backend Foundation

### 1.1 Project Structure Setup
**Files to create:**
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings and environment variables
│   ├── database.py          # SQLAlchemy async setup
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic request/response models
│   ├── dependencies.py      # FastAPI dependencies (auth, db session)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py          # Login/logout endpoints
│   │   ├── admin.py         # Bot CRUD, avatar, ingestion
│   │   ├── public.py        # Widget config, avatar serving
│   │   └── chat.py          # Main chat endpoint (SSE)
│   └── services/
│       ├── __init__.py
│       ├── auth_service.py  # Password hashing, session management
│       ├── scraper.py       # Web scraping with BeautifulSoup
│       ├── chunker.py       # Text chunking logic
│       ├── embeddings.py    # OpenAI embeddings + Qdrant storage
│       └── chat_service.py  # RAG retrieval + OpenAI chat
├── data/                    # Created at runtime
│   ├── chatbots.db
│   ├── qdrant/
│   └── uploads/avatars/
├── requirements.txt
└── .env
```

**Tasks:**
- [x] Create app package structure with `__init__.py` files
- [x] Implement `config.py` with Pydantic Settings for environment variables
- [x] Create `main.py` with FastAPI app, CORS middleware, route mounting
- [x] Add health check endpoint: `GET /api/health`

### 1.2 Database Layer
**Tasks:**
- [x] Implement `database.py` with async SQLAlchemy engine and session
- [x] Create `models.py` with ORM models:
  - `Bot` (id, name, welcome_message, avatar_url, accent_color, position, show_button_text, button_text, source_type, source_content, api_key, message_count, message_limit, created_at, updated_at)
  - `Conversation` (id, bot_id, session_id, created_at, updated_at)
  - `Message` (id, conversation_id, role, content, created_at)
  - `AdminSession` (id, username, token_hash, expires_at, created_at)
- [x] Create `schemas.py` with Pydantic models for API validation
- [x] Add database initialization on app startup (create tables)
- [x] Create indexes for performance (bot_id, session_id, api_key)

### 1.3 Authentication System
**Tasks:**
- [x] Implement `auth_service.py`:
  - Password hashing with bcrypt (cost factor 12)
  - Session token generation (UUID v4)
  - Token hashing (SHA-256) before storage
  - Session validation and expiry check
- [x] Create admin user on first startup (from env vars)
- [x] Implement `routes/auth.py`:
  - `POST /api/auth/login` - Validate credentials, create session, set cookie
  - `POST /api/auth/logout` - Clear session from DB and cookie
- [x] Create `dependencies.py` with `get_current_admin` dependency for protected routes

---

## Phase 2: Bot Management API

### 2.1 Bot CRUD Endpoints
**Tasks:**
- [x] Implement `routes/admin.py`:
  - `GET /api/admin/bots` - List all bots with stats
  - `POST /api/admin/bots` - Create new bot (generate UUID, API key)
  - `GET /api/admin/bots/{bot_id}` - Get single bot details
  - `PUT /api/admin/bots/{bot_id}` - Update bot configuration
  - `DELETE /api/admin/bots/{bot_id}` - Delete bot (cascade to Qdrant)
- [x] Add request/response schemas for all endpoints
- [x] Add error handling (404, 400, 500)

### 2.2 Avatar Management
**Tasks:**
- [x] Implement avatar upload endpoint:
  - `POST /api/admin/bots/{bot_id}/avatar`
  - Validate file type (magic numbers, not just extension)
  - Check file size (max 500KB)
  - Resize to 64x64px (use Pillow)
  - Save to `./data/uploads/avatars/{bot_id}_{timestamp}.png`
  - Delete old avatar if exists
- [x] Implement avatar delete: `DELETE /api/admin/bots/{bot_id}/avatar`
- [x] Implement public avatar serving: `GET /api/public/avatar/{bot_id}`
- [x] Add Pillow to requirements.txt

### 2.3 API Key Management
**Tasks:**
- [x] Implement key regeneration: `POST /api/admin/bots/{bot_id}/regenerate-key`
- [ ] Hash API keys with SHA-256 before storage (Note: Deferred - not needed for MVP, keys stored as UUIDs)
- [x] Create dependency for widget API key validation

---

## Phase 3: Qdrant Integration

### 3.1 Qdrant Client Setup
**Tasks:**
- [ ] Create `services/qdrant_client.py`:
  - Initialize QdrantClient based on config (local path or server URL)
  - Create collection `chirp_embeddings` if not exists
  - Configure vector params (size=1536, distance=Cosine)
  - Create payload indexes for `bot_id`
- [ ] Add Qdrant health check to `/api/health`

### 3.2 Vector Operations
**Tasks:**
- [ ] Implement upsert function (add/update vectors with payload)
- [ ] Implement search function (query by embedding, filter by bot_id)
- [ ] Implement delete function (remove all vectors for a bot_id)
- [ ] Add similarity threshold filtering (> 0.7)

---

## Phase 4: Content Ingestion Pipeline

### 4.1 Web Scraping
**Tasks:**
- [ ] Implement `services/scraper.py`:
  - URL validation and sanitization (prevent SSRF)
  - Fetch page with httpx (async, with timeout)
  - Parse HTML with BeautifulSoup
  - Extract clean text (strip tags, scripts, styles)
  - Limit to 10,000 words
  - Handle errors gracefully (timeouts, 404s, blocked)

### 4.2 Text Chunking
**Tasks:**
- [ ] Implement `services/chunker.py`:
  - Split text into ~500 token chunks
  - 50 token overlap between chunks
  - Sentence-aware splitting (don't break mid-sentence)
  - Return list of chunks with metadata (index, source)

### 4.3 Embedding Generation
**Tasks:**
- [ ] Implement `services/embeddings.py`:
  - OpenAI API integration for text-embedding-3-small
  - Batch embedding (up to 100 chunks per request)
  - Retry logic with exponential backoff
  - Store embeddings in Qdrant with payload

### 4.4 Ingestion Endpoint
**Tasks:**
- [ ] Implement `POST /api/admin/bots/{bot_id}/ingest`:
  - Read source_type and source_content from bot record
  - If URL: scrape and extract text
  - If text: use directly
  - Chunk the text
  - Generate embeddings
  - Clear old vectors for this bot_id
  - Store new vectors in Qdrant
  - Update bot.updated_at
- [ ] Add background task support (don't block response)
- [ ] Return 202 Accepted with status

---

## Phase 5: Chat Engine

### 5.1 Retrieval Logic
**Tasks:**
- [ ] Implement `services/chat_service.py`:
  - Embed user question with OpenAI
  - Query Qdrant for top 3 similar chunks (filtered by bot_id)
  - Filter by similarity score > 0.7
  - Return chunks with content

### 5.2 Response Generation
**Tasks:**
- [ ] Build prompt template with:
  - Bot name and context
  - Retrieved chunks
  - Conversation history (last 10 messages)
  - User question
  - Instructions (answer only from context)
- [ ] Call OpenAI gpt-4o-mini with streaming enabled
- [ ] Yield tokens as they arrive

### 5.3 Chat Endpoint
**Tasks:**
- [ ] Implement `POST /api/chat` in `routes/chat.py`:
  - Validate API key against bot record
  - Check bot-level rate limit (message_count < message_limit)
  - Check session-level rate limit (10 msg/min)
  - Find or create conversation
  - Save user message to database
  - Retrieve context from Qdrant
  - Stream response via SSE
  - Save assistant response to database
  - Increment message_count
- [ ] Set proper headers for SSE (Content-Type, Cache-Control)
- [ ] Handle errors gracefully (return error events)

### 5.4 Widget Configuration
**Tasks:**
- [ ] Implement `GET /api/public/config/{bot_id}`:
  - Validate API key (query param)
  - Return bot config (name, welcome_message, avatar_url, accent_color, position, button settings)
- [ ] Add rate limiting (60 req/min per bot_id)

---

## Phase 6: Frontend Dashboard

### 6.1 Core Setup
**Tasks:**
- [ ] Set up React Router for navigation
- [ ] Create API client (fetch wrapper with credentials)
- [ ] Implement auth context (login state, session management)
- [ ] Create layout components (sidebar, topbar)
- [ ] Add loading and error state components

### 6.2 Authentication Pages
**Tasks:**
- [ ] Create Login page (`/login`):
  - Username/password form with validation
  - Submit to `/api/auth/login`
  - Redirect to dashboard on success
  - Show error messages on failure
- [ ] Add logout functionality
- [ ] Implement protected route wrapper

### 6.3 Bot Management Pages
**Tasks:**
- [ ] Create Dashboard page (`/dashboard`):
  - Fetch and display bot list as cards
  - Show bot name, avatar, message usage (progress bar)
  - Quick actions: Edit, Test, Delete, Copy Code
  - "Create New Bot" button
- [ ] Create Bot Form page (`/dashboard/bots/new` and `/dashboard/bots/:id`):
  - **Basic Settings Tab:** Name, welcome message
  - **Appearance Tab:**
    - Avatar upload (drag-drop)
    - Color picker
    - Position selector (visual)
    - Button text toggle and input
    - Live preview panel
  - **Knowledge Tab:**
    - Source type toggle (URL/Text)
    - URL input or textarea
    - Train button with progress indicator
    - Last trained timestamp
  - **Settings Tab:**
    - Message limit input
    - API key display with regenerate button
    - Delete bot with confirmation
- [ ] Create Test Chat page (`/dashboard/bots/:id/test`):
  - Full widget preview
  - Reset conversation button
  - Copy embed code button

### 6.4 Settings Page
**Tasks:**
- [ ] Create Settings page (`/dashboard/settings`):
  - Change admin password form
  - Global defaults configuration
  - Database backup/export button

---

## Phase 7: Embeddable Widget

### 7.1 Widget Project Setup
**Tasks:**
- [ ] Create widget directory with Vite config (library mode)
- [ ] Configure build to output single `widget.js`
- [ ] Set up Tailwind CSS scoped to widget

### 7.2 Widget Components
**Tasks:**
- [ ] Create ChatWidget main component:
  - Fetch config on load
  - Apply customization (colors, position, avatar)
  - Manage open/closed state
- [ ] Create ChatBubble (floating button):
  - Custom color support
  - Avatar display
  - Button text toggle
  - Position support (bottom-right, bottom-left, bottom-center)
- [ ] Create ChatWindow:
  - Header with bot name and close button
  - MessageList with auto-scroll
  - MessageInput with send button
- [ ] Create Message component:
  - User messages (accent color)
  - Bot messages (gray, with avatar)
  - Markdown rendering
  - Typing indicator

### 7.3 Widget Logic
**Tasks:**
- [ ] Implement Shadow DOM wrapper:
  - Create host element
  - Attach shadow root
  - Inject styles (isolated)
  - Mount React app inside shadow
- [ ] Implement API integration:
  - Fetch config: `GET /api/public/config/{bot_id}`
  - Send message: `POST /api/chat` (SSE streaming)
  - Parse SSE events and update UI
- [ ] Implement localStorage persistence:
  - Generate session_id on first load
  - Store message history
  - Restore on page reload
- [ ] Handle errors:
  - Network failures
  - Rate limit exceeded
  - API errors

### 7.4 Widget Build
**Tasks:**
- [ ] Configure Vite for library mode output
- [ ] Inline all assets (icons, fonts)
- [ ] Minify and tree-shake
- [ ] Test bundle size (target: <150KB gzipped)
- [ ] Test on sample HTML pages with various CSS frameworks

---

## Phase 8: Testing & Polish

### 8.1 Backend Testing
**Tasks:**
- [ ] Write unit tests for services (auth, chunker, embeddings)
- [ ] Write integration tests for API endpoints
- [ ] Test rate limiting logic
- [ ] Test error handling and edge cases
- [ ] Test with multiple concurrent requests

### 8.2 Frontend Testing
**Tasks:**
- [ ] Test all user flows end-to-end
- [ ] Test responsive design (mobile, tablet, desktop)
- [ ] Test error states and loading states
- [ ] Cross-browser testing (Chrome, Firefox, Safari)

### 8.3 Widget Testing
**Tasks:**
- [ ] Test Shadow DOM isolation
- [ ] Test on sites with different CSS frameworks
- [ ] Test localStorage persistence
- [ ] Test SSE streaming reliability
- [ ] Test mobile responsiveness

### 8.4 Performance Optimization
**Tasks:**
- [ ] Add database connection pooling
- [ ] Optimize Qdrant queries
- [ ] Add caching where appropriate
- [ ] Lazy load frontend components
- [ ] Optimize widget bundle size

---

## Phase 9: Deployment

### 9.1 Docker Setup
**Tasks:**
- [ ] Create Dockerfile (multi-stage build):
  - Python backend
  - Node.js for frontend/widget builds
  - Serve static files from backend
- [ ] Create docker-compose.yml:
  - App service with volumes for data persistence
  - Optional Qdrant service for server mode
  - Environment variable configuration
- [ ] Add .dockerignore file
- [ ] Test Docker build and run

### 9.2 Production Configuration
**Tasks:**
- [ ] Create production environment template
- [ ] Add HTTPS enforcement
- [ ] Configure logging
- [ ] Create backup script (cron job)
- [ ] Add health monitoring

### 9.3 Documentation
**Tasks:**
- [ ] Update README.md with screenshots
- [ ] Create CONTRIBUTING.md
- [ ] Document API endpoints (OpenAPI/Swagger)
- [ ] Create deployment guide
- [ ] Add troubleshooting guide

---

## Implementation Order

### Week 1: Backend Core
1. Phase 1.1: Project structure setup
2. Phase 1.2: Database layer
3. Phase 1.3: Authentication system
4. Phase 2.1: Bot CRUD endpoints
5. Phase 2.2: Avatar management

### Week 2: Ingestion & Chat
1. Phase 2.3: API key management
2. Phase 3: Qdrant integration
3. Phase 4: Content ingestion pipeline
4. Phase 5: Chat engine

### Week 3: Frontend
1. Phase 6.1: Core setup
2. Phase 6.2: Authentication pages
3. Phase 6.3: Bot management pages
4. Phase 6.4: Settings page

### Week 4: Widget & Deployment
1. Phase 7: Embeddable widget
2. Phase 8: Testing & polish
3. Phase 9: Deployment

---

## Success Criteria

### MVP Complete When:
- [ ] Admin can log in and manage bots
- [ ] Bots can be trained from URL or text
- [ ] Widget can be embedded on any site
- [ ] Chat responses use RAG with Qdrant
- [ ] SSE streaming works reliably
- [ ] Rate limiting prevents abuse
- [ ] Docker deployment works end-to-end

### Performance Targets:
- Chat response start: < 3 seconds (p95)
- Widget load time: < 500ms
- Dashboard page load: < 1 second
- Widget bundle size: < 150KB gzipped

### Quality Checklist:
- [ ] All API endpoints have error handling
- [ ] Input validation on all user inputs
- [ ] No console errors in frontend
- [ ] Responsive design works on mobile
- [ ] Shadow DOM isolates widget styles
