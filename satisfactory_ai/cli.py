#!/usr/bin/env python3
"""
Command-line interface for Satisfactory AI analyzer.

Usage:
    python cli.py analyze <save-file> [--interactive] [--json]
    python cli.py stats <save-file>
    python cli.py --help
"""

import json
import sys
from pathlib import Path
from typing import Dict

import click

from .analyze_factory import analyze_save_file
from .parse_save import parse_save_file


@click.group()
def cli():
    """Satisfactory AI - Factory Analysis Tool"""
    pass


@cli.command()
@click.argument('save_file', type=click.Path(exists=True))
@click.option('--interactive', '-i', is_flag=True, help='Interactive analysis with follow-up questions')
@click.option('--json', 'output_json', is_flag=True, help='Output raw JSON')
@click.option('--debug', is_flag=True, help='Show debug information')
def analyze(save_file: str, interactive: bool, output_json: bool, debug: bool):
    """Analyze a Satisfactory save file and get AI optimization recommendations."""

    click.echo(f"📂 Loading save file: {save_file}", err=True)

    # Parse the save file
    factory_data = parse_save_file(save_file, debug=debug)
    if not factory_data:
        click.echo("❌ Failed to parse save file", err=True)
        sys.exit(1)

    # Output JSON if requested
    if output_json:
        click.echo(json.dumps(factory_data, indent=2))
        return

    # Analyze with Claude
    click.echo("🤖 Analyzing factory with Claude AI...", err=True)

    if interactive:
        analyze_save_file(factory_data, interactive=True)
    else:
        analysis = analyze_save_file(factory_data, interactive=False)

        # Format and print analysis
        click.echo("\n" + "="*60)
        click.echo("FACTORY ANALYSIS REPORT")
        click.echo("="*60 + "\n")

        session = factory_data.get("session", {})
        click.echo(f"Factory: {session.get('name', 'Unknown')}")
        click.echo(f"Play Time: {session.get('playTime', 0) / 3600:.1f} hours")
        click.echo(f"Game Phase: {session.get('gamePhase', 0)}")
        click.echo("\n" + "-"*60 + "\n")

        click.echo(analysis)

        click.echo("\n" + "="*60)


@cli.command()
@click.argument('save_file', type=click.Path(exists=True))
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def stats(save_file: str, output_json: bool):
    """Display parsed factory statistics."""

    click.echo(f"📂 Loading save file: {save_file}", err=True)

    factory_data = parse_save_file(save_file)
    if not factory_data:
        click.echo("❌ Failed to parse save file", err=True)
        sys.exit(1)

    if output_json:
        click.echo(json.dumps(factory_data, indent=2))
        return

    # Format stats output
    session = factory_data.get("session", {})
    buildings = factory_data.get("buildings", [])
    power = factory_data.get("powerGrid", {})
    resources = factory_data.get("resources", {})

    click.echo("\n" + "="*60)
    click.echo("FACTORY STATISTICS")
    click.echo("="*60 + "\n")

    click.echo(f"Session: {session.get('name', 'Unknown')}")
    click.echo(f"Play Time: {session.get('playTime', 0) / 3600:.1f} hours")
    click.echo(f"Game Phase: {session.get('gamePhase', 0)}")
    click.echo(f"Active Milestone: {session.get('activeMilestone', 'None')}")

    click.echo(f"\nBuildings: {len(buildings)}")
    if buildings:
        # Group by type
        building_types: Dict[str, int] = {}
        for b in buildings:
            btype = b.get('type', 'Unknown')
            building_types[btype] = building_types.get(btype, 0) + 1

        for btype, count in sorted(building_types.items()):
            click.echo(f"  - {btype}: {count}")

    click.echo("\nPower Grid:")
    click.echo(f"  - Production: {power.get('totalProduction', 0)} MW")
    click.echo(f"  - Consumption: {power.get('totalConsumption', 0)} MW")
    click.echo(f"  - Storage: {power.get('storage', 0)} MWh")
    click.echo(f"  - Batteries: {power.get('batteries', 0)}")

    if resources:
        click.echo("\nResources Mined:")
        for resource, amount in resources.items():
            click.echo(f"  - {resource}: {amount}")

    click.echo("\n" + "="*60)


@cli.command()
def config():
    """Check configuration and API key status."""

    import os

    from anthropic import Anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")

    click.echo("\n" + "="*60)
    click.echo("CONFIGURATION")
    click.echo("="*60 + "\n")

    if api_key:
        click.echo("✅ ANTHROPIC_API_KEY is set")
        # Test the API connection
        try:
            client = Anthropic(api_key=api_key)
            # Simple test call
            client.messages.create(
                model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6"),
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}],
            )
            click.echo("✅ Claude API is accessible")
        except Exception as e:
            click.echo(f"❌ API error: {e}")
    else:
        click.echo("❌ ANTHROPIC_API_KEY not set")
        click.echo("\nSet it with:")
        click.echo("  export ANTHROPIC_API_KEY=your-key-here")
        click.echo("\nOr create a .env file with:")
        click.echo("  ANTHROPIC_API_KEY=your-key-here")

    # Check for sat_sav_parse
    sat_sav_path = Path(__file__).parent / "sat_sav_parse"
    if sat_sav_path.exists():
        click.echo("\n✅ sat_sav_parse module found")
    else:
        click.echo("\n⚠️  sat_sav_parse module not found")
        click.echo("Initialize submodule with:")
        click.echo("  git submodule update --init --recursive")

    click.echo("\n" + "="*60)


@cli.command()
def version():
    """Show version information."""
    click.echo("satisfactory-ai v0.1.0")
    click.echo("Powered by Claude AI")


if __name__ == '__main__':
    cli()
