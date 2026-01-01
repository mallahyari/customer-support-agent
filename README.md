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

## 📖 Documentation

- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment
- **[API Docs](http://localhost:8000/docs)** - OpenAPI/Swagger
- **[Quick Start](docs/QUICK-START.md)** - Getting started
- **[Implementation Plan](docs/IMPLEMENTATION-PLAN.md)** - Development roadmap

---

## 📝 License

MIT License - see [LICENSE](LICENSE)

