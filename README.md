# notes2latex

Convert handwritten math notes (PDFs or images) into compiled LaTeX documents using vision LLMs.

Upload your notes, and notes2latex will process each page through a vision model to produce LaTeX, automatically compile it, and fix any compilation errors — outputting a clean `.pdf` and `.tex` file.

## Quick Start (Docker)

```bash
docker compose up
```

Open `http://localhost:8000`, go to Settings, and enter your API key. The key is stored in your browser and sent directly to the provider.

### CLI

```bash
# Basic conversion
notes2latex convert notes.pdf

# With options
notes2latex convert notes.pdf -m openai/gpt-4o -o ./out --dpi 200

# Start the web server
notes2latex serve
```

## Configuration

The API key and model are configured in the web UI Settings page. For the CLI, set your provider's API key as an environment variable (e.g. `OPENROUTER_API_KEY`, `OPENAI_API_KEY`) — see [litellm providers](https://docs.litellm.ai/docs/providers).

Pipeline settings can be set via environment variables with the `NOTES2LATEX_` prefix:

| Variable | Default | Description |
|---|---|---|
| `NOTES2LATEX_MODEL` | `openrouter/google/gemini-3-flash-preview` | LLM model ([supported providers](https://docs.litellm.ai/docs/providers)) |
| `NOTES2LATEX_TEMPERATURE` | `0.1` | LLM sampling temperature |
| `NOTES2LATEX_MAX_TOKENS` | `16384` | Max tokens per LLM call |
| `NOTES2LATEX_MAX_RETRIES` | `3` | Compilation fix attempts per page |
| `NOTES2LATEX_CONTEXT_LINES` | `40` | Lines of prior LaTeX passed as context |
| `NOTES2LATEX_DPI` | `300` | DPI for PDF-to-image rasterization |
| `NOTES2LATEX_LATEX_ENGINE` | `pdflatex` | LaTeX engine for compilation |
| `NOTES2LATEX_COMPILE_TIMEOUT` | `60` | Seconds before compilation timeout |
| `NOTES2LATEX_OUTPUT_DIR` | `./output` | Output directory (CLI only) |

## Local Development

**Prerequisites:** Python 3.12+, Node.js 22+, [uv](https://docs.astral.sh/uv/), a LaTeX distribution (`texlive-latex-extra`, `texlive-science`, `texlive-pictures`, `latexmk`)

```bash
# Install dependencies
make install
cd frontend && npm install && cd ..

```

Run the backend and frontend dev servers in separate terminals:

```bash
# Terminal 1: backend (port 8000)
make serve

# Terminal 2: frontend with hot reload (port 5173, proxies API to 8000)
make dev-frontend
```

### Other commands

```bash
make test          # run tests
make lint          # ruff check
make format        # ruff format
make docker-build  # build Docker image
```
