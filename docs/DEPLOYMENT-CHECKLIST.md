# Deployment Checklist

This checklist helps you verify that all deployment components are correctly set up.

## Pre-Deployment Verification

### 1. Environment Configuration

- [ ] `.env` file created (copied from `.env.production.example`)
- [ ] `OPENAI_API_KEY` set with valid API key
- [ ] `ADMIN_PASSWORD` changed from default (minimum 12 characters)
- [ ] `SECRET_KEY` generated (minimum 32 characters)
  ```bash
  # Generate secure SECRET_KEY
  openssl rand -hex 32
  ```

### 2. Docker Files

- [ ] `Dockerfile` exists and is readable
- [ ] `docker-compose.yml` exists and is readable
- [ ] `.dockerignore` exists to optimize builds

### 3. Required Directories

- [ ] `data/` directory will be created automatically
- [ ] `data/uploads/avatars/` for bot avatars
- [ ] `data/qdrant/` for vector database (local mode)
- [ ] `data/chatbots.db` for SQLite database

## Build & Test

### 1. Docker Build

```bash
# Build the Docker image
docker-compose build

# Expected: Build completes without errors
```

**Verify:**
- [ ] Frontend build stage completes successfully
- [ ] Widget build stage completes successfully
- [ ] Python dependencies install successfully
- [ ] Final image is created

### 2. Start Application

```bash
# Start in detached mode
docker-compose up -d

# Expected: Container starts and passes health check
```

**Verify:**
- [ ] Container `chirp-app` is running
  ```bash
  docker-compose ps
  ```
- [ ] Health check passes after ~40 seconds
  ```bash
  docker-compose logs app | grep "Application startup complete"
  ```

### 3. Test Endpoints

```bash
# Health check
curl http://localhost:8000/api/health

# Expected: {"status":"healthy",...}
```

**Verify:**
- [ ] Health endpoint returns 200 OK
- [ ] Database component is healthy
- [ ] Qdrant component is healthy

```bash
# Root endpoint
curl http://localhost:8000/

# Expected: {"message":"Chirp AI Chatbot API",...}
```

```bash
# API documentation
curl -I http://localhost:8000/docs

# Expected: 200 OK with HTML content
```

### 4. Test Authentication

```bash
# Login with admin credentials
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your-admin-password"}' \
  -c cookies.txt

# Expected: {"message":"Login successful"}
```

**Verify:**
- [ ] Login returns 200 OK
- [ ] Session cookie is set
- [ ] Can access admin endpoints with cookie

### 5. Create Test Bot

```bash
# Create a bot
curl -X POST http://localhost:8000/api/admin/bots \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name":"Test Bot",
    "welcome_message":"Hello! How can I help?",
    "accent_color":"#3B82F6",
    "position":"bottom-right",
    "show_button_text":true,
    "button_text":"Chat with us",
    "message_limit":1000,
    "source_type":"text",
    "source_content":"This is a test bot for customer support."
  }'

# Expected: Returns bot object with ID and API key
```

**Verify:**
- [ ] Bot creation succeeds
- [ ] Bot ID is a valid UUID
- [ ] API key is generated
- [ ] Bot appears in database

### 6. Train Bot

```bash
# Get bot ID from previous response
BOT_ID="your-bot-id-here"

# Train the bot
curl -X POST http://localhost:8000/api/admin/bots/$BOT_ID/ingest \
  -b cookies.txt

# Expected: {"message":"Successfully ingested content..."}
```

**Verify:**
- [ ] Training completes successfully
- [ ] Embeddings are created in Qdrant
- [ ] No errors in logs

## Production Deployment

### 1. Server Setup

- [ ] Server meets minimum requirements (1GB RAM, 10GB storage)
- [ ] Docker and Docker Compose installed
- [ ] Domain name configured (A record pointing to server)
- [ ] Firewall configured (allow ports 80, 443, 22)

### 2. SSL/HTTPS

- [ ] Nginx installed and configured
- [ ] SSL certificate obtained (Let's Encrypt recommended)
- [ ] Certificate auto-renewal configured
- [ ] HTTPS redirect configured (HTTP → HTTPS)

### 3. Reverse Proxy

- [ ] Nginx configuration created (`/etc/nginx/sites-available/chirp`)
- [ ] Site enabled (`/etc/nginx/sites-enabled/chirp`)
- [ ] Proxy headers configured correctly
- [ ] SSE timeout configured (300s+ for streaming)
- [ ] Nginx configuration tested (`nginx -t`)

### 4. Security

- [ ] Admin password is strong (16+ characters)
- [ ] SECRET_KEY is unique (32+ random characters)
- [ ] Firewall enabled (ufw/iptables)
- [ ] Only necessary ports exposed (80, 443, 22)
- [ ] SSH key authentication configured
- [ ] Security headers configured in Nginx
- [ ] CORS origins restricted if needed

### 5. Monitoring

- [ ] Health check endpoint accessible
- [ ] Log monitoring configured
  ```bash
  docker-compose logs -f app
  ```
- [ ] Disk space monitoring
- [ ] Resource usage monitoring
  ```bash
  docker stats chirp-app
  ```

### 6. Backup

- [ ] Backup script created and tested
- [ ] Automated backups scheduled (cron)
- [ ] Backup retention policy configured (7+ days)
- [ ] Restore procedure tested

**Files to backup:**
- `data/chatbots.db` - SQLite database
- `data/qdrant/` - Vector embeddings
- `data/uploads/` - Avatar images
- `.env` - Environment configuration

## Post-Deployment

### 1. Access Verification

- [ ] Dashboard accessible at `https://yourdomain.com`
- [ ] Login works with admin credentials
- [ ] Bot creation and management works
- [ ] Widget embed code can be copied

### 2. Widget Testing

- [ ] Create test HTML page with widget
- [ ] Widget loads without console errors
- [ ] Chat functionality works
- [ ] Messages are saved to database
- [ ] RAG retrieval works (relevant answers)

### 3. Performance

- [ ] API response time < 500ms (non-streaming)
- [ ] Chat streaming works smoothly
- [ ] No memory leaks after prolonged use
- [ ] Database queries are efficient

### 4. Documentation

- [ ] Deployment documented (this checklist)
- [ ] Access credentials stored securely
- [ ] Backup procedures documented
- [ ] Troubleshooting guide available

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs app

# Common issues:
# - Missing OPENAI_API_KEY
# - Port 8000 already in use
# - Permission issues with data directory
```

### Database errors

```bash
# Check database file
ls -la data/chatbots.db

# Verify permissions
chmod 644 data/chatbots.db
```

### Qdrant errors

```bash
# Check Qdrant directory
ls -la data/qdrant/

# Verify permissions
chmod -R 755 data/qdrant/
```

### Health check failing

```bash
# Check health endpoint
curl http://localhost:8000/api/health

# Check container health
docker inspect chirp-app | grep -A 10 Health
```

## Rollback Procedure

If deployment fails:

```bash
# Stop containers
docker-compose down

# Restore from backup
cp backups/chatbots_TIMESTAMP.db data/chatbots.db
tar -xzf backups/qdrant_TIMESTAMP.tar.gz -C data/

# Start with previous version
git checkout previous-tag
docker-compose up -d
```

## Support

If you encounter issues not covered here:

1. Check [docs/DEPLOYMENT.md](./DEPLOYMENT.md) for detailed instructions
2. Review application logs: `docker-compose logs -f app`
3. Check GitHub issues: https://github.com/yourusername/chirp-app/issues
4. Join discussions: https://github.com/yourusername/chirp-app/discussions

---

**Last Updated:** January 1, 2026
**Version:** 1.0.0
