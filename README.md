# Chirp AI Chatbot 🤖

Open-source, self-hostable AI chatbot widget with RAG (Retrieval-Augmented Generation). Train your bot on your content and embed it on any website.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![Node](https://img.shields.io/badge/node-20-green.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)

---

## ✨ Features

- 🤖 **AI-Powered Chat**: Uses OpenAI GPT-4o-mini for intelligent, context-aware conversations
- 🔍 **RAG Support**: Retrieval-Augmented Generation with Qdrant vector database for accurate answers
- 📚 **Content Ingestion**: Train bots from website URLs or direct text input
- 🎨 **Fully Customizable**: Customize colors, position, avatar, and button text
- 🔐 **Secure**: Session-based admin authentication, API key management
- 📊 **Analytics**: Track message usage and bot performance
- 🚀 **Easy Deployment**: Docker-ready with one-command deployment
- 🌐 **Embeddable Widget**: Shadow DOM isolation, works on any website
- ⚡ **Real-time Streaming**: Server-Sent Events (SSE) for instant responses
- 📱 **Responsive**: Works perfectly on desktop and mobile devices

---

## 🚀 Quick Start

See **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** for full deployment guide.

### Docker (Recommended)

```bash
git clone https://github.com/yourusername/chirp-app.git
cd chirp-app
cp .env.production.example .env
# Edit .env with your API keys
docker-compose up -d
```

Access dashboard at http://localhost:8000

---

## 🏗️ System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        A1[Admin Dashboard<br/>React + TypeScript]
        A2[Website Visitor<br/>Any Website]
        A3[Chat Widget<br/>Shadow DOM]
    end

    subgraph "API Gateway"
        B1[FastAPI Server<br/>Python 3.12]
        B2[CORS Middleware]
        B3[Session Auth]
    end

    subgraph "Application Layer"
        C1[Auth Service<br/>bcrypt + Sessions]
        C2[Bot CRUD Service]
        C3[Content Ingestion<br/>Scraper + Chunking]
        C4[Chat Engine<br/>RAG Pipeline]
        C5[Avatar Service<br/>Image Processing]
    end

    subgraph "Data Layer"
        D1[(SQLite/PostgreSQL<br/>Bots, Conversations)]
        D2[(Qdrant Vector DB<br/>Embeddings)]
        D3[File Storage<br/>Avatars]
    end

    subgraph "External Services"
        E1[OpenAI API<br/>GPT-4o-mini]
        E2[OpenAI API<br/>text-embedding-3-small]
    end

    subgraph "Content Sources"
        F1[Website URLs<br/>Web Scraping]
        F2[Direct Text<br/>User Input]
    end

    %% Admin Dashboard Flow
    A1 -->|Login/Manage Bots| B1
    B1 --> B3
    B3 --> C1
    B3 --> C2

    %% Bot Creation & Training
    C2 --> D1
    F1 --> C3
    F2 --> C3
    C3 -->|Chunk Text| E2
    E2 -->|Embeddings| D2
    D2 -.->|Store| C3

    %% Widget Integration
    A2 -->|Load Widget| A3
    A3 -->|API Key Auth| B1

    %% Chat Flow
    A3 -->|User Message| B1
    B1 --> B2
    B2 --> C4
    C4 -->|Embed Query| E2
    C4 -->|Search Similar| D2
    D2 -->|Top 3 Chunks| C4
    C4 -->|Context + History| E1
    E1 -->|Stream Response| C4
    C4 -->|SSE Stream| A3
    C4 -->|Save| D1

    %% Avatar Management
    C2 --> C5
    C5 --> D3

    %% Styling
    classDef clientStyle fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef apiStyle fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef appStyle fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef dataStyle fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef externalStyle fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef sourceStyle fill:#fff9c4,stroke:#f57f17,stroke-width:2px

    class A1,A2,A3 clientStyle
    class B1,B2,B3 apiStyle
    class C1,C2,C3,C4,C5 appStyle
    class D1,D2,D3 dataStyle
    class E1,E2 externalStyle
    class F1,F2 sourceStyle
```

### Key Components

**Client Layer:**
- **Admin Dashboard**: React-based UI for managing bots, training, and configuration
- **Chat Widget**: Embeddable JavaScript widget with Shadow DOM isolation

**API Gateway:**
- **FastAPI**: High-performance async Python web framework
- **Authentication**: Session-based for admin, API key for widget
- **CORS**: Configured for cross-origin widget embedding

**Application Services:**
- **Content Ingestion**: Web scraping, text chunking (~500 tokens), embedding generation
- **Chat Engine**: RAG pipeline with vector similarity search and GPT-4o-mini
- **Bot Management**: CRUD operations, avatar uploads, API key generation

**Data Storage:**
- **Relational DB**: SQLite (dev) or PostgreSQL (prod) for structured data
- **Vector DB**: Qdrant for semantic search (1536-dim embeddings)
- **File Storage**: Local filesystem for avatar images

**External APIs:**
- **OpenAI GPT-4o-mini**: Conversational AI responses
- **OpenAI Embeddings**: text-embedding-3-small for vector generation

### Data Flow

1. **Bot Training**: Admin ingests content → Scraper fetches/processes → Text chunked → Embeddings generated → Stored in Qdrant
2. **Chat Request**: User message → Embedded → Vector search (top 3 chunks) → Context + history → GPT-4o-mini → Streamed response (SSE)
3. **Widget Load**: Fetch config via API key → Render with custom styling → Connect to chat endpoint

---

## 📖 Documentation

- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment
- **[API Docs](http://localhost:8000/docs)** - OpenAPI/Swagger
- **[Quick Start](docs/QUICK-START.md)** - Getting started
- **[Implementation Plan](docs/IMPLEMENTATION-PLAN.md)** - Development roadmap

---

## 📝 License

MIT License - see [LICENSE](LICENSE)

