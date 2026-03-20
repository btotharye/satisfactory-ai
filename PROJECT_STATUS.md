# satisfactory-ai — Project Status

## Current State: **MVP Ready** ✅

The core functionality is implemented and working. Users can parse save files and get AI-powered optimization recommendations.

---

## What's Done

### Core Features
- ✅ **Save file parsing** — Full integration with sat_sav_parse for 1.2 compatibility
- ✅ **Data extraction** — Buildings, power grid, resources, production rates
- ✅ **Claude AI analysis** — Optimization recommendations and bottleneck detection
- ✅ **CLI interface** — Multiple commands (analyze, stats, config)
- ✅ **Interactive mode** — Multi-turn conversation with follow-up questions
- ✅ **JSON output** — Structured data for programmatic use

### Project Structure
- ✅ Modern Python packaging with `pyproject.toml`
- ✅ uv for fast dependency management
- ✅ Proper package layout (`satisfactory_ai/`)
- ✅ MIT License
- ✅ Git submodule for sat_sav_parse

### Documentation
- ✅ **README.md** — User guide with examples
- ✅ **DEVELOPMENT.md** — Developer setup and workflow
- ✅ **TESTING.md** — Comprehensive testing guide
- ✅ **.env.example** — Configuration template

### Code Quality
- ✅ Type hints throughout
- ✅ Error handling with helpful messages
- ✅ Docstrings on all functions
- ✅ Clean module organization

---

## How to Use

### Installation

```bash
git clone --recurse-submodules https://github.com/btotharye/satisfactory-ai.git
cd satisfactory-ai
uv sync
export ANTHROPIC_API_KEY=your-key-here
```

### Basic Usage

```bash
# Analyze your save file
uv run satisfactory-ai analyze ~/MyWorld_autosave_0.sav

# Interactive mode (ask follow-up questions)
uv run satisfactory-ai analyze ~/MyWorld_autosave_0.sav --interactive

# JSON output
uv run satisfactory-ai analyze ~/MyWorld_autosave_0.sav --json

# View parsed data
uv run satisfactory-ai stats ~/MyWorld_autosave_0.sav

# Check configuration
uv run satisfactory-ai config
```

---

## What's Next (Future Enhancements)

### Phase 2 - Polish
- [ ] Add actual test suite (pytest)
- [ ] GitHub Actions for CI/CD
- [ ] Release versioning and tags
- [ ] PyPI package distribution

### Phase 3 - Expand
- [ ] Web UI (Flask/FastAPI)
- [ ] Discord bot integration
- [ ] Historical tracking (compare saves over time)
- [ ] Multi-language support

### Phase 4 - Advanced
- [ ] Production scheduling recommendations
- [ ] Cost/benefit analysis for expansions
- [ ] Community factory database
- [ ] Multiplayer coordination features

---

## Known Limitations

1. **Save Version Support** — Only 1.1.0+ (1.1.x, 1.2.x). Satisfactory 1.0 saves are not supported.
2. **Data Extraction** — Currently extracts basic factory stats. Could be more granular (belt speeds, production ratios, etc.)
3. **Analysis Depth** — Uses general Claude model; could fine-tune for Satisfactory domain
4. **Performance** — No caching; every analysis hits Claude API

---

## GitHub Repository

**https://github.com/btotharye/satisfactory-ai**

Latest commit: `bbfb093` — All functionality working and documented

### Open for:
- Bug reports
- Feature requests
- Pull requests
- Community contributions

---

## Development Notes

### Technology Stack
- **Language:** Python 3.8+
- **Package Manager:** uv
- **Parser:** sat_sav_parse (GreyHak's excellent Satisfactory parser)
- **AI:** Anthropic Claude API
- **CLI:** Click

### Architecture
```
satisfactory_ai/
├── __init__.py           # Package exports
├── cli.py                # Click CLI interface
├── parse_save.py         # Save file parsing + extraction
└── analyze_factory.py    # Claude AI analysis

sat_sav_parse/            # Git submodule (parsing engine)
```

### Key Design Decisions
1. **Modular:** Parsing, analysis, and CLI are separate
2. **Dependency-light:** Only essentials (click, anthropic, python-dotenv)
3. **Submodule approach:** Leverages existing, maintained parser
4. **User-friendly errors:** Helpful messages for common issues

---

## Quick Stats

- **Lines of code:** ~1,500 (Python) + sat_sav_parse
- **Files:** 4 core modules + docs + config
- **Dependencies:** 3 main + sat_sav_parse
- **Commits:** 6
- **Development time:** ~4 hours (this session)

---

## Contributing

Want to help? See [DEVELOPMENT.md](DEVELOPMENT.md) for setup and workflow.

Priority areas:
1. Add pytest test suite
2. Improve data extraction (more detailed building stats)
3. Fine-tune Claude prompts for Satisfactory domain
4. Web UI
5. Community feedback

---

## License

MIT — Free to use, modify, distribute. See [LICENSE](LICENSE).

---

**Project created:** March 20, 2026
**Last updated:** March 20, 2026
**Status:** Ready for beta testing and community use
