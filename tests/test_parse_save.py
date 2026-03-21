"""
Tests for satisfactory_ai.parse_save — FactoryDataExtractor and parse_save_file.
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from satisfactory_ai.parse_save import (
    FactoryDataExtractor,
    _convert_save_to_json,
    parse_save_file,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_save_data() -> dict:
    """Load the sample save JSON fixture."""
    with open(FIXTURES_DIR / "sample_save.json") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# FactoryDataExtractor — initialisation
# ---------------------------------------------------------------------------


class TestFactoryDataExtractorInit:
    def test_collects_objects_and_headers_from_all_levels(self, sample_save_data):
        extractor = FactoryDataExtractor(sample_save_data)
        # Fixture has 5 objects in LEVEL_HASH_1 and 0 in LEVEL_HASH_EMPTY
        assert len(extractor.all_headers) == 5
        assert len(extractor.all_objects) == 5

    def test_objects_by_name_index_is_populated(self, sample_save_data):
        extractor = FactoryDataExtractor(sample_save_data)
        assert "Persistent_Level:PersistentLevel.Build_MinerMk1_C_001" in extractor.objects_by_name

    def test_headers_by_name_index_is_populated(self, sample_save_data):
        extractor = FactoryDataExtractor(sample_save_data)
        assert "Persistent_Level:PersistentLevel.Build_SmelterMk1_C_001" in extractor.headers_by_name

    def test_handles_empty_levels_dict(self):
        extractor = FactoryDataExtractor({"saveFileInfo": {}, "levels": {}})
        assert extractor.all_headers == []
        assert extractor.all_objects == []

    def test_handles_levels_as_list(self):
        """Supports an alternative save format where levels is a list."""
        data = {
            "saveFileInfo": {},
            "levels": [
                {
                    "objectHeaders": [
                        {
                            "typePath": "/Game/FactoryGame/Buildable/Factory/MinerMK1/Build_MinerMk1.Build_MinerMk1_C",
                            "instanceName": "test_miner",
                            "position": [0.0, 0.0, 0.0],
                        }
                    ],
                    "objects": [{"instanceName": "test_miner", "properties": []}],
                }
            ],
        }
        extractor = FactoryDataExtractor(data)
        assert len(extractor.all_headers) == 1

    def test_handles_missing_levels_key(self):
        extractor = FactoryDataExtractor({"saveFileInfo": {}})
        assert extractor.all_headers == []


# ---------------------------------------------------------------------------
# FactoryDataExtractor — session info
# ---------------------------------------------------------------------------


class TestExtractSessionInfo:
    def test_reads_session_name(self, sample_save_data):
        session = FactoryDataExtractor(sample_save_data)._extract_session_info()
        assert session["name"] == "TestSession"

    def test_reads_play_time(self, sample_save_data):
        session = FactoryDataExtractor(sample_save_data)._extract_session_info()
        assert session["playTime"] == 3600

    def test_reads_build_version(self, sample_save_data):
        session = FactoryDataExtractor(sample_save_data)._extract_session_info()
        assert session["buildVersion"] == 12345

    def test_falls_back_gracefully_on_missing_save_info(self):
        session = FactoryDataExtractor({})._extract_session_info()
        assert session["name"] == "Unknown"
        assert session["playTime"] == 0


# ---------------------------------------------------------------------------
# FactoryDataExtractor — buildings
# ---------------------------------------------------------------------------


class TestExtractBuildings:
    def test_returns_only_factory_buildings(self, sample_save_data):
        buildings = FactoryDataExtractor(sample_save_data)._extract_buildings()
        types = {b["type"] for b in buildings}
        # SpaceGiraffe is wildlife — must be excluded
        assert "Char_SpaceGiraffe_C" not in types

    def test_includes_miner(self, sample_save_data):
        buildings = FactoryDataExtractor(sample_save_data)._extract_buildings()
        types = {b["type"] for b in buildings}
        assert "Build_MinerMk1_C" in types

    def test_includes_smelter(self, sample_save_data):
        buildings = FactoryDataExtractor(sample_save_data)._extract_buildings()
        types = {b["type"] for b in buildings}
        assert "Build_SmelterMk1_C" in types

    def test_includes_conveyor_belt(self, sample_save_data):
        buildings = FactoryDataExtractor(sample_save_data)._extract_buildings()
        types = {b["type"] for b in buildings}
        assert "Build_ConveyorBeltMk1_C" in types

    def test_building_has_location(self, sample_save_data):
        buildings = FactoryDataExtractor(sample_save_data)._extract_buildings()
        miner = next(b for b in buildings if b["type"] == "Build_MinerMk1_C")
        assert miner["location"] == [100.0, 200.0, 300.0]

    def test_building_has_name(self, sample_save_data):
        buildings = FactoryDataExtractor(sample_save_data)._extract_buildings()
        miner = next(b for b in buildings if b["type"] == "Build_MinerMk1_C")
        assert "Build_MinerMk1_C_001" in miner["name"]

    def test_building_has_type_path(self, sample_save_data):
        buildings = FactoryDataExtractor(sample_save_data)._extract_buildings()
        miner = next(b for b in buildings if b["type"] == "Build_MinerMk1_C")
        assert "/Buildable/" in miner["typePath"]

    def test_returns_empty_list_when_no_objects(self):
        buildings = FactoryDataExtractor({"saveFileInfo": {}, "levels": {}})._extract_buildings()
        assert buildings == []


# ---------------------------------------------------------------------------
# FactoryDataExtractor — power grid
# ---------------------------------------------------------------------------


class TestExtractPowerGrid:
    def test_counts_generators(self, sample_save_data):
        power = FactoryDataExtractor(sample_save_data)._extract_power_grid()
        assert len(power["generators"]) == 1

    def test_generator_type_is_short_class_name(self, sample_save_data):
        power = FactoryDataExtractor(sample_save_data)._extract_power_grid()
        assert "Build_GeneratorIntegratedBiomass_C" in power["generators"]

    def test_batteries_zero_when_none_present(self, sample_save_data):
        power = FactoryDataExtractor(sample_save_data)._extract_power_grid()
        assert power["batteries"] == 0


# ---------------------------------------------------------------------------
# FactoryDataExtractor — production rates
# ---------------------------------------------------------------------------


class TestEstimateProductionRates:
    def test_counts_each_building_type(self, sample_save_data):
        extractor = FactoryDataExtractor(sample_save_data)
        buildings = extractor._extract_buildings()
        rates = extractor._estimate_production_rates(buildings)
        counts = rates["buildingCounts"]
        assert counts.get("Build_MinerMk1_C") == 1
        assert counts.get("Build_SmelterMk1_C") == 1

    def test_estimated_flag_is_true(self, sample_save_data):
        extractor = FactoryDataExtractor(sample_save_data)
        rates = extractor._estimate_production_rates([])
        assert rates["estimated"] is True

    def test_accepts_none_and_re_extracts(self, sample_save_data):
        extractor = FactoryDataExtractor(sample_save_data)
        rates = extractor._estimate_production_rates(None)
        assert "buildingCounts" in rates
        assert len(rates["buildingCounts"]) > 0


# ---------------------------------------------------------------------------
# FactoryDataExtractor — extract_all
# ---------------------------------------------------------------------------


class TestExtractAll:
    def test_returns_all_expected_keys(self, sample_save_data):
        result = FactoryDataExtractor(sample_save_data).extract_all()
        assert set(result.keys()) == {"session", "buildings", "powerGrid", "resources", "production", "unlocks"}

    def test_buildings_not_extracted_twice(self, sample_save_data):
        """_extract_buildings should only be called once per extract_all invocation."""
        extractor = FactoryDataExtractor(sample_save_data)
        original = extractor._extract_buildings

        call_count = {"n": 0}

        def counting_extract():
            call_count["n"] += 1
            return original()

        extractor._extract_buildings = counting_extract  # type: ignore[method-assign]
        extractor.extract_all()
        assert call_count["n"] == 1


# ---------------------------------------------------------------------------
# _is_factory_building static method
# ---------------------------------------------------------------------------


class TestIsFactoryBuilding:
    def test_buildable_path_with_build_prefix(self):
        hdr = {"typePath": "/Game/FactoryGame/Buildable/Factory/MinerMK1/Build_MinerMk1.Build_MinerMk1_C"}
        assert FactoryDataExtractor._is_factory_building(hdr) is True

    def test_non_buildable_wildlife(self):
        hdr = {"typePath": "/Game/FactoryGame/Character/Creature/Wildlife/Char_SpaceGiraffe.Char_SpaceGiraffe_C"}
        assert FactoryDataExtractor._is_factory_building(hdr) is False

    def test_empty_header(self):
        assert FactoryDataExtractor._is_factory_building({}) is False

    def test_non_dict_input(self):
        assert FactoryDataExtractor._is_factory_building("not a dict") is False  # type: ignore[arg-type]

    def test_resource_node_excluded(self):
        hdr = {"typePath": "/Game/FactoryGame/Resource/BP_ResourceNode.BP_ResourceNode_C"}
        assert FactoryDataExtractor._is_factory_building(hdr) is False

    def test_generator_included_via_keyword_fallback(self):
        # Also matches via the /Buildable/ + Build_ path
        hdr = {"typePath": "/Game/FactoryGame/Buildable/Factory/GeneratorBiomass/Build_GeneratorIntegratedBiomass.Build_GeneratorIntegratedBiomass_C"}
        assert FactoryDataExtractor._is_factory_building(hdr) is True


# ---------------------------------------------------------------------------
# parse_save_file — filesystem-level checks (no real .sav needed)
# ---------------------------------------------------------------------------


class TestParseSaveFile:
    def test_missing_file_returns_none(self, tmp_path):
        result = parse_save_file(str(tmp_path / "nonexistent.sav"))
        assert result is None

    def test_wrong_extension_returns_none(self, tmp_path):
        bad_file = tmp_path / "save.txt"
        bad_file.write_text("dummy content")
        result = parse_save_file(str(bad_file))
        assert result is None

    def test_valid_sav_calls_converter(self, tmp_path):
        """If the .sav file exists and the converter succeeds, data is returned."""
        fake_sav = tmp_path / "test.sav"
        fake_sav.write_bytes(b"\x00" * 16)

        minimal_json = {
            "saveFileInfo": {"sessionName": "Test", "playDurationInSeconds": 0, "buildVersion": 0},
            "levels": {},
        }

        with patch("satisfactory_ai.parse_save._convert_save_to_json", return_value=minimal_json):
            result = parse_save_file(str(fake_sav))

        assert result is not None
        assert result["session"]["name"] == "Test"

    def test_converter_failure_returns_none(self, tmp_path):
        fake_sav = tmp_path / "test.sav"
        fake_sav.write_bytes(b"\x00" * 16)

        with patch("satisfactory_ai.parse_save._convert_save_to_json", return_value=None):
            result = parse_save_file(str(fake_sav))

        assert result is None

    def test_debug_mode_prints_levels_summary(self, tmp_path, capsys):
        fake_sav = tmp_path / "test.sav"
        fake_sav.write_bytes(b"\x00" * 16)

        minimal_json = {
            "saveFileInfo": {},
            "levels": {
                "HASH1": {
                    "objects": [{"instanceName": "foo"}],
                    "objectHeaders": [{"instanceName": "foo", "typePath": ""}],
                }
            },
        }
        with patch("satisfactory_ai.parse_save._convert_save_to_json", return_value=minimal_json):
            parse_save_file(str(fake_sav), debug=True)

        captured = capsys.readouterr()
        assert "DEBUG" in captured.err
        assert "Levels:" in captured.err

    def test_debug_mode_flat_objects_fallback(self, tmp_path, capsys):
        """Debug path: levels is a list (not a dict) and a top-level 'objects' key exists."""
        fake_sav = tmp_path / "test.sav"
        fake_sav.write_bytes(b"\x00" * 16)

        # levels must be a non-dict so isinstance(levels, dict) is False,
        # which makes the elif 'objects' in json_data branch reachable.
        flat_json = {
            "saveFileInfo": {},
            "levels": [],  # list, not dict → elif branch fires
            "objects": [{"key": "val"}],
        }
        with patch("satisfactory_ai.parse_save._convert_save_to_json", return_value=flat_json):
            parse_save_file(str(fake_sav), debug=True)

        captured = capsys.readouterr()
        assert "Objects count: 1" in captured.err

    def test_unsupported_version_error_returns_none(self, tmp_path, capsys):
        fake_sav = tmp_path / "test.sav"
        fake_sav.write_bytes(b"\x00" * 16)

        with patch(
            "satisfactory_ai.parse_save._convert_save_to_json",
            side_effect=Exception("Unsupported save header version: 99"),
        ):
            result = parse_save_file(str(fake_sav))

        assert result is None
        captured = capsys.readouterr()
        assert "unsupported Satisfactory version" in captured.err

    def test_generic_exception_returns_none(self, tmp_path, capsys):
        fake_sav = tmp_path / "test.sav"
        fake_sav.write_bytes(b"\x00" * 16)

        with patch(
            "satisfactory_ai.parse_save._convert_save_to_json",
            side_effect=RuntimeError("something broke"),
        ):
            result = parse_save_file(str(fake_sav))

        assert result is None
        captured = capsys.readouterr()
        assert "Error parsing save file" in captured.err


# ---------------------------------------------------------------------------
# _convert_save_to_json
# ---------------------------------------------------------------------------


class TestConvertSaveToJson:
    def _make_sat_sav_path(self, exists: bool, tmp_path: Path) -> Path:
        p = tmp_path / "sat_sav_parse"
        if exists:
            p.mkdir()
            (p / "sav_cli.py").write_text("# stub")
        return p

    def test_submodule_not_found_returns_none(self, tmp_path, capsys):
        # Direct approach: temporarily rename sat_sav_parse or patch __file__
        fake_sav = str(tmp_path / "test.sav")
        with patch("satisfactory_ai.parse_save.Path") as mock_path_cls:
            # Make the sat_sav_path.exists() return False
            instance = MagicMock()
            instance.parent.parent.__truediv__ = MagicMock(return_value=instance)
            instance.exists.return_value = False
            mock_path_cls.return_value = instance
            mock_path_cls.side_effect = None

            # We need __file__ to return a proper path chain
            # Simpler: patch the sat_sav_path directly inside the function
            with patch(
                "satisfactory_ai.parse_save.Path",
                wraps=Path,
            ) as mock_p:
                # Override __file__ parent.parent chain
                orig_path = Path
                call_count = {"n": 0}

                def side_effect(arg):
                    call_count["n"] += 1
                    if call_count["n"] == 1:
                        # This is Path(__file__)
                        m = MagicMock(spec=orig_path)
                        sat = MagicMock()
                        sat.exists.return_value = False
                        m.parent.parent.__truediv__.return_value = sat
                        return m
                    return orig_path(arg)

                mock_p.side_effect = side_effect
                result = _convert_save_to_json(fake_sav)

        assert result is None
        captured = capsys.readouterr()
        assert "sat_sav_parse submodule not found" in captured.err

    def test_subprocess_nonzero_returns_none(self, tmp_path, capsys):
        fake_sav = str(tmp_path / "test.sav")
        with (
            patch("satisfactory_ai.parse_save.Path", wraps=Path) as mock_p,
            patch("satisfactory_ai.parse_save.subprocess.run") as mock_run,
            patch("satisfactory_ai.parse_save.tempfile.NamedTemporaryFile"),
        ):
            orig_path = Path
            call_count = {"n": 0}

            def side_effect(arg):
                call_count["n"] += 1
                if call_count["n"] == 1:
                    m = MagicMock(spec=orig_path)
                    sat = MagicMock()
                    sat.exists.return_value = True
                    m.parent.parent.__truediv__.return_value = sat
                    return m
                return orig_path(arg)

            mock_p.side_effect = side_effect
            mock_run.return_value = MagicMock(returncode=1, stderr="Parser failed")
            result = _convert_save_to_json(fake_sav)

        assert result is None

    def test_timeout_returns_none(self, tmp_path, capsys):
        fake_sav = str(tmp_path / "test.sav")
        with patch("satisfactory_ai.parse_save.subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 60)):
            with patch("satisfactory_ai.parse_save.Path", wraps=Path) as mock_p:
                orig_path = Path
                call_count = {"n": 0}

                def side_effect(arg):
                    call_count["n"] += 1
                    if call_count["n"] == 1:
                        m = MagicMock(spec=orig_path)
                        sat = MagicMock()
                        sat.exists.return_value = True
                        m.parent.parent.__truediv__.return_value = sat
                        return m
                    return orig_path(arg)

                mock_p.side_effect = side_effect
                result = _convert_save_to_json(fake_sav)

        assert result is None
        captured = capsys.readouterr()
        assert "timed out" in captured.err

    def test_json_decode_error_returns_none(self, tmp_path, capsys):
        """Covers the JSONDecodeError except branch."""
        fake_sav = str(tmp_path / "test.sav")
        json_file = tmp_path / "out.json"
        json_file.write_text("not valid json {{")

        with (
            patch("satisfactory_ai.parse_save.subprocess.run", return_value=MagicMock(returncode=0)),
            patch("satisfactory_ai.parse_save.Path", wraps=Path) as mock_p,
        ):
            orig_path = Path
            call_count = {"n": 0}

            def side_effect(arg):
                call_count["n"] += 1
                if call_count["n"] == 1:
                    m = MagicMock(spec=orig_path)
                    sat = MagicMock()
                    sat.exists.return_value = True
                    m.parent.parent.__truediv__.return_value = sat
                    return m
                return orig_path(arg)

            mock_p.side_effect = side_effect

            # Also patch open to return bad JSON
            with patch("builtins.open", side_effect=[
                MagicMock(  # NamedTemporaryFile open — not called directly in new code
                    __enter__=MagicMock(return_value=MagicMock(name=str(json_file))),
                    __exit__=MagicMock(return_value=False),
                )
            ]):
                pass  # can't easily test this path without deeper mocking

        # Test the JSONDecodeError path by patching json.load
        with (
            patch("satisfactory_ai.parse_save.subprocess.run", return_value=MagicMock(returncode=0)),
            patch("satisfactory_ai.parse_save.json.load", side_effect=json.JSONDecodeError("err", "doc", 0)),
            patch("satisfactory_ai.parse_save.Path", wraps=Path) as mock_p2,
        ):
            orig_path2 = Path
            cc2 = {"n": 0}

            def se2(arg):
                cc2["n"] += 1
                if cc2["n"] == 1:
                    m = MagicMock(spec=orig_path2)
                    sat = MagicMock()
                    sat.exists.return_value = True
                    m.parent.parent.__truediv__.return_value = sat
                    return m
                return orig_path2(arg)

            mock_p2.side_effect = se2
            result = _convert_save_to_json(fake_sav)

        assert result is None
        captured = capsys.readouterr()
        assert "Invalid JSON" in captured.err

    def test_generic_exception_returns_none(self, tmp_path, capsys):
        """Covers the generic except branch."""
        fake_sav = str(tmp_path / "test.sav")
        with (
            patch("satisfactory_ai.parse_save.subprocess.run", side_effect=OSError("disk full")),
            patch("satisfactory_ai.parse_save.Path", wraps=Path) as mock_p,
        ):
            orig_path = Path
            call_count = {"n": 0}

            def side_effect(arg):
                call_count["n"] += 1
                if call_count["n"] == 1:
                    m = MagicMock(spec=orig_path)
                    sat = MagicMock()
                    sat.exists.return_value = True
                    m.parent.parent.__truediv__.return_value = sat
                    return m
                return orig_path(arg)

            mock_p.side_effect = side_effect
            result = _convert_save_to_json(fake_sav)

        assert result is None
        captured = capsys.readouterr()
        assert "Error converting save to JSON" in captured.err


# ---------------------------------------------------------------------------
# FactoryDataExtractor — debug mode
# ---------------------------------------------------------------------------


class TestFactoryDataExtractorDebug:
    def test_debug_prints_object_count(self, sample_save_data, capsys):
        FactoryDataExtractor(sample_save_data, debug=True)
        captured = capsys.readouterr()
        assert "Pre-collected" in captured.err
        assert "5" in captured.err

    def test_debug_extract_buildings_prints_checking(self, sample_save_data, capsys):
        extractor = FactoryDataExtractor(sample_save_data, debug=True)
        capsys.readouterr()  # discard init output
        extractor._extract_buildings()
        captured = capsys.readouterr()
        assert "Checking" in captured.err
        assert "Extracted" in captured.err

    def test_debug_no_objects_prints_warning(self, capsys):
        extractor = FactoryDataExtractor({"saveFileInfo": {}, "levels": {}}, debug=True)
        capsys.readouterr()  # discard init output
        extractor._extract_buildings()
        captured = capsys.readouterr()
        assert "Warning: No objects found" in captured.err


# ---------------------------------------------------------------------------
# FactoryDataExtractor — exception paths
# ---------------------------------------------------------------------------


class TestFactoryDataExtractorExceptionPaths:
    def test_buildings_exception_without_debug_prints_warning(self, sample_save_data, capsys):
        extractor = FactoryDataExtractor(sample_save_data, debug=False)
        # Force an exception by making all_headers contain a bad item that will
        # raise inside _is_factory_building via a broken __contains__ on typePath
        bad_hdr = MagicMock(spec=dict)
        bad_hdr.__contains__ = MagicMock(side_effect=RuntimeError("boom"))
        bad_hdr.get.side_effect = RuntimeError("boom")
        extractor.all_headers = [bad_hdr]

        result = extractor._extract_buildings()
        assert result == []
        captured = capsys.readouterr()
        assert "Warning: Could not extract buildings" in captured.err

    def test_buildings_exception_with_debug_prints_traceback(self, sample_save_data, capsys):
        extractor = FactoryDataExtractor(sample_save_data, debug=True)
        bad_hdr = MagicMock(spec=dict)
        bad_hdr.get.side_effect = RuntimeError("debug boom")
        extractor.all_headers = [bad_hdr]

        result = extractor._extract_buildings()
        assert result == []
        captured = capsys.readouterr()
        assert "Warning: Could not extract buildings" in captured.err


# ---------------------------------------------------------------------------
# FactoryDataExtractor — resources extraction branches
# ---------------------------------------------------------------------------


class TestExtractResources:
    def test_reads_mined_resources(self, sample_save_data):
        sample_save_data["minedResources"] = {"Iron Ore": 999}
        resources = FactoryDataExtractor(sample_save_data)._extract_resources()
        assert resources == {"Iron Ore": 999}

    def test_reads_resources_key_as_fallback(self):
        data = {"saveFileInfo": {}, "levels": {}, "resources": {"Copper Ore": 50}}
        resources = FactoryDataExtractor(data)._extract_resources()
        assert resources == {"Copper Ore": 50}

    def test_reads_resource_counts_as_second_fallback(self):
        data = {"saveFileInfo": {}, "levels": {}, "resourceCounts": {"Coal": 300}}
        resources = FactoryDataExtractor(data)._extract_resources()
        assert resources == {"Coal": 300}

    def test_returns_empty_dict_when_no_resource_keys(self):
        resources = FactoryDataExtractor({"saveFileInfo": {}, "levels": {}})._extract_resources()
        assert resources == {}

    def test_mined_resources_takes_priority_over_resources_key(self):
        data = {
            "saveFileInfo": {},
            "levels": {},
            "minedResources": {"Iron Ore": 100},
            "resources": {"Iron Ore": 999},
        }
        resources = FactoryDataExtractor(data)._extract_resources()
        assert resources["Iron Ore"] == 100


# ---------------------------------------------------------------------------
# FactoryDataExtractor — unlocks
# ---------------------------------------------------------------------------


class TestExtractUnlocks:
    def test_counts_milestones(self):
        data = {"saveFileInfo": {}, "levels": {}, "milestones": ["a", "b", "c"]}
        unlocks = FactoryDataExtractor(data)._extract_unlocks()
        assert unlocks["milestonesCompleted"] == 3

    def test_counts_schematics(self):
        data = {"saveFileInfo": {}, "levels": {}, "schematics": ["x", "y"]}
        unlocks = FactoryDataExtractor(data)._extract_unlocks()
        assert unlocks["schematicsUnlocked"] == 2

    def test_zero_when_no_unlocks_keys(self):
        unlocks = FactoryDataExtractor({"saveFileInfo": {}, "levels": {}})._extract_unlocks()
        assert unlocks["milestonesCompleted"] == 0
        assert unlocks["schematicsUnlocked"] == 0
