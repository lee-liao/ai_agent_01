# Backend Dockerfile for Child Growth Assistant
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy config and rag from parent context
COPY config ./config
COPY rag ./rag

# Copy backend files
COPY backend/requirements.txt ./backend/
WORKDIR /app/backend

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ .

# Back to app root for paths
WORKDIR /app

# Expose port
EXPOSE 8011

# Health check
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8011/healthz || exit 1

# Run application
WORKDIR /app/backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8011"]

