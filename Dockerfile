FROM ghcr.io/astral-sh/uv:0.10 AS uv

# Stage 1: Build frontend
FROM node:22-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Backend + serve
FROM python:3.12-slim

LABEL org.opencontainers.image.title="notes2latex" \
      org.opencontainers.image.description="Convert handwritten math notes to compiled LaTeX using vision LLMs" \
      org.opencontainers.image.source="https://github.com/advaypakhale/notes2latex" \
      org.opencontainers.image.url="https://github.com/advaypakhale/notes2latex" \
      org.opencontainers.image.licenses="MIT"

# The default preamble pulls from latex-extra, science and pictures, and users
# can add arbitrary packages to their preamble in Settings. Trimming this set
# breaks documents that compiled before.
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-base texlive-latex-recommended texlive-latex-extra \
    texlive-fonts-recommended texlive-science texlive-pictures \
    latexmk && rm -rf /var/lib/apt/lists/*

# Pre-creating data/ and output/ seeds the ownership of any volume mounted over
# them. app must own /app here: a chown after the venv exists would duplicate
# every one of its files into a second layer.
RUN useradd --create-home --uid 1000 app \
    && install -d -o app -g app /app /app/data /app/output

WORKDIR /app
USER app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1

COPY --chown=app:app pyproject.toml uv.lock README.md ./
RUN --mount=from=uv,source=/uv,target=/usr/local/bin/uv \
    --mount=type=cache,target=/home/app/.cache/uv,uid=1000,gid=1000 \
    uv sync --locked --no-install-project --no-editable

COPY --chown=app:app src/ src/
RUN --mount=from=uv,source=/uv,target=/usr/local/bin/uv \
    --mount=type=cache,target=/home/app/.cache/uv,uid=1000,gid=1000 \
    uv sync --locked --no-editable

COPY --from=frontend --chown=app:app /app/frontend/dist frontend/dist

# User preambles reach TeX verbatim, and \input/\openin can read any file the
# process can. "p" confines them to the job directory; texmf.cnf ships "a".
ENV openin_any=p \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

COPY --chmod=755 <<'EOF' /usr/local/bin/entrypoint.sh
#!/bin/sh
# A volume created by an image running as root stays root-owned, and SQLite
# surfaces that only as a readonly-database error from deep inside the app.
data_dir="${NOTES2LATEX_DATA_DIR:-/app/data}"
probe="$data_dir/.write-check"

if ! (mkdir -p "$data_dir" && touch "$probe") 2>/dev/null; then
    cat >&2 <<MSG
notes2latex: $data_dir is not writable by uid $(id -u).

Give the volume to that uid, then restart:

  docker run --rm -v notes2latex-data:/data alpine chown -R $(id -u):$(id -g) /data

Compose prefixes the volume name with the project; "docker volume ls" shows it.
MSG
    exit 1
fi
rm -f "$probe"

exec "$@"
EOF

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/openapi.json', timeout=3)"

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["notes2latex", "serve"]
