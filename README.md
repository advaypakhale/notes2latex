<p align="center">
  <h1 align="center">notes2latex</h1>
  <p align="center">
    Handwritten notes in, compiled LaTeX out. Open source. Runs locally. Free forever.
  </p>
  <p align="center">
    <a href="#quick-start">Quick Start</a> &bull;
    <a href="#how-it-works">How It Works</a> &bull;
    <a href="#features">Features</a> &bull;
    <a href="#configuration">Configuration</a> &bull;
    <a href="#model-recommendations">Model Recommendations</a> &bull;
    <a href="#local-development">Local Development</a>
  </p>
  <p align="center">
    <a href="https://github.com/advaypakhale/notes2latex/actions/workflows/ci.yml"><img src="https://github.com/advaypakhale/notes2latex/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
    <a href="https://github.com/advaypakhale/notes2latex/pkgs/container/notes2latex"><img src="https://ghcr-badge.egpl.dev/advaypakhale/notes2latex/latest_tag?trim=major&label=image" alt="Docker Image"></a>
    <a href="https://github.com/advaypakhale/notes2latex/blob/main/LICENSE"><img src="https://img.shields.io/github/license/advaypakhale/notes2latex" alt="License"></a>
  </p>
</p>

---

**notes2latex** is an open-source tool that converts handwritten math notes into compiled LaTeX documents using vision language models (VLMs). Upload a scan or photo of your notes, and it gives you back a `.tex` file and a PDF.

It uses an agentic generate-compile-fix loop: every page is compiled as it's generated, and if anything breaks, the model reads the error log and fixes it automatically. Because pages are processed sequentially with context carried forward, there's no limit on document length. Further, the output is compiler-verified, so you get a PDF that actually renders.

It runs entirely on your machine; there's no account, no subscription, no data leaving your computer beyond the API calls you choose to make. It's also bring your own key (BYOK) and model-agnostic, so you can choose your model freely, including self-hosted models (!!).
## Quick Start

Create a `docker-compose.yml`:

```yaml
services:
  notes2latex:
    image: ghcr.io/advaypakhale/notes2latex:latest
    ports:
      - "8000:8000"
    env_file:
      - path: .env
        required: false
    volumes:
      - notes2latex-data:/app/data

volumes:
  notes2latex-data:
```

Then run:

```bash
docker compose up
```

