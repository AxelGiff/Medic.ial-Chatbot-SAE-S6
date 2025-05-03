FROM node:20-alpine AS builder
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Copy only package files first to leverage caching
COPY frontend/package*.json frontend/yarn*.lock ./
RUN \
    if [ -f yarn.lock ]; then yarn --frozen-lockfile; \
    elif [ -f package-lock.json ]; then npm ci; \
    elif [ -f pnpm-lock.yaml ]; then yarn global add pnpm && pnpm i --frozen-lockfile; \
    else echo "Lockfile not found." && exit 1; \
    fi

# Copy frontend source files after dependencies are installed
COPY frontend/ .
RUN npm install --save @huggingface/inference

RUN npm run build

FROM python:3.10-slim AS backend
WORKDIR /app

# Simplify apt-get command to essential packages
RUN apt-get update && apt-get install --no-install-recommends -y \
    git ffmpeg curl gnupg \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 user

# Copy only requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Copy built frontend from builder stage
COPY --from=builder /app/build ./static

# Copy backend files last
COPY . .    

CMD ["python", "app.py"]