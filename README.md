# satisfactory-ai

AI-powered factory analyzer for Satisfactory. Upload your save file and get intelligent optimization suggestions, bottleneck analysis, and production insights powered by Claude AI.

## Features

- 📊 **Save File Analysis** — Parse Satisfactory `.sav` files and extract factory stats
- 🤖 **AI Insights** — Get personalized optimization suggestions using Claude
- 🔍 **Bottleneck Detection** — Identifies production constraints and inefficiencies
- ⚡ **Power Analysis** — Reviews power consumption and grid efficiency
- 📈 **Production Targets** — Recommends building counts and ratios
- 🎯 **Priority Fixes** — Ranked optimization suggestions

## Installation

### With uv (Recommended)

```bash
# Clone with submodules included
git clone --recurse-submodules https://github.com/btotharye/satisfactory-ai.git
cd satisfactory-ai

# Install dependencies
uv sync

# Set API key
export ANTHROPIC_API_KEY=your-key-here

# Run
uv run satisfactory-ai analyze <save-file>
```

**If you already cloned without `--recurse-submodules`:**
```bash
cd satisfactory-ai
git submodule update --init --recursive
uv sync
```

### With pip

```bash
git clone https://github.com/btotharye/satisfactory-ai.git
cd satisfactory-ai
pip install -r requirements.txt
```

## Quick Start

```bash
# Set your API key
export ANTHROPIC_API_KEY=your-key-here

# Analyze your save file
uv run satisfactory-ai analyze ~/path/to/YourWorld_autosave_0.sav

# Output: Detailed optimization report with AI analysis
```

## How It Works

1. **Parse** — Your save file is parsed using the Satisfactory save format (Unreal Engine binary)
2. **Extract** — Factory data is extracted: buildings, power grid, resources, production rates
3. **Analyze** — Data is sent to Claude API for intelligent analysis
4. **Report** — You get a detailed report with:
   - Current production bottlenecks
   - Power grid inefficiencies
   - Specific optimization recommendations
   - Building count suggestions for your targets

## Usage

### Basic Analysis

```bash
uv run satisfactory-ai analyze <save-file-path>
```

Outputs a formatted analysis report to the terminal.

Example:
```bash
uv run satisfactory-ai analyze ~/MyWorld_autosave_0.sav
```

### Interactive Analysis

Ask follow-up questions about your factory:
```bash
uv run satisfactory-ai analyze <save-file-path> --interactive
```

### JSON Output

```bash
uv run satisfactory-ai analyze <save-file-path> --json
```

Outputs raw JSON for integration with other tools.

### Detailed Factory Stats

```bash
uv run satisfactory-ai stats <save-file-path>
```

Shows parsed factory data (buildings, power, resources, etc.).

### Check Configuration

```bash
uv run satisfactory-ai config
```

Verify API key is set and dependencies are working.

## Configuration

Set your OpenAI API key:

```bash
export ANTHROPIC_API_KEY=your-key-here
```

Or create a `.env` file:

```
ANTHROPIC_API_KEY=your-key-here
```

## Requirements

- Python 3.8+
- [uv](https://docs.astral.sh/uv/) or pip
- Claude API key (free tier available at [console.anthropic.com](https://console.anthropic.com))
- A Satisfactory save file (`.sav`)

## Project Structure

```
satisfactory-ai/
├── cli.py                 # Command-line interface
├── parse_save.py          # Save file parser wrapper
├── analyze_factory.py     # Claude AI analysis
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── LICENSE                # MIT License
└── sat_sav_parse/         # Submodule: Parser library
```

## Supported Versions

**Satisfactory 1.1.0 and later** (1.1.x, 1.2.x)

**Not supported:**
- Satisfactory 1.0.x and earlier
- Experimental builds may need newer parser

If you get "Unsupported save header version" error, your save is too old. Consider updating to a newer Satisfactory version or using a more recent save file.

## Save File Location

### Windows
```
%LOCALAPPDATA%\FactoryGame\Saved\SaveGames\
```

### Linux / Mac
```
~/.config/Epic/FactoryGame/Saved/SaveGames/
```

## Example Analysis

```
Factory Analysis Report
======================

Session: My Factory v1
Play Time: 45.6 hours
Game Phase: 3

BOTTLENECKS DETECTED:
1. Iron production is capped at 120 plates/min but you need 180
   → Add 2 more smelters + 1 mining operation
   
2. Copper wire is the limiting factor for circuits
   → Increase wire production from 45 to 90 items/min
   
POWER ANALYSIS:
- Current: 2,100 MW / 2,500 MW capacity (84% utilization)
- Recommended: Add 1 more coal generator (500 MW buffer)

PRIORITY RECOMMENDATIONS:
1. Scale iron production (High Impact, 2 hours work)
2. Expand power grid (Medium Impact, 1 hour work)
3. Optimize copper routing (Low Impact, 30 min work)
```

## Contributing

Contributions welcome! Please:

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Roadmap

- [ ] Web UI for drag-and-drop analysis
- [ ] Discord bot integration
- [ ] Multi-language support
- [ ] Advanced production planning
- [ ] Comparison against community builds
- [ ] Historical tracking (analyze save file changes over time)

## Troubleshooting

### "Invalid save file format"
- Ensure the `.sav` file is from Satisfactory v1.2.0.0 or compatible version
- Try uploading to [Satisfactory Calculator](https://satisfactory-calculator.com) to verify the file is readable

### API Key Issues
- Check your `ANTHROPIC_API_KEY` environment variable is set correctly
- Verify your API key is active at [console.anthropic.com](https://console.anthropic.com)

### Parser Errors
- Update sat_sav_parse submodule: `git submodule update --init --recursive`

## License

MIT License — See [LICENSE](LICENSE) for details.

## Credits

- Parser: [GreyHak/sat_sav_parse](https://github.com/GreyHak/sat_sav_parse)
- AI: [Anthropic Claude API](https://anthropic.com)
- Game: [Satisfactory by Coffee Stain Studios](https://www.satisfactory.com)

## Support

Found a bug? Have a suggestion? [Open an issue](https://github.com/btotharye/satisfactory-ai/issues).

---

**Built with ❤️ by [Brian](https://github.com/btotharye) | [Twitter](https://twitter.com/btotharye)**