Open [http://localhost:8000](http://localhost:8000), go to **Settings**, enter your API key, and upload your notes and get converting!

> Don't have an API key yet? See [Configuration](#setting-your-api-key) for a fast-ish way to get one.

## How It Works

The core of notes2latex is an agentic **generate-compile-fix loop** built with [LangGraph](https://github.com/langchain-ai/langgraph). For each page:

1. A VLM reads the page image and generates LaTeX body content: equations, theorems, proofs, definitions, diagrams, text, and all.
2. The output is immediately compiled. If compilation succeeds, it moves to the next page.
3. If compilation fails, the model receives the error log and rewrites the broken section. This retries up to 3 times per page, and most errors get resolved automatically.

Pages are processed sequentially, not in isolation. Each page receives the last 40 lines of previously generated LaTeX as context, plus a list of any open environments (e.g. an unclosed `align*` from the previous page). This means notation, numbering, and document structure stay consistent - and there's no upper limit on document length.

The output is a complete, compilable `.tex` document with preamble and the compiled PDF. Because every page is compiler-verified before the pipeline moves on, the final document is essentially guaranteed to compile.

## Features

- **Compiler-verified output**: every page is compiled as it's generated; if it fails, the model fixes it before moving on.
- **Full document output**: produces a complete `.tex` file with preamble and all pages, plus the compiled PDF.
- **Unlimited document length**: pages are processed sequentially with context carried forward, so there's no cap on how long the input can be.
- **Side-by-side review**: compare each original page against the generated LaTeX in a split view. Copy LaTeX per page.
- **Customizable preamble**: the default includes `amsmath`, `amssymb`, `amsthm`, `mathtools`, `physics`, `tikz`, `pgfplots`, and common theorem environments. Add your own packages and `\newcommand` definitions in the Settings page.
- **Any model, any provider**: works with any VLM through [LiteLLM](https://docs.litellm.ai/docs/providers) (100+ models), including free and self-hosted ones.
- **Real-time progress**: streaming updates show which page is being processed and what step the pipeline is on.
- **CLI**: `notes2latex convert notes.pdf` if you prefer the command line.

```bash
# Convert a file
notes2latex convert notes.pdf

# Pick a model and output directory
notes2latex convert notes.pdf -m openai/gpt-4o -o ./out --dpi 200

# Start the web server
notes2latex serve
```

## Configuration

### Setting your API key

Your API key is configured in the web UI under **Settings**.

> **Tip — OpenRouter as a universal key:** [OpenRouter](https://openrouter.ai) gives you a single API key that routes to models from Google, Anthropic, OpenAI, Meta, Qwen, and others — including free models. Easiest way to get started without managing multiple keys.

### Pipeline settings

These can be set as environment variables (prefix `NOTES2LATEX_`) or in a `.env` file:

| Variable | Default | Description |
|---|---|---|
| `NOTES2LATEX_MODEL` | `ollama/llava` | VLM to use ([supported providers](https://docs.litellm.ai/docs/providers)) |
| `NOTES2LATEX_API_BASE` | `http://localhost:11434` | Base URL for model providers (useful for self-hosted Ollama endpoints) |
| `NOTES2LATEX_TEMPERATURE` | `0.1` | Sampling temperature |
| `NOTES2LATEX_MAX_TOKENS` | `16384` | Max tokens per VLM call |
| `NOTES2LATEX_MAX_RETRIES` | `3` | Compilation fix attempts per page |
| `NOTES2LATEX_CONTEXT_LINES` | `40` | Lines of prior LaTeX passed as context |
| `NOTES2LATEX_DPI` | `300` | DPI for PDF-to-image rasterization |
| `NOTES2LATEX_LATEX_ENGINE` | `pdflatex` | LaTeX engine |
| `NOTES2LATEX_COMPILE_TIMEOUT` | `60` | Compilation timeout (seconds) |

## Model Recommendations

notes2latex works with any vision language model accessible through [LiteLLM](https://docs.litellm.ai/docs/providers). Some handle handwritten math better than others. Here's what has worked well so far in my limited testing; this is not exhaustive and the landscape moves fast.

### Proprietary models

**Gemini 3 Flash Preview** is set as the default model in settings. This works fairly well, and is reasonably cheap at ~$0.002–0.003 per page.

### Local / free models

If you're into open models, **Qwen3-VL-30B-A3B-Thinking** is probably the lowest parameter model that I tried that gave decent outputs (it also seems amenable to self-hosting without going bankrupt). It is also available for free on [OpenRouter](https://openrouter.ai), although availability is (understandably) poor. The **Qwen 3.5** variants also performed pretty well.

> **Tip:** You can enter any model string in Settings by clicking **"Enter custom model string"** and typing the [LiteLLM model identifier](https://docs.litellm.ai/docs/providers) (e.g., `openrouter/qwen/qwen3-vl-30b-a3b-thinking`).

## Local Development

**Prerequisites:** Python 3.12+, Node.js 22+, [uv](https://docs.astral.sh/uv/), a LaTeX installation with `latexmk`.

```bash
make install    # install backend + frontend dependencies
make dev        # run backend + frontend dev servers
```

Run `make help` to see all available targets.

## AI Declaration

I wrote a (very crude) first version of this project back in Summer 2025, and never released it. Software engineering has drastically shifted since then (currently March 2026), and I used the tools we have available now to revisit the project and see if I can make it ready for release, without spending too much time on it.

Mainly this was developed with Claude Code with Opus 4.6. I wrote the core code for the backend by hand, then expanded it rapidly to include a frontend (which I literally cannot do; I'm primarily a backend dev) and some other neat features.

I think these sorts of projects are particularly amenable to AI development. This runs locally, has very standard dependencies, and in general doesn't do a whole lot that is messy from a security perspective. I would NOT host this on a public endpoint before doing a thorough code review, however.

## License

[MIT](LICENSE)
