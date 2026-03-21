.DEFAULT_GOAL := help
.PHONY: help install test test-cov lint format format-check type-check check clean all

# ── Paths ──────────────────────────────────────────────────────────────────────
SRC   := satisfactory_ai
TESTS := tests

# ── Help ───────────────────────────────────────────────────────────────────────
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' | \
		sort

# ── Setup ──────────────────────────────────────────────────────────────────────
install: ## Install all dependencies (including dev extras)
	uv sync --extra dev

# ── Testing ────────────────────────────────────────────────────────────────────
test: ## Run tests
	uv run pytest $(TESTS)

test-cov: ## Run tests with coverage report
	uv run pytest $(TESTS) --cov=$(SRC) --cov-report=term-missing --cov-report=html

# ── Linting & Formatting ───────────────────────────────────────────────────────
lint: ## Lint with ruff (errors only, no auto-fix)
	uv run ruff check $(SRC) $(TESTS)

lint-fix: ## Lint with ruff and auto-fix safe issues
	uv run ruff check --fix $(SRC) $(TESTS)

format: ## Format code with black
	uv run black $(SRC) $(TESTS)

format-check: ## Check formatting without making changes
	uv run black --check $(SRC) $(TESTS)

type-check: ## Run mypy static type checking
	uv run mypy $(SRC)/

# ── Compound targets ───────────────────────────────────────────────────────────
check: lint format-check type-check ## Run all checks (lint + format-check + type-check)

all: install check test ## Install, run all checks, then run tests

# ── Cleanup ────────────────────────────────────────────────────────────────────
clean: ## Remove build artefacts, caches, and coverage data
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache"   -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache"   -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov"       -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info"    -exec rm -rf {} + 2>/dev/null || true
	rm -f coverage.xml .coverage
