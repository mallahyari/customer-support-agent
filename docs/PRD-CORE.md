# PRD-CORE: Open Source AI Chatbot Widget
**Version:** 1.0 (OSS Foundation)  
**License:** MIT  
**Target:** Self-hostable, single-tenant chatbot for small businesses  
**Deployment:** Docker-ready, designed for one business per installation  
**Date:** December 2025

---

## 1. Executive Summary

An open source chatbot widget that lets business owners add AI-powered customer support to their website. Business owner provides content (via URL scraping or direct text), the system creates a knowledge base, and visitors can ask questions answered by the AI using only that knowledge.

**Key Principle:** Simple, self-hostable, and extensible. No vendor lock-in.

**Core Value Proposition:**
- Deploy in 10 minutes via Docker
- Train on your content (website or text)
- Embed with one line of code
- Customize to match your brand
- Own your data completely

---

## 2. Technical Architecture

### 2.1 Tech Stack
- **Frontend (Dashboard):** React (Vite) + TypeScript + TailwindCSS + Shadcn/UI
- **Frontend (Widget):** React (compiled to single `widget.js` via Vite library mode)
- **Backend (API):** Python FastAPI
- **Database:** SQLite + SQLAlchemy (Async)
- **Vector Store:** ChromaDB (embedded, file-based - no separate service needed)
- **Embeddings:** OpenAI `text-embedding-3-small` (cheap, good quality)
- **LLM:** OpenAI `gpt-4o-mini` (fast, cheap for MVP)
- **Scraping:** `crawl4ai` or `BeautifulSoup4`
- **Authentication:** Simple API key system (no third-party auth - keep it self-hostable)
- **File Storage:** Local filesystem for avatars/uploads

### 2.2 Why These Choices?
- **ChromaDB:** Embedded mode = zero infrastructure, just a local folder
- **OpenAI:** Most reliable, well-documented, cheap for MVP ($0.0001/1K tokens for embeddings)
- **SQLite:** Perfect for single-tenant, easy to backup, no DB server needed
- **No Third-Party Auth:** Open source projects should avoid proprietary services
- **Local File Storage:** Simple, no S3 dependency for OSS version

---

## 3. Core User Flows

### 3.1 Initial Setup (One-Time)
1. **Deploy:** User runs Docker container or `pip install` + runs FastAPI
2. **Configure:** User sets `OPENAI_API_KEY` in `.env`
3. **Access Dashboard:** User opens `http://localhost:3000` (or their domain)
4. **Set Admin Password:** First-time setup creates an admin account (username/password stored hashed in SQLite)

### 3.2 Creating a Bot
1. **Login:** User logs into dashboard with admin credentials
2. **Create Bot:** User clicks "New Bot" and provides:
   - Bot name (e.g., "Support Bot")
   - Welcome message (e.g., "Hi! How can I help?")
   - **Visual customization:**
     - Upload bot avatar (optional, 64x64px image)
     - Select accent color (hex picker)
     - Choose widget position (bottom-right, bottom-left, bottom-center)
     - Toggle button text on/off
     - Customize button text (default: "Chat with us")
3. **Add Knowledge:** User chooses one of:
   - **Option A:** Paste text/markdown directly
   - **Option B:** Provide a single URL to scrape
4. **Process (Backend):**
   - Scrape URL (if provided) - **limit: first 10,000 words only**
   - Chunk text into ~500-token segments
   - Generate embeddings via OpenAI
   - Store in ChromaDB with bot_id as metadata filter
5. **Generate Widget Code:** System creates unique `bot_id` and shows embed code:
   ```html
   <script 
     src="http://your-domain.com/widget.js" 
     data-bot-id="abc123"
     data-api-key="widget-key-xyz"
   ></script>
   ```
6. **Preview:** User sees live preview of customized widget
7. **Test:** User can test chat in dashboard preview before deploying

### 3.3 End User Interaction (Widget)
1. **Load:** Visitor lands on client website, widget loads (customized position and color)
2. **See Brand:** Widget shows uploaded avatar (if any) and custom colors
3. **Chat:** Visitor clicks bubble (sees custom button text if enabled), types "What are your hours?"
4. **Backend Process:**
   - Receive message + `bot_id` + `api_key`
   - Verify API key
   - Check message limits
   - Embed the question
   - Query ChromaDB for top 3 most relevant chunks (filtered by `bot_id`)
   - Send chunks + question to GPT-4o-mini with prompt: "Answer using ONLY this context"
   - Stream response back to widget
5. **Display:** Answer appears in chat bubble with bot's custom styling

---

## 4. Database Schema (SQLite)

