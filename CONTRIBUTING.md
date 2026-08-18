# Contributing

## Setup

Python 3.12+, Node 22+, [uv](https://docs.astral.sh/uv/), and a LaTeX install with `latexmk`.

```bash
make install
make dev
```

`make help` lists the rest.

## Before pushing

```bash
make lint format typecheck test
```

## Commits

[Conventional Commits](https://www.conventionalcommits.org/). Releases are generated from them.

## Pull requests

Open an issue first for anything large.
