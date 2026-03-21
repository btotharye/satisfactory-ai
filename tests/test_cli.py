"""
Tests for satisfactory_ai.cli — all Click commands via CliRunner.

All external I/O (parse_save_file, analyze_save_file, Anthropic) is mocked so
these tests run instantly without a real .sav file or API key.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from satisfactory_ai.cli import cli

# ---------------------------------------------------------------------------
# Shared factory data used across tests
# ---------------------------------------------------------------------------

SAMPLE_FACTORY_DATA = {
    "session": {
        "name": "TestWorld",
        "playTime": 7200,
        "gamePhase": 1,
        "activeMilestone": "Tier 2",
        "buildVersion": 480000,
    },
    "buildings": [
        {
            "type": "Build_MinerMk1_C",
            "typePath": "/Game/FactoryGame/Buildable/Factory/MinerMK1/Build_MinerMk1.Build_MinerMk1_C",
            "location": [100.0, 200.0, 300.0],
            "name": "Persistent_Level:PersistentLevel.Build_MinerMk1_C_001",
        },
        {
            "type": "Build_SmelterMk1_C",
            "typePath": "/Game/FactoryGame/Buildable/Factory/SmelterMk1/Build_SmelterMk1.Build_SmelterMk1_C",
            "location": [150.0, 200.0, 300.0],
            "name": "Persistent_Level:PersistentLevel.Build_SmelterMk1_C_001",
        },
    ],
    "powerGrid": {
        "totalProduction": 150,
        "totalConsumption": 80,
        "storage": 0,
        "batteries": 0,
        "generators": ["Build_GeneratorIntegratedBiomass_C", "Build_GeneratorIntegratedBiomass_C"],
    },
    "resources": {"Iron Ore": 500, "Copper Ore": 200},
    "production": {
        "estimated": True,
        "buildingCounts": {"Build_MinerMk1_C": 1, "Build_SmelterMk1_C": 1},
    },
    "unlocks": {"milestonesCompleted": 3, "schematicsUnlocked": 5},
}


@pytest.fixture
def runner():
    # mix_stderr=False keeps stderr separate so stdout-only assertions
    # (e.g. JSON parsing) are not contaminated by progress messages.
    return CliRunner(mix_stderr=False)


@pytest.fixture
def fake_sav(tmp_path) -> Path:
    """Create a dummy .sav file so click's path existence check passes."""
    f = tmp_path / "test.sav"
    f.write_bytes(b"\x00" * 16)
    return f


# ---------------------------------------------------------------------------
# analyze command
# ---------------------------------------------------------------------------