### Table: `bots`
| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT (PK) | UUID, used in widget embed code |
| `name` | TEXT | Display name (e.g., "Help Bot") |
| `welcome_message` | TEXT | Initial greeting |
| `avatar_url` | TEXT | Path to uploaded avatar image (nullable) |
| `accent_color` | TEXT | Hex color for buttons/user bubbles (default: `#3B82F6`) |
| `position` | TEXT | Widget position: `bottom-right`, `bottom-left`, `bottom-center` |
| `show_button_text` | BOOLEAN | Show text label on chat button (default: `false`) |
| `button_text` | TEXT | Custom button text (default: "Chat with us") |
| `source_type` | TEXT | `"url"` or `"text"` |
| `source_content` | TEXT | The original URL or pasted text |
| `api_key` | TEXT | Unique key for widget requests (UUID) |
| `message_count` | INTEGER | Track total messages for this bot |
| `message_limit` | INTEGER | Max messages allowed (default: 1000/month) |
| `created_at` | DATETIME | Timestamp |
| `updated_at` | DATETIME | Last modified |

### Table: `conversations`
| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT (PK) | UUID |
| `bot_id` | TEXT (FK) | References `bots.id` |
| `session_id` | TEXT | Browser fingerprint or random ID from widget |
| `created_at` | DATETIME | Conversation start time |
| `updated_at` | DATETIME | Last message time |

### Table: `messages`
| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT (PK) | UUID |
| `conversation_id` | TEXT (FK) | References `conversations.id` |
| `role` | TEXT | `"user"` or `"assistant"` |
| `content` | TEXT | Message text |
| `created_at` | DATETIME | Timestamp |

**Note:** 
- ChromaDB handles vector storage separately (stored in `./chroma_data/` folder)
- Avatar images stored in `./data/uploads/avatars/` folder

---

## 5. Functional Requirements

### 5.1 Avatar Upload
**Endpoint:** `POST /api/admin/bots/{bot_id}/avatar`

**Logic:**
1. **Validation:**
   - Accept only `.png`, `.jpg`, `.jpeg`, `.gif`
   - Max file size: 500KB
   - Validate image dimensions (recommend 64x64 to 256x256)
2. **Processing:**
   - Resize to 64x64px (maintain aspect ratio, center crop if needed)
   - Generate unique filename: `{bot_id}_{timestamp}.png`
   - Save to `./data/uploads/avatars/`
   - Update `bots.avatar_url` with relative path
3. **Security:**
   - Sanitize filename (prevent path traversal)
   - Verify file is actual image (not just extension)
   - Delete old avatar if replacing

**Endpoint:** `DELETE /api/admin/bots/{bot_id}/avatar`
- Removes avatar file from filesystem
- Sets `bots.avatar_url` to NULL

### 5.2 Content Ingestion
**Endpoint:** `POST /api/admin/bots/{bot_id}/ingest`

**Logic:**
1. **Input Validation:**
   - If `source_type == "url"`: Validate URL, check it's accessible
   - If `source_type == "text"`: Accept up to 50,000 characters
2. **Scraping (if URL):**
   - Use `crawl4ai` to extract clean text
   - **Limit:** First 10,000 words only (prevent abuse)
   - Strip HTML, keep only readable content
   - Handle errors gracefully (timeouts, 404s, etc.)
