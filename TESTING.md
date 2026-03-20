# Testing Guide

## Setup

```bash
# Install with all dependencies
uv sync

# Verify installation
uv run satisfactory-ai config
```

## Test Cases

### 1. Config Check

```bash
uv run satisfactory-ai config
```

Expected output:
- ✅ ANTHROPIC_API_KEY is set
- ✅ Claude API is accessible
- ✅ sat_sav_parse module found

### 2. Save File Analysis

Get a Satisfactory save file (`.sav`):

```bash
uv run satisfactory-ai analyze ~/MyWorld_autosave_0.sav
```

Expected output:
- Factory data parsed and extracted
- Claude analysis with optimization recommendations

### 3. JSON Output

```bash
uv run satisfactory-ai analyze ~/MyWorld_autosave_0.sav --json
```

Expected output:
- JSON structure with session, buildings, powerGrid, resources, production, unlocks

### 4. Factory Stats

```bash
uv run satisfactory-ai stats ~/MyWorld_autosave_0.sav
```

Expected output:
- Factory name, playtime, game phase
- Building counts by type
- Power grid stats
- Resources mined

### 5. Interactive Mode

```bash
uv run satisfactory-ai analyze ~/MyWorld_autosave_0.sav --interactive
```

Expected output:
- Initial analysis report
- Prompt for follow-up questions
- Multi-turn conversation with Claude

## Troubleshooting

### "ANTHROPIC_API_KEY not set"

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Or create `.env` file:
```
ANTHROPIC_API_KEY=sk-ant-...
```

### "sat_sav_parse module not found"

Ensure submodules are initialized:
```bash
git submodule update --init --recursive
```

### "Module not found: click / anthropic / etc"

Reinstall dependencies:
```bash
uv sync
```

### Save file parsing fails

- Verify it's a Satisfactory 1.2+ save file
- Try uploading to [Satisfactory Calculator](https://satisfactory-calculator.com) to confirm file is valid
- Check file permissions

## Performance Notes

- Parse time: 1-5 seconds (depends on save size and factory size)
- Claude analysis: 5-15 seconds (API call latency)
- Interactive mode: Faster subsequent questions (uses conversation history)

## Manual Testing Checklist

- [ ] Config check passes
- [ ] Save file parses without errors
- [ ] JSON output is valid
- [ ] Stats display building counts
- [ ] Initial analysis completes
- [ ] Interactive questions/answers work
- [ ] --json flag produces parseable JSON

## Contributing Tests

When adding features, please test:

1. **Parsing:** Does it handle the new data?
2. **Analysis:** Does Claude get useful context?
3. **Output:** Is the format correct (text/JSON)?
4. **Errors:** Do errors have helpful messages?

Example test structure:
```python
def test_new_feature(sample_save_data):
    """Test the new feature works correctly."""
    result = parse_save_file(sample_save_data)
    assert result is not None
    assert "new_field" in result
```
