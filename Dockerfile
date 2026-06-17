# ============================================
# Stage 1: Frontend Builder
# ============================================
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# Install pnpm
RUN npm install -g pnpm

# Copy package.json and lockfile
COPY frontend/package.json frontend/pnpm-lock.yaml ./

# Install frontend dependencies
RUN pnpm install --frozen-lockfile

# Copy frontend source files
COPY frontend/ .

# Copy empty dummy directory or files if referenced relatively
RUN mkdir -p ../backend/app/public

# Build frontend (output goes to ../backend/app/public, which translates to /backend/app/public)
RUN pnpm build

# ============================================
# Stage 2: Backend Builder
# ============================================
FROM python:3.9-slim AS backend-builder

WORKDIR /build

RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================
# Stage 3: Runtime
# ============================================
FROM python:3.9-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libmariadb3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy python packages from backend-builder
COPY --from=backend-builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH

# Copy backend code
COPY backend/app/ ./app/
COPY backend/.env.example .env

# Copy frontend build output from stage 1 into app/public
COPY --from=frontend-builder /backend/app/public/ ./app/public/

# Create necessary directories
RUN mkdir -p app/public/uploads app/data logs

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/ping || exit 1

# Start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
