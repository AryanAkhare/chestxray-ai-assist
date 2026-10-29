# Stage 1: Build Frontend Single Page Application
FROM node:20-alpine AS frontend-builder
WORKDIR /build

COPY frontend/package*.json ./
RUN npm ci || npm install

COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python Runtime
FROM python:3.11-slim
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000 \
    APP_DATA_DIR=/app/data

# Install curl for healthcheck & dos2unix to ensure line endings are valid
RUN apt-get update && apt-get install -y --no-install-recommends curl dos2unix && rm -rf /var/lib/apt/lists/*

# Install Python backend dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend code, conversion scripts, and model outputs
COPY backend /app/backend
COPY scripts /app/scripts
COPY output_baseline /app/output_baseline
COPY output_gan /app/output_gan

# Copy data directory (containing converted safetensors weights)
COPY data /app/data

# Copy built frontend assets from Stage 1
COPY --from=frontend-builder /build/dist /app/frontend/dist

# Copy entrypoint script and normalize line endings
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN dos2unix /app/docker-entrypoint.sh && chmod +x /app/docker-entrypoint.sh

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
