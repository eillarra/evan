FROM node:22-alpine AS develop-stage
WORKDIR /app
COPY package*.json ./
RUN yarn global add vite
COPY . .

FROM develop-stage AS build-stage
RUN yarn
RUN yarn build

FROM python:3.12-slim-bullseye AS production-stage

EXPOSE 5000

RUN apt-get update && \
  apt-get install -y build-essential default-libmysqlclient-dev pkg-config weasyprint && \
  rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir poetry

WORKDIR /app
COPY poetry.lock pyproject.toml /app/
RUN poetry config virtualenvs.create false && \
  poetry install --no-root --no-interaction --no-ansi --without dev && \
  rm -rf $(poetry config cache-dir)

COPY . /app
COPY --from=build-stage /app/vue/dist /app/vue/dist