class TestAnalyzeCommand:
    def test_success_prints_report(self, runner, fake_sav):
        with (
            patch("satisfactory_ai.cli.parse_save_file", return_value=SAMPLE_FACTORY_DATA),
            patch("satisfactory_ai.cli.analyze_save_file", return_value="Great factory!"),
        ):
            result = runner.invoke(cli, ["analyze", str(fake_sav)])

        assert result.exit_code == 0
        assert "FACTORY ANALYSIS REPORT" in result.output
        assert "Great factory!" in result.output

    def test_success_shows_session_name(self, runner, fake_sav):
        with (
            patch("satisfactory_ai.cli.parse_save_file", return_value=SAMPLE_FACTORY_DATA),
            patch("satisfactory_ai.cli.analyze_save_file", return_value="OK"),
        ):
            result = runner.invoke(cli, ["analyze", str(fake_sav)])

        assert "TestWorld" in result.output

    def test_success_shows_play_time_in_hours(self, runner, fake_sav):
        with (
            patch("satisfactory_ai.cli.parse_save_file", return_value=SAMPLE_FACTORY_DATA),
            patch("satisfactory_ai.cli.analyze_save_file", return_value="OK"),
        ):
            result = runner.invoke(cli, ["analyze", str(fake_sav)])

        # 7200 seconds == 2.0 hours
        assert "2.0 hours" in result.output

    def test_parse_failure_exits_nonzero(self, runner, fake_sav):
        with patch("satisfactory_ai.cli.parse_save_file", return_value=None):
            result = runner.invoke(cli, ["analyze", str(fake_sav)])

        assert result.exit_code != 0

    def test_json_flag_outputs_json(self, runner, fake_sav):
        with patch("satisfactory_ai.cli.parse_save_file", return_value=SAMPLE_FACTORY_DATA):
            result = runner.invoke(cli, ["analyze", str(fake_sav), "--json"])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["session"]["name"] == "TestWorld"

    def test_json_flag_skips_ai_analysis(self, runner, fake_sav):
        with (
            patch("satisfactory_ai.cli.parse_save_file", return_value=SAMPLE_FACTORY_DATA),
            patch("satisfactory_ai.cli.analyze_save_file") as mock_analyze,
        ):
            runner.invoke(cli, ["analyze", str(fake_sav), "--json"])

        mock_analyze.assert_not_called()

    def test_debug_flag_is_forwarded_to_parser(self, runner, fake_sav):
        with (
            patch(
                "satisfactory_ai.cli.parse_save_file", return_value=SAMPLE_FACTORY_DATA
            ) as mock_parse,
            patch("satisfactory_ai.cli.analyze_save_file", return_value="OK"),
        ):
            runner.invoke(cli, ["analyze", str(fake_sav), "--debug"])

        mock_parse.assert_called_once_with(str(fake_sav), debug=True)

    def test_debug_false_by_default(self, runner, fake_sav):
        with (
            patch(
                "satisfactory_ai.cli.parse_save_file", return_value=SAMPLE_FACTORY_DATA
            ) as mock_parse,
            patch("satisfactory_ai.cli.analyze_save_file", return_value="OK"),
        ):
            runner.invoke(cli, ["analyze", str(fake_sav)])

        mock_parse.assert_called_once_with(str(fake_sav), debug=False)

    def test_interactive_flag_calls_interactive_mode(self, runner, fake_sav):
        with (
            patch("satisfactory_ai.cli.parse_save_file", return_value=SAMPLE_FACTORY_DATA),
            patch("satisfactory_ai.cli.analyze_save_file", return_value="") as mock_analyze,
        ):
            runner.invoke(cli, ["analyze", str(fake_sav), "--interactive"])

        mock_analyze.assert_called_once_with(SAMPLE_FACTORY_DATA, interactive=True)

    def test_nonexistent_file_exits_nonzero(self, runner, tmp_path):
        result = runner.invoke(cli, ["analyze", str(tmp_path / "no_such.sav")])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# stats command
# ---------------------------------------------------------------------------


class TestStatsCommand:
    def test_success_prints_statistics(self, runner, fake_sav):
        with patch("satisfactory_ai.cli.parse_save_file", return_value=SAMPLE_FACTORY_DATA):
            result = runner.invoke(cli, ["stats", str(fake_sav)])

        assert result.exit_code == 0
        assert "FACTORY STATISTICS" in result.output

    def test_shows_session_name(self, runner, fake_sav):
        with patch("satisfactory_ai.cli.parse_save_file", return_value=SAMPLE_FACTORY_DATA):
            result = runner.invoke(cli, ["stats", str(fake_sav)])

        assert "TestWorld" in result.output

    def test_shows_play_time_in_hours(self, runner, fake_sav):
        with patch("satisfactory_ai.cli.parse_save_file", return_value=SAMPLE_FACTORY_DATA):
            result = runner.invoke(cli, ["stats", str(fake_sav)])

        assert "2.0 hours" in result.output

    def test_shows_building_counts(self, runner, fake_sav):
        with patch("satisfactory_ai.cli.parse_save_file", return_value=SAMPLE_FACTORY_DATA):
            result = runner.invoke(cli, ["stats", str(fake_sav)])

        assert "Build_MinerMk1_C: 1" in result.output
        assert "Build_SmelterMk1_C: 1" in result.output

    def test_shows_power_grid(self, runner, fake_sav):
        with patch("satisfactory_ai.cli.parse_save_file", return_value=SAMPLE_FACTORY_DATA):
            result = runner.invoke(cli, ["stats", str(fake_sav)])

        assert "Power Grid" in result.output
        assert "150" in result.output  # totalProduction

    def test_shows_resources_when_present(self, runner, fake_sav):
        with patch("satisfactory_ai.cli.parse_save_file", return_value=SAMPLE_FACTORY_DATA):
            result = runner.invoke(cli, ["stats", str(fake_sav)])

        assert "Iron Ore" in result.output
        assert "500" in result.output

    def test_skips_resources_section_when_empty(self, runner, fake_sav):
        data = {**SAMPLE_FACTORY_DATA, "resources": {}}
        with patch("satisfactory_ai.cli.parse_save_file", return_value=data):
            result = runner.invoke(cli, ["stats", str(fake_sav)])

        assert result.exit_code == 0
        assert "Resources Mined" not in result.output

    def test_skips_per_building_list_when_no_buildings(self, runner, fake_sav):
        data = {**SAMPLE_FACTORY_DATA, "buildings": []}
        with patch("satisfactory_ai.cli.parse_save_file", return_value=data):
            result = runner.invoke(cli, ["stats", str(fake_sav)])

        assert result.exit_code == 0
        assert "Buildings: 0" in result.output

    def test_json_flag_outputs_json(self, runner, fake_sav):
        with patch("satisfactory_ai.cli.parse_save_file", return_value=SAMPLE_FACTORY_DATA):
            result = runner.invoke(cli, ["stats", str(fake_sav), "--json"])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["session"]["name"] == "TestWorld"

    def test_parse_failure_exits_nonzero(self, runner, fake_sav):
        with patch("satisfactory_ai.cli.parse_save_file", return_value=None):
            result = runner.invoke(cli, ["stats", str(fake_sav)])

        assert result.exit_code != 0

    def test_shows_active_milestone(self, runner, fake_sav):
        with patch("satisfactory_ai.cli.parse_save_file", return_value=SAMPLE_FACTORY_DATA):
            result = runner.invoke(cli, ["stats", str(fake_sav)])

        assert "Tier 2" in result.output


