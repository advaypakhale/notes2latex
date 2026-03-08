# Project Commands

Use the Makefile for project-specific commands (tests, linting, formatting, etc.) whenever possible. If the Makefile target doesn't fit the exact need, read the Makefile first to understand the standard tooling and environment setup (e.g., `uv run`, `PYTHONPATH=`), then construct commands accordingly.

# Commit and PR Conventions

- Use conventional commits (e.g., `fix:`, `feat:`, `chore:`, `docs:`)
- Never include `Co-Authored-By` or any Claude/AI attribution in commits
- Never include `Closes #N` or `Fixes #N` in commit messages — only in PR descriptions
