.PHONY: help install dev dev-backend dev-frontend build up down lint format typecheck test clean

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install backend and frontend dependencies
	uv sync
	cd frontend && npm install
	uvx pre-commit install

dev: ## Run backend and frontend dev servers
	trap 'kill 0' EXIT; $(MAKE) dev-backend & $(MAKE) dev-frontend & wait

dev-backend: ## Run backend dev server
	uv run notes2latex serve

dev-frontend: ## Run frontend dev server
	cd frontend && npm run dev

build: ## Build the Docker image
	docker compose build

up: ## Start the container in the background
	docker compose up -d

down: ## Stop the container
	docker compose down

lint: ## Lint backend and frontend
	uv run ruff check src/ tests/
	cd frontend && npm run lint

format: ## Format backend and frontend
	uv run ruff format src/ tests/
	cd frontend && npm run format

typecheck: ## Type-check the frontend
	cd frontend && npm run typecheck

test: ## Run backend tests
	uv run pytest -v

clean: ## Remove build artifacts and caches
	rm -rf frontend/dist .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -not -path './.venv/*' -exec rm -rf {} +
