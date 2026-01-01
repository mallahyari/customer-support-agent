# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Chirp is an open-source, self-hostable AI chatbot widget that enables businesses to add AI-powered customer support to their websites. The system creates a knowledge base from provided content (URL scraping or direct text input) and uses RAG (Retrieval-Augmented Generation) to answer visitor questions.

**Key Architecture:**
- **Backend:** FastAPI + SQLAlchemy (async) + SQLite
- **Vector Store:** Qdrant (local/embedded mode or server)
- **AI:** OpenAI API (embeddings: text-embedding-3-small, chat: gpt-4o-mini)
- **Frontend Dashboard:** React + Vite + TypeScript + Tailwind CSS + Shadcn/UI
- **Widget:** React compiled to single widget.js via Vite library mode
- **Auth:** Session-based (bcrypt passwords, session tokens)

## Development Commands

### Backend

The backend uses Python with uv for package management (configured in `pyproject.toml`).

```bash
# Navigate to backend directory
cd backend

# Install dependencies (using uv)
uv pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --port 8000

# Run with specific host
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Environment Setup:**
- Copy `.env` file with required API keys (see `backend/.env` for structure)
- Required: `OPENAI_API_KEY`, `GOOGLE_API_KEY`, admin credentials
- Database URL, ChromaDB path, and upload paths are configured via environment variables

### Frontend

The frontend is a React application using Vite and Tailwind CSS v4.

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server (default port 5173)
npm run dev

# Build for production
npm run build

# Type checking
tsc -b

# Lint
npm run lint

# Preview production build
npm run preview
```

**Important Frontend Details:**
- Uses `@` path alias pointing to `./src` (configured in vite.config.ts)
- Shadcn/UI components are in `src/components/ui/`
- Tailwind CSS v4 with `@tailwindcss/vite` plugin
- Component configuration in `components.json`

### Widget Build

The embeddable widget is built separately from the dashboard:

```bash
cd widget

# Install dependencies
npm install

# Build widget (outputs widget.js)
npm run build

# Development mode with hot reload
npm run dev
```

The widget uses Vite library mode to compile to a single `widget.js` file with Shadow DOM isolation.

## Project Structure

### Backend (`/backend`)

```
backend/
├── app/                 # Currently empty, backend code needs implementation
├── .env                 # Environment variables (NOT committed - contains API keys)
└── requirements.txt     # Python dependencies
```

**Key Backend Components (to be implemented per docs):**
- `main.py` - FastAPI app entry point
- `database.py` - SQLAlchemy setup (async SQLite)
- `models.py` - DB models (Bot, Conversation, Message, AdminSession)
- `schemas.py` - Pydantic models for validation
- `auth.py` - Authentication utilities
- `routes/` - API endpoints (auth, admin, public, chat)
- `services/` - Business logic (scraper, embeddings, chat_service)

### Frontend (`/frontend`)

```
frontend/
├── src/
│   ├── App.tsx              # Main app component
│   ├── main.tsx             # Entry point
│   ├── components/
│   │   ├── ui/              # Shadcn/UI components (Base UI + Radix)
│   │   ├── component-example.tsx
│   │   └── example.tsx
│   ├── lib/
│   │   └── utils.ts         # Utility functions (cn, etc.)
│   └── index.css            # Global styles + Tailwind
├── vite.config.ts           # Vite configuration
├── tsconfig.json            # TypeScript config
└── components.json          # Shadcn/UI configuration
```

**UI Component Library:**
- Uses Base UI (headless React components from MUI team)
- Styled with Tailwind CSS v4 and class-variance-authority
- Components: AlertDialog, Badge, Button, Card, Combobox, DropdownMenu, Field, Input, InputGroup, Label, Select, Separator, Textarea

### Documentation (`/docs`)

Comprehensive documentation exists in the `docs/` folder:
- `QUICK-START.md` - Tech stack, database schema, folder structure, implementation steps
- `API-SPEC.md` - Complete API endpoint specifications with examples
- `PRD-CORE.md` - Full product requirements document with architecture decisions

**Always reference these docs when:**
- Implementing new features
- Understanding expected API contracts
- Questions about database schema or architecture
- Understanding business rules and constraints

## Database Schema

**SQLite with SQLAlchemy (async):**

### Tables

