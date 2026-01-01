# Multi-stage Dockerfile for Chirp AI Chatbot
# Stage 1: Build frontend and widget
# Stage 2: Build Python backend
# Stage 3: Production runtime

# =============================================================================
# Stage 1: Build Frontend Assets
# =============================================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Copy package files for both frontend and widget
COPY frontend/package*.json ./frontend/
COPY frontend/widget/package*.json ./frontend/widget/

# Install dependencies
RUN cd frontend && npm ci
RUN cd frontend/widget && npm ci

# Copy source files
COPY frontend/ ./frontend/

# Build frontend dashboard
RUN cd frontend && npm run build

# Build embeddable widget
RUN cd frontend/widget && npm run build

# =============================================================================
# Stage 2: Python Dependencies
# =============================================================================
FROM python:3.12-slim AS python-builder

WORKDIR /app

# Install system dependencies for Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# =============================================================================
# Stage 3: Production Runtime
# =============================================================================
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=python-builder /root/.local /root/.local

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend assets
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist
COPY --from=frontend-builder /app/frontend/widget/dist ./frontend/widget/dist

# Create data directory for runtime files
RUN mkdir -p /app/data/uploads/avatars /app/data/qdrant

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PATH=/root/.local/bin:$PATH \
    PYTHONPATH=/app/backend

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Switch to backend directory
WORKDIR /app/backend

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
