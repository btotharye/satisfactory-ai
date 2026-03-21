"""
Tests for satisfactory_ai.analyze_factory — FactoryAnalyzer and analyze_save_file.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from satisfactory_ai.analyze_factory import DEFAULT_MODEL, FactoryAnalyzer, analyze_save_file

# ---------------------------------------------------------------------------
# Shared fixture data
# ---------------------------------------------------------------------------

SAMPLE_FACTORY_DATA = {
    "session": {
        "name": "TestFactory",
        "playTime": 3600,
        "buildVersion": 480000,
        "gamePhase": 1,
        "activeMilestone": "",
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
        "totalProduction": 0,
        "totalConsumption": 0,
        "storage": 0,
        "batteries": 0,
        "generators": ["Build_GeneratorIntegratedBiomass_C"],
    },
    "resources": {},
    "production": {
        "estimated": True,
        "buildingCounts": {
            "Build_MinerMk1_C": 1,
            "Build_SmelterMk1_C": 1,
        },
    },
    "unlocks": {"milestonesCompleted": 0, "schematicsUnlocked": 0},
}


# ---------------------------------------------------------------------------
# DEFAULT_MODEL constant
# ---------------------------------------------------------------------------


def test_default_model_is_current_sonnet():
    assert DEFAULT_MODEL == "claude-sonnet-4-6"


def test_default_model_does_not_reference_old_date_versioned_model():
    """Ensure we're not accidentally referencing the old claude-3-sonnet-20240229."""
    assert "20240229" not in DEFAULT_MODEL


# ---------------------------------------------------------------------------
# FactoryAnalyzer — instantiation
# ---------------------------------------------------------------------------


class TestFactoryAnalyzerInit:
    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            FactoryAnalyzer()

    def test_accepts_explicit_api_key(self):
        with patch("satisfactory_ai.analyze_factory.Anthropic"):
            analyzer = FactoryAnalyzer(api_key="test-key-123")
        assert analyzer.api_key == "test-key-123"

    def test_reads_api_key_from_env(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key-456")
        with patch("satisfactory_ai.analyze_factory.Anthropic"):
            analyzer = FactoryAnalyzer()
        assert analyzer.api_key == "env-key-456"


# ---------------------------------------------------------------------------
# FactoryAnalyzer — _build_analysis_prompt (static, no API key needed)
# ---------------------------------------------------------------------------


class TestBuildAnalysisPrompt:
    def test_contains_session_name(self):
        prompt = FactoryAnalyzer._build_analysis_prompt(SAMPLE_FACTORY_DATA)
        assert "TestFactory" in prompt

    def test_contains_play_time_in_hours(self):
        prompt = FactoryAnalyzer._build_analysis_prompt(SAMPLE_FACTORY_DATA)
        assert "1.0 hours" in prompt

    def test_contains_building_type_counts(self):
        prompt = FactoryAnalyzer._build_analysis_prompt(SAMPLE_FACTORY_DATA)
        assert "Build_MinerMk1_C" in prompt
        assert "Build_SmelterMk1_C" in prompt

    def test_contains_generator_info(self):
        prompt = FactoryAnalyzer._build_analysis_prompt(SAMPLE_FACTORY_DATA)
        assert "Build_GeneratorIntegratedBiomass_C" in prompt

    def test_returns_non_empty_string(self):
        prompt = FactoryAnalyzer._build_analysis_prompt(SAMPLE_FACTORY_DATA)
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_handles_empty_factory_data(self):
        prompt = FactoryAnalyzer._build_analysis_prompt({})
        assert isinstance(prompt, str)

    def test_no_buildings_shows_none(self):
        data = {**SAMPLE_FACTORY_DATA, "buildings": [], "production": {"buildingCounts": {}}}
        prompt = FactoryAnalyzer._build_analysis_prompt(data)
        assert "(none)" in prompt


# ---------------------------------------------------------------------------
# FactoryAnalyzer — analyze()
# ---------------------------------------------------------------------------


class TestFactoryAnalyzerAnalyze:
    def _make_analyzer(self, response_text: str = "Great factory!") -> FactoryAnalyzer:
        with patch("satisfactory_ai.analyze_factory.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text=response_text)]
            mock_client.messages.create.return_value = mock_response
            analyzer = FactoryAnalyzer(api_key="test-key")
            analyzer._mock_client = mock_client  # stash for assertions
            return analyzer

    def test_returns_response_text(self):
        analyzer = self._make_analyzer("Optimization report here")
        result = analyzer.analyze(SAMPLE_FACTORY_DATA)
        assert result == "Optimization report here"

    def test_uses_default_model_when_env_not_set(self, monkeypatch):
        monkeypatch.delenv("CLAUDE_MODEL", raising=False)
        analyzer = self._make_analyzer()
        analyzer.analyze(SAMPLE_FACTORY_DATA)
        call_kwargs = analyzer._mock_client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == DEFAULT_MODEL

    def test_respects_claude_model_env_var(self, monkeypatch):
        monkeypatch.setenv("CLAUDE_MODEL", "claude-opus-4-6")
        analyzer = self._make_analyzer()
        analyzer.analyze(SAMPLE_FACTORY_DATA)
        call_kwargs = analyzer._mock_client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == "claude-opus-4-6"

    def test_sends_one_message_to_api(self):
        analyzer = self._make_analyzer()
        analyzer.analyze(SAMPLE_FACTORY_DATA)
        analyzer._mock_client.messages.create.assert_called_once()


# ---------------------------------------------------------------------------
# analyze_save_file convenience function
# ---------------------------------------------------------------------------


class TestAnalyzeSaveFile:
    def test_returns_error_string_without_api_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        result = analyze_save_file(SAMPLE_FACTORY_DATA)
        assert "ANTHROPIC_API_KEY" in result

    def test_returns_analysis_string_on_success(self):
        with patch("satisfactory_ai.analyze_factory.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Actionable recommendations")]
            mock_client.messages.create.return_value = mock_response

            result = analyze_save_file(SAMPLE_FACTORY_DATA, interactive=False)

        assert result == "Actionable recommendations"

    def test_handles_unexpected_exception_gracefully(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        with patch("satisfactory_ai.analyze_factory.Anthropic") as mock_cls:
            mock_cls.side_effect = RuntimeError("Network error")
            result = analyze_save_file(SAMPLE_FACTORY_DATA)
        assert "error" in result.lower()
