# Development Guide

This project uses **uv** for fast, modern Python package management.

## Setup

### Install uv

If you don't have uv installed:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via Homebrew
brew install uv

# Or via pip
pip install uv
```

### Clone and Install

```bash
git clone --recurse-submodules https://github.com/btotharye/satisfactory-ai.git
cd satisfactory-ai

# Install dependencies with uv
uv sync

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# or on Windows:
.venv\Scripts\activate

# Or run commands directly with uv
uv run python cli.py --help
```

## Development Workflow

### Running Commands

```bash
# With venv activated
python cli.py analyze <save-file>

# Or with uv (no venv needed)
uv run python cli.py analyze <save-file>

# Run as script
uv run satisfactory-ai analyze <save-file>
```

### Installing Dev Dependencies

```bash
# Install with dev tools (pytest, black, ruff)
uv sync --all-extras

# Or install extras separately
uv pip install pytest black ruff
```

### Code Quality

```bash
# Format code
uv run black .

# Lint
uv run ruff check .

# Fix linting issues
uv run ruff check --fix .

# Run tests
uv run pytest
```

### Adding Dependencies

```bash
# Add a new package
uv pip install new-package

# Or add to pyproject.toml and sync
uv sync
```

### Updating Dependencies

```bash
# Update lock file
uv lock

# Upgrade all packages
uv pip install --upgrade -e .
```

## Project Structure

```
satisfactory-ai/
├── cli.py                 # Main CLI entry point
├── parse_save.py          # Save file parsing
├── analyze_factory.py     # Claude AI analysis
├── pyproject.toml         # Project config (uv, packaging)
├── uv.lock                # Locked dependencies
├── requirements.txt       # Legacy pip format (optional)
├── README.md              # User documentation
├── DEVELOPMENT.md         # This file
├── LICENSE                # MIT
└── sat_sav_parse/         # Submodule: Satisfactory parser
```

## Testing

### Running Tests

```bash
uv run pytest
```

### Writing Tests

Create test files in a `tests/` directory:

```python
# tests/test_parse_save.py
import pytest
from parse_save import parse_save_file

def test_parse_save_file():
    # Test implementation
    pass
```

## Build and Release

### Build Package

```bash
# Using hatchling (specified in pyproject.toml)
uv build
```

### Publish to PyPI

```bash
# After building
uv publish
```

## Tips

- **uv is fast:** Dependency resolution is much faster than pip
- **Lock file:** Commit `uv.lock` for reproducible installs
- **Python versions:** Supports 3.8+
- **Virtual env:** Auto-created in `.venv` by uv

## Troubleshooting

### "uv command not found"

Make sure uv is installed and in your PATH:

```bash
uv --version
```

### Submodule issues

If `sat_sav_parse` is missing:

```bash
git submodule update --init --recursive
```

### Dependency conflicts

Clear cache and reinstall:

```bash
rm uv.lock
uv sync
```

## Contributing

1. Fork the repo
2. Create a feature branch
3. Install dev dependencies: `uv sync --all-extras`
4. Make changes
5. Format & lint: `uv run black . && uv run ruff check --fix .`
6. Submit a PR

---

Questions? Open an issue or check [uv docs](https://docs.astral.sh/uv/).
