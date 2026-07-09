# Stage 1: Python dependency builder
FROM python:3.14-slim AS python-builder

RUN apt-get update && \
  apt-get install -y --no-install-recommends build-essential default-libmysqlclient-dev libcairo2-dev pkg-config && \
  rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY uv.lock pyproject.toml ./
# Using uv to install directly to system as you had it
RUN uv export --no-dev --no-emit-project > requirements.txt && \
    uv pip install --system --no-cache -r requirements.txt

# Stage 2: Node builder (Switching to slim to match Python base)
FROM node:24-slim AS node-builder
RUN corepack enable && corepack prepare yarn@stable --activate

WORKDIR /app
# Only copy files needed for install first
COPY package.json yarn.lock .yarnrc.yml ./
COPY .yarn ./.yarn
RUN yarn install --immutable

# Copy everything else and build
COPY . .
RUN yarn build

# Stage 3: Production image
FROM python:3.14-slim AS production

# System dependencies for MySQL, WeasyPrint and Cairo (svglib/pycairo)
RUN apt-get update && \
  apt-get install -y --no-install-recommends default-libmysqlclient-dev libcairo2 weasyprint && \
  rm -rf /var/lib/apt/lists/*

# 1. Copy Python libraries from builder
COPY --from=python-builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=python-builder /usr/local/bin /usr/local/bin

WORKDIR /app

# 2. Copy your source code FIRST
COPY . /app

# 3. Copy the built frontend assets LAST (This prevents them from being overwritten)
COPY --from=node-builder /app/vue/dist /app/vue/dist

# No CMD needed; Dokku uses your Procfile
