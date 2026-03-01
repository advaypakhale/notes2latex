# Stage 1: Build frontend
FROM node:22-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Backend + serve
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-base texlive-latex-recommended texlive-latex-extra \
    texlive-fonts-recommended texlive-science texlive-pictures \
    latexmk && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/ src/
RUN uv sync --frozen --no-dev
COPY --from=frontend /app/frontend/dist frontend/dist

EXPOSE 8000
CMD ["uv", "run", "notes2latex", "serve"]