**bots:**
- `id` (TEXT PK) - UUID
- `name`, `welcome_message`, `avatar_url`
- `accent_color` (default: #3B82F6)
- `position` (bottom-right|bottom-left|bottom-center)
- `show_button_text` (BOOLEAN), `button_text`
- `source_type` (url|text), `source_content`
- `api_key` (UUID, unique)
- `message_count`, `message_limit` (default: 1000)
- `created_at`, `updated_at`

**conversations:**
- `id` (TEXT PK), `bot_id` (FK)
- `session_id` - Browser fingerprint from widget
- `created_at`, `updated_at`

**messages:**
- `id` (TEXT PK), `conversation_id` (FK)
- `role` (user|assistant), `content`
- `created_at`

**admin_sessions:**
- `id` (TEXT PK) - Session token
- `username`, `token_hash` (SHA-256)
- `expires_at`, `created_at`

**Important Indexes:**
```sql
idx_conversations_bot_id, idx_conversations_session_id
idx_messages_conversation_id, idx_bots_api_key
```

## Key Technical Concepts

### Content Ingestion Pipeline

1. **Input:** URL scraping (max 10K words) or direct text paste
2. **Chunking:** ~500 tokens per chunk with 50-token overlap (sentence-aware)
3. **Embedding:** OpenAI text-embedding-3-small (1536 dimensions)
4. **Storage:** Qdrant with payload `{"bot_id": "...", "chunk_index": 0, "content": "..."}`

### Qdrant Vector Database

**Setup Options:**

1. **Local/Embedded Mode (Development):**
   ```python
   from qdrant_client import QdrantClient

   client = QdrantClient(path="./data/qdrant")
   ```
   - No separate server needed
   - Data stored in local directory
   - Perfect for development and single-instance deployments

2. **Server Mode (Production):**
   ```python
   client = QdrantClient(url="http://localhost:6333")
   # Or with authentication
   client = QdrantClient(
       url="http://localhost:6333",
       api_key="your-api-key"
   )
   ```
   - Better performance and scalability
   - Can be deployed with Docker: `docker run -p 6333:6333 qdrant/qdrant`
   - Supports Qdrant Cloud for managed hosting

**Collection Strategy:**

Option A - Single Collection (Recommended):
- Collection name: `chirp_embeddings`
- Use payload filtering: `{"bot_id": "..."}`
- More efficient for multi-bot queries
- Easier backup and management

Option B - Collection per Bot:
- Collection name: `bot_{bot_id}`
- No need for filtering
- Simpler isolation but more collections to manage

**Vector Configuration:**
- Dimension: 1536 (OpenAI text-embedding-3-small)
- Distance: Cosine similarity
- Payload schema:
  ```python
  {
      "bot_id": "uuid-string",
      "chunk_index": 0,
      "content": "text content of chunk",
      "source": "url or text",
      "metadata": {}  # Additional custom fields
  }
  ```

### Chat Logic (RAG Pattern)

1. Authenticate via `api_key` matching `bots.api_key`
2. Check rate limits (bot-level: message_count < message_limit, session: 10 msg/min)
3. Embed user question with OpenAI
4. Retrieve top 3 chunks from Qdrant (similarity > 0.7, filtered by bot_id)
5. Build prompt with context + last 10 messages
6. Stream response from OpenAI gpt-4o-mini via SSE
7. Save conversation to DB, increment message_count

**Prompt Template:**
```
You are a helpful customer support assistant for {bot_name}.

Context from knowledge base:
{retrieved_chunks}

Conversation history:
{last_10_messages}

User question: {current_message}

Instructions:
- Answer using ONLY the context provided
- Be helpful, concise, and friendly
- If answer not in context: "I don't have that information in my knowledge base..."
- Do not make up information
```

### Widget Architecture

- **Shadow DOM:** Isolates styles from client site CSS
- **Customization:** Applies accent_color, avatar, position, button_text dynamically
- **Persistence:** localStorage for session_id and message history
- **API Calls:**
  - `GET /api/public/config/{bot_id}` on load
  - `POST /api/chat` for messages (SSE streaming)

## API Endpoints

### Authentication
- `POST /api/auth/login` - Admin login (returns session cookie)
- `POST /api/auth/logout` - Clear session

### Admin Routes (Session Required)
- `GET /api/admin/bots` - List all bots
- `POST /api/admin/bots` - Create bot
- `GET /api/admin/bots/{id}` - Get bot details
- `PUT /api/admin/bots/{id}` - Update bot
- `DELETE /api/admin/bots/{id}` - Delete bot (cascade to Qdrant collection)
- `POST /api/admin/bots/{id}/ingest` - Train/retrain bot
- `POST /api/admin/bots/{id}/avatar` - Upload avatar (max 500KB, resize to 64x64)
- `DELETE /api/admin/bots/{id}/avatar` - Remove avatar
- `POST /api/admin/bots/{id}/regenerate-key` - New API key

### Public Routes (API Key Required)
- `GET /api/public/config/{bot_id}?api_key=...` - Widget configuration
- `POST /api/chat` - Main chat endpoint (SSE stream)
- `GET /api/public/avatar/{bot_id}` - Serve avatar image

**CORS Configuration:**
- Admin routes: Credentials allowed, restricted origins
- Public/chat routes: `*` origins (widget works on any domain)

## Important Business Rules

### Rate Limiting
- Admin routes: 100 req/min per IP
- Chat endpoint: 10 msg/min per session_id
- Bot-level: Check message_count < message_limit before processing

### File Uploads (Avatars)
- Formats: .png, .jpg, .jpeg, .gif
- Max size: 500KB
- Processing: Resize to 64x64px (center crop)
- Storage: `./data/uploads/avatars/{bot_id}_{timestamp}.png`
- Security: Validate actual image (magic numbers), sanitize filename

### Content Constraints
- Max scrape: 10,000 words per URL
- Chunk size: ~500 tokens with 50-token overlap
- Context window: Last 10 messages
- Retrieval: Top 3 chunks with similarity > 0.7

## Testing Workflow

After implementing features, test in this order:

1. **Backend API:**
   ```bash
   # Login
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"password"}' \
     -c cookies.txt

   # Create bot
   curl -X POST http://localhost:8000/api/admin/bots \
     -H "Content-Type: application/json" -b cookies.txt \
     -d '{"name":"Test","source_type":"text","source_content":"..."}'
   ```

2. **Frontend Dashboard:** Verify login, bot CRUD, live preview

3. **Widget Integration:** Test on sample HTML with various CSS frameworks

## Common Gotchas

1. **Qdrant:** Use local mode `QdrantClient(path="./data/qdrant")` for development, or server mode `QdrantClient(url="http://localhost:6333")` for production
2. **SQLite async:** Connection string must be `sqlite+aiosqlite:///...`
3. **SSE Streaming:** Headers must include `'Content-Type': 'text/event-stream'`, `'Cache-Control': 'no-cache'`
4. **Widget CORS:** `/api/chat` needs `Access-Control-Allow-Origin: *`
5. **File uploads:** Use FastAPI's `UploadFile`, validate with magic numbers not extensions
6. **Session security:** Always hash tokens (SHA-256) before DB storage
7. **Qdrant collections:** Create collection per bot or use single collection with payload filtering on `bot_id`

## Security Checklist

- [ ] API keys: UUIDs hashed with SHA-256
- [ ] Admin passwords: bcrypt (cost factor 12)
- [ ] Session tokens: 32-byte random, hashed storage
- [ ] File uploads: Magic number validation, filename sanitization
- [ ] Input validation: Sanitize all user inputs (XSS prevention)
- [ ] SQL injection: Use parameterized queries (SQLAlchemy ORM)
- [ ] URL validation: Prevent SSRF when scraping

## Component Development Guidelines

### Adding Shadcn/UI Components

```bash
# The project uses a custom configuration (components.json)
# Add components via shadcn CLI or manually to src/components/ui/
```

**Component Style:**
- Use Base UI headless components as foundation
- Style with Tailwind CSS v4 and CVA (class-variance-authority)
- Export named components with proper TypeScript types
- Use `cn()` utility from `@/lib/utils` for conditional classes

### Frontend Patterns

- **State Management:** React hooks (useState, useEffect)
- **API Calls:** Fetch/Axios with proper error handling
- **Forms:** Controlled components with validation
- **Styling:** Tailwind utility classes, avoid inline styles
- **Icons:** `@tabler/icons-react` package

## Data Persistence

### Local Development
- SQLite: `./data/chatbots.db`
- Qdrant: `./data/qdrant/` (local mode) or connect to server at `localhost:6333`
- Avatars: `./data/uploads/avatars/`

### Backup Strategy
- Database: Copy SQLite file
- Vector DB:
  - Local mode: Copy Qdrant data folder
  - Server mode: Use Qdrant's snapshot API
- Uploads: Copy avatars folder
- Export: Create `.tar.gz` with timestamp

## Environment Variables Reference

**Required:**
- `OPENAI_API_KEY` - For embeddings and chat
- `ADMIN_USERNAME`, `ADMIN_PASSWORD` - First-time setup
- `SECRET_KEY` - For session token generation
- `CLERK_SECRET_KEY`, `CLERK_WEBHOOK_SECRET` - Auth integration
- `STRIPE_*` - Payment integration keys

**Optional with Defaults:**
- `DATABASE_URL` - Default: `sqlite+aiosqlite:///./data/chatbots.db`
- `QDRANT_PATH` - Default: `./data/qdrant` (local mode)
- `QDRANT_URL` - Optional: `http://localhost:6333` (server mode, overrides QDRANT_PATH)
- `QDRANT_API_KEY` - Optional: For Qdrant Cloud or secured instances
- `UPLOAD_PATH` - Default: `./data/uploads`
- `MESSAGE_LIMIT_DEFAULT` - Default: 1000
- `MAX_SCRAPE_WORDS` - Default: 10000
- `LOG_LEVEL` - Default: INFO

## Implementation Status

**Current State:** Early development phase
- Frontend: Basic React + Vite setup with Shadcn/UI components
- Backend: Directory structure exists but implementation pending
- Widget: Not yet implemented

**Next Steps (per PRD-CORE.md):**
1. Backend foundation (FastAPI app, SQLAlchemy models, health check)
2. Authentication system (password hashing, login endpoint, session middleware)
3. Bot CRUD endpoints
4. Qdrant integration (local or server mode)
5. Ingestion pipeline (scraper, chunking, embeddings)
6. Chat engine with SSE streaming
7. Frontend dashboard pages
8. Widget development
9. Docker deployment setup

Refer to `docs/QUICK-START.md` Section "First Steps (Order of Implementation)" for detailed breakdown.