# ---------------------------------------------------------------------------
# config command
# ---------------------------------------------------------------------------


class TestConfigCommand:
    def test_no_api_key_shows_error(self, runner, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        result = runner.invoke(cli, ["config"])

        assert result.exit_code == 0
        assert "ANTHROPIC_API_KEY not set" in result.output

    def test_api_key_set_and_accessible(self, runner, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-123")
        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.return_value = MagicMock()
            result = runner.invoke(cli, ["config"])

        assert result.exit_code == 0
        assert "ANTHROPIC_API_KEY is set" in result.output
        assert "Claude API is accessible" in result.output

    def test_api_key_set_but_api_error(self, runner, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "bad-key")
        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.side_effect = Exception("Auth error")
            result = runner.invoke(cli, ["config"])

        assert result.exit_code == 0
        assert "API error" in result.output

    def test_sat_sav_parse_not_found_shows_warning(self, runner, monkeypatch, tmp_path):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        # Point __file__ at a dir that has no sat_sav_parse sibling
        with patch("satisfactory_ai.cli.Path") as mock_path_cls:
            mock_path_cls.return_value.parent.__truediv__.return_value.exists.return_value = False
            result = runner.invoke(cli, ["config"])

        assert result.exit_code == 0
        assert "sat_sav_parse" in result.output

    def test_sat_sav_parse_found_shows_checkmark(self, runner, monkeypatch, tmp_path):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with patch("satisfactory_ai.cli.Path") as mock_path_cls:
            mock_path_cls.return_value.parent.__truediv__.return_value.exists.return_value = True
            result = runner.invoke(cli, ["config"])

        assert result.exit_code == 0
        assert "sat_sav_parse" in result.output

    def test_shows_configuration_header(self, runner, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        result = runner.invoke(cli, ["config"])
        assert "CONFIGURATION" in result.output


# ---------------------------------------------------------------------------
# version command
# ---------------------------------------------------------------------------


class TestVersionCommand:
    def test_shows_version_string(self, runner):
        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0
        assert "satisfactory-ai" in result.output

    def test_mentions_claude(self, runner):
        result = runner.invoke(cli, ["version"])
        assert "Claude" in result.output


# ---------------------------------------------------------------------------
# Top-level help
# ---------------------------------------------------------------------------


class TestCLIHelp:
    def test_help_exits_zero(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0

    def test_analyze_help(self, runner):
        result = runner.invoke(cli, ["analyze", "--help"])
        assert result.exit_code == 0
        assert "--debug" in result.output
        assert "--json" in result.output
        assert "--interactive" in result.output

    def test_stats_help(self, runner):
        result = runner.invoke(cli, ["stats", "--help"])
        assert result.exit_code == 0
        assert "--json" in result.output
