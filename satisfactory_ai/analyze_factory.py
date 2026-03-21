"""
Analyze factory data using Claude AI.

Takes extracted factory data and generates optimization recommendations.
"""

import json
import os
from typing import Any, Dict, List, Optional

from anthropic import Anthropic

# Default Claude model — override with the CLAUDE_MODEL environment variable.
DEFAULT_MODEL = "claude-sonnet-4-6"


class FactoryAnalyzer:
    """Analyze factory data and generate AI-powered insights."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the analyzer with Claude API.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable."
            )

        self.client = Anthropic(api_key=self.api_key)
        self.conversation_history = []

    def analyze(self, factory_data: Dict[str, Any]) -> str:
        """
        Analyze factory data and return optimization recommendations.

        Args:
            factory_data: Extracted factory data from parse_save.py

        Returns:
            Analysis report as formatted string
        """
        prompt = self._build_analysis_prompt(factory_data)

        model = os.getenv("CLAUDE_MODEL", DEFAULT_MODEL)

        response = self.client.messages.create(
            model=model,
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        return response.content[0].text

    def analyze_interactive(self, factory_data: Dict[str, Any]) -> None:
        """
        Start an interactive analysis session.

        Allows follow-up questions about the factory.
        """
        print("Starting interactive factory analysis...")
        print("(Type 'quit' to exit)\n")

        # Initial analysis
        initial_prompt = self._build_analysis_prompt(factory_data)
        self.conversation_history.append({
            "role": "user",
            "content": initial_prompt
        })

        model = os.getenv("CLAUDE_MODEL", DEFAULT_MODEL)

        response = self.client.messages.create(
            model=model,
            max_tokens=2000,
            messages=self.conversation_history
        )

        analysis = response.content[0].text
        print("=== Factory Analysis ===\n")
        print(analysis)
        print("\n" + "="*50 + "\n")

        self.conversation_history.append({
            "role": "assistant",
            "content": analysis
        })

        # Interactive follow-ups
        while True:
            user_input = input("Ask a follow-up question (or 'quit'): ").strip()
            if user_input.lower() == 'quit':
                break
            if not user_input:
                continue

            self.conversation_history.append({
                "role": "user",
                "content": user_input
            })

            response = self.client.messages.create(
                model=model,
                max_tokens=1500,
                messages=self.conversation_history
            )

            answer = response.content[0].text
            print(f"\n{answer}\n")

            self.conversation_history.append({
                "role": "assistant",
                "content": answer
            })

    @staticmethod
    def _build_analysis_prompt(factory_data: Dict[str, Any]) -> str:
        """Build the analysis prompt for Claude."""
        session = factory_data.get("session", {})
        buildings: List[Dict[str, Any]] = factory_data.get("buildings", [])
        power = factory_data.get("powerGrid", {})
        resources = factory_data.get("resources", {})
        production = factory_data.get("production", {})

        # Summarise buildings by type count rather than dumping every instance
        building_counts = production.get("buildingCounts", {})
        building_summary = (
            "\n".join(f"  - {btype}: {count}" for btype, count in sorted(building_counts.items()))
            if building_counts
            else "  (none)"
        )

        generators = power.get("generators", [])
        generator_summary = (
            "\n".join(f"  - {g}" for g in sorted(set(generators)))
            if generators
            else "  (none)"
        )

        prompt = f"""You are an expert Satisfactory factory advisor. Analyze this factory and provide specific, actionable optimization recommendations.

FACTORY DATA:
- Session: {session.get('name', 'Unknown')}
- Play Time: {session.get('playTime', 0) / 3600:.1f} hours
- Game Build Version: {session.get('buildVersion', 'Unknown')}
- Active Milestone: {session.get('activeMilestone', 'None') or 'None'}

BUILDINGS ({len(buildings)} total):
{building_summary}

POWER GRID:
- Total Generators: {len(generators)}
{generator_summary}
- Batteries/Storage: {power.get('batteries', 0)}

RESOURCES:
{json.dumps(resources, indent=2) if resources else "  (none recorded)"}

Please provide:
1. **Current State** — Brief summary of what the factory has built so far
2. **Bottlenecks** — What is limiting production right now?
3. **Power Analysis** — Is the power setup sufficient for expansion?
4. **Top 3 Priorities** — Most impactful next steps, specific to the buildings listed
5. **What to Build Next** — Concrete building recommendations with counts

Be specific and reference the actual building types listed above."""

        return prompt


def analyze_save_file(save_data: Dict[str, Any], interactive: bool = False) -> str:
    """
    Analyze factory save data using Claude.

    Args:
        save_data: Parsed factory data
        interactive: If True, start interactive session

    Returns:
        Analysis report as string
    """
    try:
        analyzer = FactoryAnalyzer()

        if interactive:
            analyzer.analyze_interactive(save_data)
            return ""
        else:
            return analyzer.analyze(save_data)

    except ValueError as e:
        return f"Error: {e}\n\nMake sure to set the ANTHROPIC_API_KEY environment variable."
    except Exception as e:
        return f"Analysis error: {e}"


if __name__ == "__main__":
    # Example usage
    sample_data = {
        "session": {
            "name": "Test Factory",
            "playTime": 3600,
            "gamePhase": 1
        },
        "buildings": [],
        "powerGrid": {},
        "resources": {}
    }

    print(analyze_save_file(sample_data))
