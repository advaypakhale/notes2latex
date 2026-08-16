# Project Commands

Use the Makefile for project-specific commands (tests, linting, formatting, etc.) whenever possible. If the Makefile target doesn't fit the exact need, read the Makefile first to understand the standard tooling and environment setup (e.g., `uv run`), then construct commands accordingly.

# Git Conventions

- Use conventional commits
- DO NOT attribute agents
- Minimise wordy commit bodies, and prefer to omit them

# Engineering Conventions

- Use what a dependency already does properly; do not hand-roll what a framework in use provides
- Minimise hand-rolled UI — pull shadcn/ui components from the registry instead of writing primitives
- Frontend stack is fixed: React + TypeScript + Vite, Tailwind v4, shadcn/ui on base-ui, TanStack Query for server state, zustand for client state
- zod schemas are the frontend's type source, parsed at every boundary
- pydantic models are the backend's, at every boundary: no ad-hoc dicts across the API, graph state or DB-to-response
- Prefer deleting code to adding it; a change that nets more code has to justify itself
