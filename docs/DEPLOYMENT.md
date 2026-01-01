# Deployment Guide

Complete guide for deploying Chirp AI Chatbot to production environments.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start with Docker](#quick-start-with-docker)
- [Production Deployment](#production-deployment)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [Reverse Proxy Setup](#reverse-proxy-setup)
- [SSL/HTTPS Configuration](#sslhttps-configuration)
- [Monitoring & Logging](#monitoring--logging)
- [Backup & Recovery](#backup--recovery)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required

- Docker 20.10+ and Docker Compose 2.0+
- OpenAI API key
- Domain name (for production)
- At least 1GB RAM, 10GB storage

### Recommended

- 2GB+ RAM for production
- SSL certificate (Let's Encrypt recommended)
- Separate Qdrant server for scale
- PostgreSQL for production database

---

## Quick Start with Docker

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/chirp-app.git
cd chirp-app
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.production.example .env

# Edit with your values
nano .env
```

**Minimum required:**
```env
OPENAI_API_KEY=sk-your-key-here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password
SECRET_KEY=your-secret-key-min-32-chars
```

### 3. Build and Run

```bash
# Build Docker image
docker-compose build

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f app
```

### 4. Access Application

- Dashboard: http://localhost:8000
- API Health: http://localhost:8000/api/health
- Login with credentials from `.env`

---

## Production Deployment

### Option 1: Docker Compose (Recommended for single server)

#### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin

# Create application directory
sudo mkdir -p /opt/chirp
cd /opt/chirp
```

#### 2. Deploy Application

```bash
# Clone repository
git clone https://github.com/yourusername/chirp-app.git .

# Configure environment
cp .env.production.example .env
nano .env

# Set production values
# - Strong passwords
# - Production SECRET_KEY
# - Valid OpenAI API key

# Build and start
docker-compose up -d

# Verify deployment
docker-compose ps
docker-compose logs app
```

#### 3. Configure Reverse Proxy (Nginx)

```bash
# Install Nginx
sudo apt install nginx

# Create configuration
sudo nano /etc/nginx/sites-available/chirp
```

**Nginx configuration:**
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL certificates (use certbot for Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy to application
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeout for SSE streaming
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Widget static files (if serving from same domain)
    location /widget {
        alias /opt/chirp/frontend/widget/dist;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/chirp /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

#### 4. SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal is configured automatically
# Test renewal
sudo certbot renew --dry-run
```

### Option 2: With Separate Qdrant Server

For better performance and scalability:

**docker-compose.yml:**
```yaml
services:
  app:
    # ... existing config ...
    environment:
      - QDRANT_URL=http://qdrant:6333
      # Remove QDRANT_PATH

  qdrant:
    image: qdrant/qdrant:latest
    container_name: chirp-qdrant
    ports:
      - "6333:6333"
    volumes:
      - qdrant-storage:/qdrant/storage
    restart: unless-stopped

volumes:
  qdrant-storage:
```

### Option 3: Kubernetes Deployment

See [docs/KUBERNETES.md](./KUBERNETES.md) for Kubernetes deployment guide.

---

## Environment Variables

### Critical Security Settings

```env
# Generate strong secret key
SECRET_KEY=$(openssl rand -hex 32)

# Use strong admin password
ADMIN_PASSWORD=$(openssl rand -base64 32)
```

### Database Options

**SQLite (Development/Small deployments):**
```env
DATABASE_URL=sqlite+aiosqlite:///./data/chatbots.db
```

**PostgreSQL (Production recommended):**
```env
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/chirp
```

### Qdrant Configuration

**Local mode (embedded):**
```env
QDRANT_PATH=./data/qdrant
```

**Server mode:**
```env
QDRANT_URL=http://qdrant-server:6333
QDRANT_API_KEY=your-api-key  # If using Qdrant Cloud
```

---

## Database Setup

### PostgreSQL (Recommended for Production)

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql

CREATE DATABASE chirp;
CREATE USER chirp_user WITH ENCRYPTED PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE chirp TO chirp_user;
\q

# Update .env
DATABASE_URL=postgresql+asyncpg://chirp_user:your-password@localhost:5432/chirp
```

### Database Migrations

Application automatically creates tables on startup. For manual migrations:

```bash
# Inside container
docker-compose exec app python -c "
from app.database import init_db
import asyncio
asyncio.run(init_db())
"
```

---

## Monitoring & Logging

### Application Logs

```bash
# View logs
docker-compose logs -f app

# Logs with timestamps
docker-compose logs -f --timestamps app

# Last 100 lines
docker-compose logs --tail=100 app
```

### Health Checks

```bash
# Check application health
curl http://localhost:8000/api/health

# Expected response:
# {"status":"healthy","database":"connected","qdrant":"connected"}
```

### Log Levels

Configure in `.env`:
```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### External Monitoring (Optional)

**Sentry for error tracking:**
```env
SENTRY_DSN=your-sentry-dsn
```

---

## Backup & Recovery

### Automated Backup Script

Create `/opt/chirp/backup.sh`:

```bash
#!/bin/bash

# Backup directory
BACKUP_DIR="/opt/chirp/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup SQLite database
cp /opt/chirp/data/chatbots.db "$BACKUP_DIR/chatbots_$TIMESTAMP.db"

# Backup Qdrant data
tar -czf "$BACKUP_DIR/qdrant_$TIMESTAMP.tar.gz" -C /opt/chirp/data qdrant/

# Backup avatars
tar -czf "$BACKUP_DIR/uploads_$TIMESTAMP.tar.gz" -C /opt/chirp/data uploads/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $TIMESTAMP"
```

```bash
# Make executable
chmod +x /opt/chirp/backup.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
0 2 * * * /opt/chirp/backup.sh >> /var/log/chirp-backup.log 2>&1
```

### Restore from Backup

```bash
# Stop application
docker-compose down

# Restore database
cp /opt/chirp/backups/chatbots_TIMESTAMP.db /opt/chirp/data/chatbots.db

# Restore Qdrant
tar -xzf /opt/chirp/backups/qdrant_TIMESTAMP.tar.gz -C /opt/chirp/data/

# Restore avatars
tar -xzf /opt/chirp/backups/uploads_TIMESTAMP.tar.gz -C /opt/chirp/data/

# Start application
docker-compose up -d
```

---

## Troubleshooting

### Application Won't Start

```bash
# Check logs
docker-compose logs app

# Common issues:
# 1. Missing OPENAI_API_KEY
# 2. Port 8000 already in use
# 3. Permission issues with data directory

# Fix permissions
sudo chown -R 1000:1000 /opt/chirp/data
```

### Database Connection Issues

```bash
# Check database file exists
ls -la /opt/chirp/data/chatbots.db

# Check PostgreSQL connection
docker-compose exec app python -c "
from app.database import engine
import asyncio

async def test():
    async with engine.begin() as conn:
        print('Database connected!')

asyncio.run(test())
"
```

### Qdrant Issues

```bash
# Check Qdrant health
curl http://localhost:6333/health

# Check collection exists
curl http://localhost:6333/collections/chirp_embeddings
```

### Widget Not Loading

```bash
# Check widget build
ls -la /opt/chirp/frontend/widget/dist/widget.js

# Check CORS headers
curl -I http://localhost:8000/api/public/config/BOT_ID?api_key=KEY

# Should include:
# Access-Control-Allow-Origin: *
```

### High Memory Usage

```bash
# Check container resources
docker stats chirp-app

# Limit memory in docker-compose.yml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 1G
```

### SSL Certificate Issues

```bash
# Renew certificate manually
sudo certbot renew --force-renewal

# Check certificate expiry
sudo certbot certificates

# Test SSL configuration
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com
```

---

## Security Checklist

- [ ] Changed default admin password
- [ ] Generated unique SECRET_KEY
- [ ] Configured firewall (UFW/iptables)
- [ ] Enabled SSL/HTTPS
- [ ] Configured security headers in Nginx
- [ ] Limited Docker container permissions
- [ ] Set up automated backups
- [ ] Configured log rotation
- [ ] Disabled unnecessary ports
- [ ] Set up monitoring/alerting

---

## Production Best Practices

1. **Use PostgreSQL** instead of SQLite for production
2. **Separate Qdrant** server for better performance
3. **Enable HTTPS** with valid SSL certificate
4. **Regular backups** (daily recommended)
5. **Monitor logs** for errors and security issues
6. **Update regularly** to latest version
7. **Rate limiting** at reverse proxy level
8. **CDN** for widget.js delivery
9. **Database connection pooling**
10. **Horizontal scaling** with load balancer

---

## Updating Application

```bash
# Pull latest changes
cd /opt/chirp
git pull origin main

# Rebuild Docker image
docker-compose build --no-cache

# Stop old container
docker-compose down

# Start new container
docker-compose up -d

# Check logs
docker-compose logs -f app
```

---

## Support

- **Documentation:** [docs/](../docs/)
- **Issues:** https://github.com/yourusername/chirp-app/issues
- **Discussions:** https://github.com/yourusername/chirp-app/discussions
