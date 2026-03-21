# Contributing to satisfactory-ai

Thank you for your interest in contributing! 🎉

## Getting Started

### 1. Fork & clone with submodules

```bash
git clone --recurse-submodules https://github.com/YOUR_USERNAME/satisfactory-ai.git
cd satisfactory-ai
```

If you already cloned without `--recurse-submodules`:

```bash
git submodule update --init --recursive
```

### 2. Install development dependencies

```bash
uv sync --extra dev
```

### 3. Set up your environment

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 4. Create a branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

---

## Development Workflow

### Running tests

```bash
uv run pytest                                          # run all tests
uv run pytest tests/test_parse_save.py                 # specific module
uv run pytest -k "test_extract_buildings"              # filter by name
uv run pytest --cov=satisfactory_ai --cov-report=term-missing  # with coverage
```

### Linting & formatting

```bash
uv run ruff check .           # lint
uv run ruff check . --fix     # auto-fix lint issues
uv run black .                # auto-format
uv run black --check .        # format check only (used in CI)
uv run mypy satisfactory_ai/  # type check
```

---

## Project Structure

```
satisfactory_ai/
├── __init__.py
├── cli.py              # Click CLI entry point (satisfactory-ai command)
├── parse_save.py       # .sav → JSON → structured factory data
└── analyze_factory.py  # Claude AI analysis & prompt building

sat_sav_parse/          # Git submodule — Satisfactory binary format parser
                        # https://github.com/GreyHak/sat_sav_parse

tests/
├── fixtures/
│   └── sample_save.json    # Minimal save JSON for unit tests
├── test_parse_save.py
└── test_analyze_factory.py
```

### Key data flow

```
.sav file
  └─► sat_sav_parse/sav_cli.py --to-json  (subprocess)
        └─► raw JSON (dict with saveFileInfo + levels[hash].objectHeaders)
              └─► FactoryDataExtractor.extract_all()
                    └─► {"session", "buildings", "powerGrid", "resources", "production", "unlocks"}
                          └─► FactoryAnalyzer.analyze()
                                └─► Claude API → analysis report
```

---

## Adding or Changing Features

### Parser changes (`parse_save.py`)

- All building detection lives in `FactoryDataExtractor._is_factory_building()`.
- The raw save JSON uses `levels[hash_key].objectHeaders` for class/position and
  `levels[hash_key].objects` for property data.
- Add tests in `tests/test_parse_save.py` — extend `tests/fixtures/sample_save.json`
  if you need new object types covered.

### Prompt / analysis changes (`analyze_factory.py`)

- Edit `FactoryAnalyzer._build_analysis_prompt()` to change what Claude sees.
- The default model is `DEFAULT_MODEL = "claude-sonnet-4-6"` (top of file). Users
  can override it via `CLAUDE_MODEL` environment variable.
- Add tests in `tests/test_analyze_factory.py`. The Anthropic client is always
  mocked in tests — never make real API calls in the test suite.

---

## Submitting a Pull Request

1. Make sure all tests pass: `uv run pytest`
2. Make sure linting passes: `uv run ruff check . && uv run black --check .`
3. Commit with a clear message (e.g. `fix: correctly parse conveyor belts`)
4. Push and open a PR against `main`
5. Fill in the PR description — what changed and why

### Commit message convention

We loosely follow [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Use for |
|--------|---------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `test:` | Adding or improving tests |
| `refactor:` | Code cleanup with no behaviour change |
| `docs:` | Documentation only |
| `chore:` | Dependency bumps, CI tweaks |

---

## Reporting Issues

Please include:

- **Satisfactory version** (build number shown in the in-game settings)
- **Python version** (`python --version`)
- **Full error output** (run with `--debug` for more detail)
- **Steps to reproduce**

Open an issue at: <https://github.com/btotharye/satisfactory-ai/issues>

---

## Code of Conduct

Be kind and constructive. We're all here to have fun with factory automation. 🏭