3. **Chunking:**
   - Split text into ~500 token chunks with 50 token overlap
   - Use simple sentence-boundary splitting (don't split mid-sentence)
   - Maintain chunk metadata (source, index)
4. **Embedding:**
   - Generate embeddings for each chunk using OpenAI
   - Cost estimate: ~$0.01 per 10,000 words
   - Batch requests for efficiency (up to 100 chunks per API call)
5. **Storage:**
   - Store in ChromaDB with metadata: `{"bot_id": "...", "chunk_index": 0, "source": "..."}`
   - Update `bots.updated_at`
   - Clear old chunks if re-training

**Error Handling:**
- If URL unreachable: Return error, suggest pasting content instead
- If OpenAI API fails: Retry 3 times with exponential backoff, then fail gracefully
- If scraping times out: Return partial content if >1000 words scraped

### 5.3 Chat Logic
**Endpoint:** `POST /api/chat`

**Request Body:**
```json
{
  "bot_id": "abc123",
  "api_key": "widget-key-here",
  "session_id": "visitor-session-xyz",
  "message": "What is your return policy?",
  "conversation_history": [
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello! How can I help?"}
  ]
}
```

**Logic:**
1. **Authentication:**
   - Verify `api_key` matches `bots.api_key` for this `bot_id`
   - If invalid: Return 401 Unauthorized
2. **Rate Limiting:**
   - Check `bots.message_count < bots.message_limit`
   - If exceeded: Return 429 "Monthly limit reached. Please contact the website owner."
   - Increment `message_count` atomically
3. **Session Rate Limiting:**
   - Max 10 messages per minute per `session_id`
   - Prevent spam/abuse
4. **Conversation Management:**
   - Find or create `conversations` entry for this `session_id`
   - Store user message in `messages` table
   - Keep last 10 messages from history for context (trim older ones)
5. **Retrieval:**
   - Embed user's question using OpenAI
   - Query ChromaDB: Get top 3 chunks where `metadata.bot_id == bot_id`
   - Include similarity scores (threshold: 0.7+)
6. **Generation:**
   - Construct prompt:
     ```
     You are a helpful customer support assistant for [Bot Name].
     
     Context from knowledge base:
     [Chunk 1]
     [Chunk 2]
     [Chunk 3]
     
     Conversation history:
     [Last 10 messages]
     
     User question: [Current message]
     
     Instructions: 
     - Answer using ONLY the context provided above
     - Be helpful, concise, and friendly
     - If the answer isn't in the context, say "I don't have that information in my knowledge base. Please contact us directly for help with this."
     - Do not make up information
     ```
   - Call OpenAI `gpt-4o-mini` with streaming enabled
   - Stream response back to client via SSE
7. **Storage:**
   - Save complete assistant response to `messages` table
   - Update `conversations.updated_at`

**Response Format:** Server-Sent Events (SSE) stream
```
data: {"type": "token", "content": "Hello"}
data: {"type": "token", "content": " there"}
data: {"type": "done"}
```

### 5.4 Widget Technical Specs

**Build Process:**
- Vite library mode compiles React app to single `widget.js` (~150KB gzipped)
- Includes Tailwind CSS (scoped to Shadow DOM)
- Bundles avatar/icon assets inline as base64

**Shadow DOM Implementation:**
```javascript
// Conceptual - prevents client site CSS from breaking widget
const shadowHost = document.createElement('div');
shadowHost.id = 'chatbot-widget-host';
document.body.appendChild(shadowHost);

const shadowRoot = shadowHost.attachShadow({mode: 'open'});
// Render React app inside shadowRoot with isolated styles
```

**Widget Features:**
- **Positioning:** Respects `position` setting from bot config
- **Customization:** Applies accent color, avatar, button text dynamically
- **Chat Bubble:**
  - Customizable color (uses `accent_color`)
  - Shows avatar if uploaded (falls back to default icon)
  - Button text toggle (icon-only or text label)
- **Message Display:**
  - User messages: Accent color background
  - Bot messages: Light gray background, avatar on left
  - Markdown support in bot responses (links, lists, bold)
- **Persistence:**
  - Message history persisted in `localStorage` (keyed by `session_id`)
  - Auto-generates `session_id` on first load (stored in localStorage)
  - Survives page reloads
- **States:**
  - Loading states during streaming (animated dots)
  - Error states (rate limit, network failure, API errors)
  - Typing indicators
  - Auto-scroll to latest message
- **Responsive:**
  - Mobile-optimized (full-screen on small devices)
  - Desktop: Fixed width (380px), max height (600px)

**Configuration:**
```html
<script 
  src="https://your-domain.com/widget.js" 
  data-bot-id="abc123"
  data-api-key="widget-key-xyz"
></script>
```

**API Calls Made by Widget:**
1. **On Load:** `GET /api/public/config/{bot_id}` (fetch customization)
2. **On Message:** `POST /api/chat` (send message, receive stream)

### 5.5 Admin Dashboard Features

**Pages:**

1. **Login (`/login`):**
   - Simple username/password form
   - "Remember me" checkbox (7-day session)
   - Password reset flow (email-based, optional for OSS)

2. **Bots List (`/dashboard`):**
   - Card grid showing all bots
   - Each card displays:
     - Bot name + avatar thumbnail
     - Message count with progress bar (e.g., "450/1000 messages - 45%")
     - Status indicator (active/training/error)
     - Quick actions: Edit, Test, Delete, Copy Code
   - "Create New Bot" button (prominent)
   - Search/filter (if >10 bots)

3. **Create/Edit Bot (`/dashboard/bots/new` or `/dashboard/bots/{id}`):**
   - **Basic Settings Tab:**
     - Bot name (required)
     - Welcome message (textarea, 200 char max)
   - **Appearance Tab:**
     - Avatar upload (drag-drop or click)
     - Color picker (accent color)
     - Position selector (visual radio buttons showing placement)
     - Button text toggle + custom text input
     - Live preview panel (shows widget as configured)
   - **Knowledge Tab:**
     - Source type selector (URL or Text)
     - URL input (with "Test URL" button) OR text area
     - "Train Bot" button
     - Training status indicator
     - Last trained timestamp
     - "Re-train" button (if already trained)
   - **Settings Tab:**
     - Monthly message limit (number input)
     - API key display (with regenerate button)
     - Delete bot (with confirmation modal)

4. **Test Chat (`/dashboard/bots/{id}/test`):**
   - Full-screen live preview of widget
   - Shows exactly what end users will see
   - Functional chat (uses real API)
   - Reset conversation button
   - "Copy Embed Code" button (always visible)

5. **Settings (`/dashboard/settings`):**
   - Change admin password
   - View OpenAI API key status (not the key itself)
   - Global defaults (default message limit for new bots)
   - Database backup/export (download SQLite file)

**Navigation:**
- Top bar: Logo, Bot count, Settings icon, Logout
- Mobile: Hamburger menu

---

## 6. API Specifications

### Authentication

**Dashboard Routes (`/api/admin/*`):**
- Require session cookie (set after login)
- Cookie: `session_token`, HttpOnly, Secure (if HTTPS)
- Session expires after 7 days (or on logout)

**Widget Routes (`/api/public/*` and `/api/chat`):**
- Require valid `api_key` in request body
- No session needed

### Endpoints Summary

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/api/auth/login` | None | Admin login (returns session cookie) |
| POST | `/api/auth/logout` | Session | Clear session cookie |
| GET | `/api/admin/bots` | Session | List all bots with stats |
| POST | `/api/admin/bots` | Session | Create new bot |
| GET | `/api/admin/bots/{id}` | Session | Get single bot details |
| PUT | `/api/admin/bots/{id}` | Session | Update bot config |
| DELETE | `/api/admin/bots/{id}` | Session | Delete bot (also clears ChromaDB) |
| POST | `/api/admin/bots/{id}/ingest` | Session | Trigger training/re-training |
| POST | `/api/admin/bots/{id}/avatar` | Session | Upload avatar image |
| DELETE | `/api/admin/bots/{id}/avatar` | Session | Remove avatar |
| POST | `/api/admin/bots/{id}/regenerate-key` | Session | Generate new API key |
| GET | `/api/public/config/{bot_id}` | API Key | Get widget config (name, color, avatar, etc.) |
| POST | `/api/chat` | API Key | Main chat endpoint (SSE stream) |
| GET | `/api/public/avatar/{bot_id}` | None | Serve avatar image file |

**CORS Configuration:**
- Allow `*` for `/api/public/*` and `/api/chat` (widget needs to work on any domain)
- Allow credentials for `/api/admin/*` (session cookies)
- Expose headers: `Content-Type`, `Authorization`

**Rate Limiting:**
- Dashboard routes: 100 requests/minute per IP
- Chat endpoint: 10 requests/minute per `session_id`
- Config endpoint: 60 requests/minute per `bot_id`

---

## 7. Non-Functional Requirements

### 7.1 Performance
- Chat response time: < 3 seconds (p95) for streaming start
- Widget load time: < 500ms (gzipped bundle)
- Dashboard page load: < 1 second
- Support 10 concurrent chat requests (sufficient for single business)
- Avatar image optimization: Resize to 64x64, convert to WebP if supported

### 7.2 Security
- **API Keys:** UUIDs (v4), hashed in database using SHA-256
- **Admin Passwords:** bcrypt with salt (cost factor: 12)
- **Session Tokens:** Random 32-byte tokens, hashed before storage
- **File Uploads:**
  - Validate file types using magic numbers (not just extensions)
  - Sanitize filenames (prevent path traversal: `../../etc/passwd`)
  - Virus scan (optional, via ClamAV integration)
- **Input Validation:**
  - Sanitize all user inputs (XSS prevention)
  - SQL injection protection (use parameterized queries)
  - URL validation (prevent SSRF attacks when scraping)
- **HTTPS:** Enforce in production (redirect HTTP → HTTPS)
- **CORS:** Strict origin checking for admin routes

### 7.3 Scalability (for OSS Users)
- **SQLite:** Up to 100GB database size (sufficient for thousands of bots)
- **ChromaDB:** Tested up to millions of vectors (embedded mode)
- **File Storage:** Up to 10GB avatars (10,000 bots × 1MB each)
- **When to Scale:** 
  - If user needs 100+ concurrent requests → suggest managed hosting (your SaaS)
  - If database >50GB → migrate to PostgreSQL (provide guide)
  - If vector search slow → migrate to Pinecone/Weaviate

### 7.4 Cost Controls (Built-in)
- **Default Limits:**
  - Message limit: 1,000/month per bot
  - Training limit: 10,000 words per URL
  - Avatar size: 500KB max
- **Estimated Costs (per bot/month):**
  - Embedding cost: ~$0.01 per 10K words ingested (one-time)
  - Chat cost: ~$0.10 for 1,000 messages (using gpt-4o-mini)
  - Storage: Negligible (<1MB per bot in SQLite)
- **Admin Controls:**
  - Adjustable message limits per bot
  - Global default limits in settings
  - Usage dashboard to monitor costs

### 7.5 Reliability
- **Error Recovery:**
  - Auto-retry OpenAI API calls (3 attempts, exponential backoff)
  - Graceful degradation (if embeddings fail, allow text-only mode)
  - Database connection pooling with reconnection logic
- **Backups:**
  - Automatic SQLite backups (daily via cron)
  - Backup ChromaDB data folder
  - Backup avatars folder
  - Export format: `.tar.gz` with timestamp
- **Monitoring:**
  - Health check endpoint: `GET /api/health`
  - Log errors to `./logs/error.log`
  - Track API usage/costs (optional dashboard)

---

## 8. Deployment

### 8.1 Docker (Recommended)

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  chatbot:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ADMIN_USERNAME=${ADMIN_USERNAME}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
```

**Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Build frontend & widget
RUN cd frontend && npm install && npm run build
RUN cd widget && npm install && npm run build

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Environment Variables (.env):**
```bash
# Required
OPENAI_API_KEY=sk-...

# Admin Account (first-time setup)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password

# Paths (defaults shown)
DATABASE_URL=sqlite:///./data/chatbots.db
CHROMA_PATH=./data/chroma_data
UPLOAD_PATH=./data/uploads

# Limits
MESSAGE_LIMIT_DEFAULT=1000
MAX_SCRAPE_WORDS=10000
AVATAR_MAX_SIZE_KB=500

# Optional
LOG_LEVEL=INFO
BACKUP_ENABLED=true
BACKUP_SCHEDULE=0 2 * * *  # Daily at 2 AM
```

**Quick Start:**
```bash
# 1. Clone repo
git clone https://github.com/yourusername/chatbot-oss
cd chatbot-oss

# 2. Create .env file
cp .env.example .env
# Edit .env with your OpenAI API key

# 3. Run
docker-compose up -d

# 4. Access dashboard
open http://localhost:8000
```

### 8.2 Manual Setup (Development)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend (Dashboard):**
```bash
cd frontend
npm install
npm run dev  # Runs on port 3000
```

**Widget Build:**
```bash
cd widget
npm install
npm run build  # Outputs to backend/static/widget.js
```

**Database Setup:**
```bash
# Auto-created on first run, or manually:
python scripts/init_db.py
```

### 8.3 Production Deployment

**Recommended Stack:**
- **Server:** Ubuntu 22.04 LTS (2GB RAM minimum)
- **Reverse Proxy:** Nginx or Caddy
- **SSL:** Let's Encrypt (via Certbot)
- **Process Manager:** Docker Compose or systemd

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name chatbot.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name chatbot.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/chatbot.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/chatbot.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Enable streaming for chat endpoint
    location /api/chat {
        proxy_pass http://localhost:8000;
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        chunked_transfer_encoding off;
    }
}
```

**Security Checklist:**
- [ ] HTTPS enabled with valid certificate
- [ ] Firewall configured (allow only 80, 443, SSH)
- [ ] SSH key-only authentication
- [ ] Strong admin password (20+ characters)
- [ ] Database backups automated
- [ ] Logs monitored (e.g., via Logtail or Papertrail)
- [ ] Regular security updates (`apt update && apt upgrade`)

---

## 9. MVP Roadmap (2-3 Weeks)

### Week 1: Backend Core
**Days 1-2: Foundation**
- [x] FastAPI project setup + project structure
- [x] SQLite database models (bots, conversations, messages)
- [x] Alembic migrations setup
- [x] Admin authentication system (login, sessions, bcrypt)
- [x] CRUD endpoints for bots
- [x] Basic error handling & logging

**Days 3-4: Knowledge Pipeline**
- [x] Web scraping implementation (crawl4ai or BeautifulSoup)
- [x] URL validation & error handling
- [x] Text chunking logic (sentence-aware, 500 tokens)
- [x] OpenAI embeddings integration
- [x] ChromaDB setup (embedded mode)
- [x] Ingestion endpoint with progress tracking
- [x] Test with 5+ diverse websites (FAQ pages, docs, blogs)

**Days 5-7: Chat Engine**
- [x] Conversation & message storage
- [x] Session management (session_id tracking)
- [x] Retrieval logic (embed query → ChromaDB search)
- [x] OpenAI chat completion with streaming (SSE)
- [x] Context window management (last 10 messages)
- [x] API key authentication for widget
- [x] Rate limiting (per-bot and per-session)
- [x] Usage tracking (message count increments)
- [x] Error responses for limits exceeded

### Week 2: Frontend
**Days 8-10: Dashboard**
- [x] React + Vite project setup
- [x] Tailwind CSS + Shadcn/UI components
- [x] Login page with form validation
- [x] Dashboard layout (sidebar, top bar)
- [x] Bots list page (cards with stats)
- [x] Create/Edit bot form:
  - [x] Basic settings (name, welcome message)
  - [x] Appearance (color picker, position selector)
  - [x] Avatar upload (drag-drop + preview)
  - [x] Button text customization
  - [x] Live preview panel
- [x] Knowledge ingestion UI:
  - [x] URL/text toggle
  - [x] Training status indicator
  - [x] Progress bar during ingestion
- [x] API integration (all endpoints)
- [x] Loading states & error handling
- [x] Settings page (password change, defaults)

**Days 11-14: Widget**
- [x] React chat UI component:
  - [x] Message list with auto-scroll
  - [x] Input field with send button
  - [x] User/bot message bubbles
  - [x] Markdown rendering in bot messages
  - [x] Typing indicators
  - [x] Error states
- [x] Shadow DOM wrapper
  - [x] Isolated styles (no conflicts)
  - [x] Position support (all 3 positions)
  - [x] Custom color application
  - [x] Avatar display
  - [x] Button text toggle
- [x] API integration:
  - [x] Fetch config on load
  - [x] SSE chat streaming
  - [x] Error handling (network, rate limits)
- [x] localStorage persistence:
  - [x] Session ID generation
  - [x] Message history storage
  - [x] Restore on page reload
- [x] Vite library build:
  - [x] Bundle to single widget.js
  - [x] Inline assets (icons, fonts)
  - [x] Minification & tree-shaking
- [x] Responsive design:
  - [x] Mobile full-screen mode
  - [x] Desktop fixed size
- [x] Browser testing (Chrome, Firefox, Safari)
- [x] Test on sample HTML page with various CSS frameworks

### Week 3: Polish & Launch
**Days 15-17: Integration & Testing**
- [x] Connect dashboard to all backend APIs
- [x] End-to-end testing:
  - [x] Create bot → train → test chat → deploy
  - [x] Multi-bot management
  - [x] Rate limit enforcement
  - [x] Avatar upload/delete
  - [x] Re-training flow
- [x] Handle edge cases:
  - [x] Empty knowledge base
  - [x] Scraping failures
  - [x] API timeouts
  - [x] Concurrent requests
- [x] Performance optimization:
  - [x] Database indexing
  - [x] Lazy loading in dashboard
  - [x] Widget bundle size reduction
- [x] Docker setup:
  - [x] Multi-stage Dockerfile
  - [x] docker-compose.yml
  - [x] Environment variable validation
  - [x] Volume persistence
- [x] Production readiness:
  - [x] Health check endpoint
  - [x] Logging configuration
  - [x] Backup script (cron job)
  - [x] HTTPS enforcement

**Days 18-21: Documentation & Release**
- [ ] Write comprehensive **README.md**:
  - [ ] What it does (with screenshots/GIFs)
  - [ ] Quick start (Docker one-liner)
  - [ ] Manual setup steps
  - [ ] Configuration options
  - [ ] Troubleshooting guide
- [ ] **CONTRIBUTING.md**:
  - [ ] How to run locally
  - [ ] Code style guide (Black, ESLint configs)
  - [ ] PR process & guidelines
  - [ ] Issue templates
- [ ] **docs/ARCHITECTURE.md**:
  - [ ] System diagram (draw.io or Excalidraw)
  - [ ] Data flow explanation
  - [ ] Tech stack rationale
  - [ ] ChromaDB vs alternatives comparison
- [ ] **docs/API.md**:
  - [ ] All endpoints documented (OpenAPI/Swagger)
  - [ ] Example requests/responses
  - [ ] Authentication flow
  - [ ] Error codes reference
- [ ] **docs/DEPLOYMENT.md**:
  - [ ] Production checklist
  - [ ] Nginx/Caddy reverse proxy setup
  - [ ] SSL certificate guide (Let's Encrypt)
  - [ ] Backup & restore procedures
  - [ ] Migration guide (SQLite → PostgreSQL)
- [ ] **docs/CUSTOMIZATION.md**:
  - [ ] Widget styling guide
  - [ ] Extending functionality
  - [ ] Adding new LLM providers
- [ ] Record **demo video** (5 minutes):
  - [ ] Deploy → Create bot → Train → Test → Embed
  - [ ] Upload to YouTube (unlisted)
- [ ] Create **landing page** (optional):
  - [ ] Simple site explaining features
  - [ ] Live demo
  - [ ] GitHub link
- [ ] GitHub release:
  - [ ] Tag v1.0.0
  - [ ] Release notes
  - [ ] Docker Hub image
- [ ] Launch posts:
  - [ ] Hacker News (Show HN: Open source AI chatbot widget)
  - [ ] Reddit (r/selfhosted, r/opensource)
  - [ ] Dev.to article
  - [ ] Tweet thread
  - [ ] Product Hunt (optional)

---

## 10. Success Metrics (Post-Launch)

### For Open Source Validation
**Within First Month:**
- 100+ GitHub stars
- 10+ actual deployments (tracked via GitHub issues/discussions)
- 5+ contributors (PRs accepted)
- 50+ downloads/pulls from Docker Hub

**Within First Quarter:**
- 500+ stars
- Featured on Awesome Lists (awesome-selfhosted, etc.)
- 20+ issues resolved
- 3+ forks with meaningful additions

### For SaaS Pivot Signal
**User Requests:**
- 3+ users asking "Can you host this for me?"
- 5+ feature requests for multi-tenancy
- Questions about specific vertical integrations (appointment booking, order tracking, etc.)

**Business Validation:**
- 2+ companies willing to pay for managed hosting
- 1+ inbound request from VC/accelerator

### Technical KPIs
**Performance:**
- Average response time < 2s (measured via logs)
- 95%+ uptime for demo deployment (track via UptimeRobot)
- Zero critical security issues (track via GitHub Security)

**Usage (Demo Site):**
- 1,000+ messages processed
- 50+ bots created (if public demo)
- Test coverage >80% (backend)

---

## 11. Out of Scope (For Later / SaaS)

**Explicitly NOT in OSS Version:**
- ❌ **Multi-tenancy** (1 deployment = 1 business only)
- ❌ **Stripe/payment integration**
- ❌ **Advanced analytics dashboard** (message trends, user satisfaction)
- ❌ **Team collaboration features** (multiple admin users, roles)
- ❌ **Webhook integrations** (Zapier, Slack notifications)
- ❌ **Custom model support** (Anthropic Claude, Google Gemini)
- ❌ **Auto-retraining** (scheduled scraping of URL changes)
- ❌ **A/B testing for responses**
- ❌ **GDPR compliance tooling** (automated data export, deletion workflows)
- ❌ **White-labeling** (remove branding, custom domains)
- ❌ **Email support** (built-in ticketing system)
- ❌ **Mobile apps** (iOS/Android native widgets)

**Why This Matters:**
- Keeps OSS version simple and maintainable
- Clear differentiation for commercial SaaS
- Prevents feature bloat before validation
- Forces focus on core value proposition

**Future OSS Additions (Community-Driven):**
- Plugin system for custom integrations
- Multiple LLM provider support (extensible architecture)
- Themes/templates for widget designs
- Import/export bots (JSON format)
- Analytics API (for custom dashboards)

---

## 12. Risk Mitigation

| Risk | Impact | Likelihood | Mitigation Strategy |
|------|--------|------------|---------------------|
| **OpenAI API costs spiral** | High | Medium | Hard message limits (1K/month default), usage dashboard, admin alerts at 80% |
| **Scraping fails on JS-heavy sites** | Medium | High | Offer "paste content" fallback, document limitations clearly, consider Playwright for v2 |
| **Widget breaks client sites** | High | Medium | Shadow DOM isolation, extensive browser testing, CSP-friendly code |
| **Database grows too large** | Medium | Low | SQLite VACUUM in cron, migration guide to Postgres, auto-archive old conversations |
| **Embedding quality issues** | Medium | Medium | Allow re-ingestion, test with 10+ diverse sites, expose similarity scores to admin |
| **ChromaDB corruption** | Medium | Low | Daily backups to `./backups/`, versioned backup retention (last 7 days) |
| **Security vulnerabilities** | High | Medium | Regular dependency updates, input sanitization, security audit before v1.0 |
| **Poor adoption (no stars)** | Medium | Medium | Launch on multiple platforms, create video demo, engage with r/selfhosted community |
| **Contributors abandon** | Low | Medium | Clear CONTRIBUTING.md, good first issues, recognize contributors in README |
| **OpenAI API changes** | Medium | Low | Abstract API calls behind interface, monitor OpenAI changelog, pin SDK versions |

**Monitoring Plan:**
- Set up GitHub Discussions for community support
- Weekly check: GitHub stars, issues, PRs
- Monthly review: Docker pulls, demo site usage
- Security: Enable Dependabot, CodeQL scanning

---

## 13. Documentation Requirements

### Must Have Before Launch

1. **README.md** (root)
   - Project description & value proposition
   - Screenshots (dashboard + widget)
   - Quick start guide (Docker)
   - Manual setup instructions
   - Configuration reference
   - Contributing link
   - License badge

2. **CONTRIBUTING.md**
   - Development setup (local)
   - Code style (Black for Python, Prettier for JS/TS)
   - Commit message conventions
   - PR process (template provided)
   - Issue reporting guidelines
   - Community Code of Conduct link

3. **docs/ARCHITECTURE.md**
   - High-level system diagram
   - Component overview (backend, frontend, widget)
   - Data flow (scraping → embedding → chat)
   - Tech stack decisions explained
   - Database schema visualization
   - ChromaDB integration details

4. **docs/API.md**
   - Full API reference (auto-generated from OpenAPI)
   - Authentication flows
   - Request/response examples (curl + JavaScript)
   - Error codes table
   - Rate limiting details
   - Webhook documentation (if applicable)

5. **docs/DEPLOYMENT.md**
   - Production deployment checklist
   - Nginx/Caddy configuration examples
   - SSL setup (Let's Encrypt)
   - Environment variables reference
   - Backup procedures
   - Monitoring setup (logs, health checks)
   - Scaling guide (when to migrate from SQLite)

6. **docs/CUSTOMIZATION.md**
   - Widget CSS customization (beyond UI settings)
   - Adding custom LLM providers
   - Extending with plugins
   - Modifying prompt templates
   - Theme development guide

7. **LICENSE** (MIT recommended)

8. **CODE_OF_CONDUCT.md** (Contributor Covenant)

### Nice to Have

- **docs/FAQ.md** (Common questions from users)
- **docs/CHANGELOG.md** (Version history)
- **docs/ROADMAP.md** (Future plans, not commits)
- **Video walkthrough** (YouTube, embedded in README)
- **Interactive demo site** (hosted publicly)

---

## Appendix A: Key Design Decisions

### Why ChromaDB over Pinecone?
- **Embedded mode = zero infrastructure:** No separate service to deploy, manage, or pay for
- **Open source alignment:** Self-hosters don't want SaaS dependencies
- **Sufficient for single-tenant:** Tested to 1M+ vectors, well beyond typical use case
- **Easy backups:** Just copy a folder, no API export needed
- **Migration path:** Can upgrade to Pinecone/Weaviate when scaling to SaaS

### Why OpenAI over Anthropic/Gemini?
- **Battle-tested documentation:** More examples, tutorials, community support
- **Cheaper embeddings:** $0.0001/1K tokens vs $0.00025/1K (Gemini)
- **Streaming support:** Mature SSE implementation for chat
- **Familiar to developers:** Lower barrier to contribution
- **Can swap later:** Abstraction layer makes it pluggable

### Why Message Limits?
- **Cost protection:** Prevents runaway costs for self-hosters
- **Quality over quantity:** Forces thoughtful use, not spam
- **SaaS upsell path:** Clear value prop for managed service
- **User expectations:** "1K messages/month" is concrete vs. "unlimited"

### Why No Built-in Analytics?
- **Complexity bloat:** Time-series DB, charting library, UI complexity
- **Different needs:** Some want Grafana, others want CSV export
- **Plugin opportunity:** Let community build analytics extensions
- **Focus on core:** Message count is enough for MVP validation

### Why Single-Tenant Architecture?
- **Simpler to build:** No tenant isolation, no billing, no user management
- **Easier to secure:** No cross-tenant data leak risks
- **Self-hosting friendly:** Small businesses want control
- **SaaS differentiation:** Multi-tenancy becomes commercial moat

### Why Shadow DOM for Widget?
- **CSS isolation:** Prevents client site styles from breaking widget
- **Professionalism:** Looks polished on any website
- **Reliability:** Works with Bootstrap, Tailwind, custom frameworks
- **Standard practice:** Used by Intercom, Drift, all major chat widgets

### Why Avatar Upload (Not URL)?
- **Reliability:** No broken external links
- **Performance:** Optimized, served locally
- **Privacy:** No external requests tracking users
- **Simplicity:** One upload vs. managing external assets

---

## Appendix B: Future Enhancements (Community Ideas)

**Plugin System:**
- Hook points for custom integrations
- Example: Appointment booking plugin for home services
- Example: Order tracking plugin for e-commerce

**Multi-Language Support:**
- Detect user language, respond accordingly
- Admin sets supported languages per bot
- Uses OpenAI's multilingual capabilities

**Voice Input/Output:**
- Web Speech API for voice questions
- Text-to-speech for answers
- Accessibility win

**Advanced Retrieval:**
- Hybrid search (keyword + semantic)
- Re-ranking algorithms
- Custom similarity thresholds per bot

**Conversation Insights:**
- Most asked questions
- Unanswered queries (for knowledge gaps)
- Average resolution time

**Mobile Widget:**
- React Native version for embedding in apps
- Same backend, different UI

**Enterprise Features (SaaS Only):**
- SSO (SAML, OAuth)
- Audit logs
- Custom data retention policies
- SLA guarantees

---

## Appendix C: Cost Estimate (Self-Hosting)

**One-Time Setup:**
- Domain name: $12/year
- SSL certificate: Free (Let's Encrypt)
- Time investment: 2-3 weeks (if building from scratch)

**Monthly Operating Costs:**
- VPS (2GB RAM): $10-20/month (DigitalOcean, Hetzner)
- OpenAI API:
  - Embeddings: ~$1 for 10 bots × 10K words each
  - Chat: ~$10 for 10 bots × 1K messages each
- Total: **~$25-35/month** for small business

**Scaling Costs (1,000 bots on SaaS):**
- VPS (8GB RAM): $40/month
- OpenAI API: ~$1,000/month (if all bots hit limits)
- Database: Migrate to managed Postgres ($20/month)
- CDN for widget.js: $5/month
- Total: **~$1,065/month** → Charge $10/bot = $10K MRR = 90% margin

---

**This PRD is production-ready.** All requirements are specified, edge cases considered, and success metrics defined. Ready to build! 🚀
