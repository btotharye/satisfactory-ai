"""
Parse Satisfactory save files and extract factory data.

Uses sat_sav_parse library to handle binary Unreal Engine format.
Converts to JSON then extracts: buildings, power grid, resources, production rates, etc.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional


def parse_save_file(save_path: str, debug: bool = False) -> Optional[Dict[str, Any]]:
    """
    Parse a Satisfactory save file and extract factory data.

    Args:
        save_path: Path to .sav file
        debug: If True, print detailed debug info

    Returns:
        Dictionary with factory data, or None if parsing fails
    """
    save_file = Path(save_path)

    if not save_file.exists():
        print(f"Error: Save file not found: {save_path}", file=sys.stderr)
        return None

    if not save_file.suffix == '.sav':
        print(f"Error: File must be a .sav file, got: {save_file.suffix}", file=sys.stderr)
        return None

    try:
        print(f"Parsing save file: {save_path}", file=sys.stderr)

        # Convert save to JSON using sat_sav_parse CLI
        json_data = _convert_save_to_json(str(save_file))

        if not json_data:
            return None

        if debug:
            print("\n=== DEBUG: JSON Structure ===", file=sys.stderr)
            print(f"Top-level keys: {list(json_data.keys())}", file=sys.stderr)
            levels = json_data.get('levels', {})
            if isinstance(levels, dict):
                total_objs = sum(len(lvl.get('objects', [])) for lvl in levels.values() if isinstance(lvl, dict))
                non_empty = sum(1 for lvl in levels.values() if isinstance(lvl, dict) and lvl.get('objects'))
                print(f"Levels: {len(levels)} total ({non_empty} with objects, {total_objs} total objects)", file=sys.stderr)
            elif 'objects' in json_data:
                print(f"Objects count: {len(json_data['objects'])}", file=sys.stderr)
                if json_data['objects']:
                    print(f"First object keys: {list(json_data['objects'][0].keys())}", file=sys.stderr)

        # Extract factory data from JSON
        extractor = FactoryDataExtractor(json_data, debug=debug)
        return extractor.extract_all()

    except Exception as e:
        error_msg = str(e)

        # Check for version errors
        if "Unsupported save header version" in error_msg:
            print("Error: Your save file is from an unsupported Satisfactory version.", file=sys.stderr)
            print(f"Details: {error_msg}", file=sys.stderr)
            print("\nSupported versions: Satisfactory 1.1.0 and later (1.1.x, 1.2.x)", file=sys.stderr)
            print("Your save appears to be from an older version.", file=sys.stderr)
            return None

        print(f"Error parsing save file: {e}", file=sys.stderr)
        return None


def _convert_save_to_json(save_path: str) -> Optional[Dict[str, Any]]:
    """
    Convert Satisfactory save file to JSON using sat_sav_parse CLI.

    Args:
        save_path: Path to .sav file

    Returns:
        Parsed JSON data, or None if conversion fails
    """
    try:
        # Get path to sat_sav_parse submodule
        sat_sav_path = Path(__file__).parent.parent / "sat_sav_parse"

        if not sat_sav_path.exists():
            print("Error: sat_sav_parse submodule not found.", file=sys.stderr)
            print("Run: git submodule update --init --recursive", file=sys.stderr)
            return None

        # Create temp file for JSON output
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            json_output_path = tmp.name

        # Run sav_cli.py --to-json
        cmd = [
            "python3",
            str(sat_sav_path / "sav_cli.py"),
            "--to-json",
            save_path,
            json_output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            print(f"Error running sat_sav_parse: {result.stderr}", file=sys.stderr)
            return None

        # Read and parse JSON
        with open(json_output_path, 'r') as f:
            data: Dict[str, Any] = json.load(f)

        # Cleanup temp file
        Path(json_output_path).unlink()

        return data

    except subprocess.TimeoutExpired:
        print("Error: Save file parsing timed out (>60 seconds)", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON from parser: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error converting save to JSON: {e}", file=sys.stderr)
        return None


class FactoryDataExtractor:
    """Extract relevant factory data from Satisfactory save JSON."""

    def __init__(self, json_data: Dict[str, Any], debug: bool = False):
        """
        Initialize with parsed save JSON data.

        Args:
            json_data: JSON structure from sav_cli.py --to-json
            debug: If True, print debug info
        """
        self.data = json_data
        self.debug = debug

        # Pre-collect all objects and headers from all levels.
        # The save format stores data in data['levels'][hash]['objects'] and
        # data['levels'][hash]['objectHeaders'] rather than a flat list.
        self.all_objects: List[Dict[str, Any]] = []
        self.all_headers: List[Dict[str, Any]] = []
        self.objects_by_name: Dict[str, Dict[str, Any]] = {}
        self.headers_by_name: Dict[str, Dict[str, Any]] = {}

        levels = json_data.get('levels', {})
        level_values = levels.values() if isinstance(levels, dict) else (levels if isinstance(levels, list) else [])

        for lvl in level_values:
            if not isinstance(lvl, dict):
                continue
            for obj in lvl.get('objects', []):
                self.all_objects.append(obj)
                name = obj.get('instanceName', '')
                if name:
                    self.objects_by_name[name] = obj
            for hdr in lvl.get('objectHeaders', []):
                self.all_headers.append(hdr)
                name = hdr.get('instanceName', '')
                if name:
                    self.headers_by_name[name] = hdr

        if self.debug:
            print(f"Pre-collected {len(self.all_headers)} objects from {len(list(level_values))} levels", file=sys.stderr)

    def extract_all(self) -> Dict[str, Any]:
        """Extract all factory data from JSON."""
        buildings = self._extract_buildings()
        return {
            "session": self._extract_session_info(),
            "buildings": buildings,
            "powerGrid": self._extract_power_grid(),
            "resources": self._extract_resources(),
            "production": self._estimate_production_rates(buildings),
            "unlocks": self._extract_unlocks(),
        }

    def _extract_session_info(self) -> Dict[str, Any]:
        """Extract session metadata."""
        # Session info is stored in saveFileInfo in the current save format
        save_info = self.data.get('saveFileInfo', {})
        return {
            "name": save_info.get('sessionName', self.data.get('sessionName', 'Unknown')),
            "playTime": save_info.get('playDurationInSeconds', self.data.get('playTime', 0)),
            "saveDate": save_info.get('saveDatetime', self.data.get('saveDate', '')),
            "buildVersion": save_info.get('buildVersion', 0),
            "gamePhase": self.data.get('gamePhase', 0),
            "activeMilestone": self.data.get('activeMilestone', '')
        }

    def _extract_buildings(self) -> List[Dict[str, Any]]:
        """Extract all player-built factory buildings from object headers."""
        buildings: List[Dict[str, Any]] = []

        try:
            if not self.all_headers:
                if self.debug:
                    print("Warning: No objects found in save data", file=sys.stderr)
                return buildings

            if self.debug:
                print(f"Checking {len(self.all_headers)} objects for factory buildings", file=sys.stderr)

            for hdr in self.all_headers:
                if self._is_factory_building(hdr):
                    type_path = hdr.get('typePath', 'Unknown')
                    # Short class name: last segment after the dot, e.g. "Build_MinerMk1_C"
                    short_type = type_path.split('.')[-1] if '.' in type_path else type_path.split('/')[-1]
                    pos = hdr.get('position') or [0, 0, 0]
                    building_data = {
                        "type": short_type,
                        "typePath": type_path,
                        "location": [
                            pos[0] if len(pos) > 0 else 0,
                            pos[1] if len(pos) > 1 else 0,
                            pos[2] if len(pos) > 2 else 0,
                        ],
                        "name": hdr.get('instanceName', ''),
                    }
                    buildings.append(building_data)

            if self.debug:
                print(f"Extracted {len(buildings)} factory buildings", file=sys.stderr)

        except Exception as e:
            print(f"Warning: Could not extract buildings: {e}", file=sys.stderr)
            if self.debug:
                import traceback
                traceback.print_exc(file=sys.stderr)

        return buildings

    def _extract_power_grid(self) -> Dict[str, Any]:
        """Extract power grid stats."""
        power_data: Dict[str, Any] = {
            "totalProduction": 0,
            "totalConsumption": 0,
            "storage": 0,
            "batteries": 0,
            "generators": [],
        }

        try:
            for hdr in self.all_headers:
                type_path = hdr.get('typePath', '')
                short_type = type_path.split('.')[-1] if '.' in type_path else type_path.split('/')[-1]

                # Count generators (biomass, coal, fuel, nuclear, etc.)
                if 'Generator' in type_path:
                    power_data['generators'].append(short_type)

                # Count batteries
                if 'Battery' in type_path or 'PowerStorage' in type_path:
                    power_data['batteries'] += 1

        except Exception as e:
            print(f"Warning: Could not extract power grid: {e}", file=sys.stderr)

        return power_data

    def _extract_resources(self) -> Dict[str, int]:
        """Extract mined/collected resource counts."""
        resources = {}

        try:
            # Resources might be in top-level or in a structure
            if 'minedResources' in self.data:
                resources = self.data['minedResources']
            elif 'resources' in self.data:
                resources = self.data['resources']
            elif 'resourceCounts' in self.data:
                resources = self.data['resourceCounts']

        except Exception as e:
            print(f"Warning: Could not extract resources: {e}", file=sys.stderr)

        return resources

    def _estimate_production_rates(
        self, buildings: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Summarise production rates as building-type counts.

        Args:
            buildings: Pre-computed building list. If omitted the buildings are
                       re-extracted (useful when calling this method in isolation).
        """
        rates: Dict[str, Any] = {
            "estimated": True,
            "buildingCounts": {},
        }
        try:
            for building in (buildings if buildings is not None else self._extract_buildings()):
                btype = building.get("type", "Unknown")
                rates["buildingCounts"][btype] = rates["buildingCounts"].get(btype, 0) + 1
        except Exception as e:
            print(f"Warning: Could not estimate production rates: {e}", file=sys.stderr)
        return rates

    def _extract_unlocks(self) -> Dict[str, Any]:
        """Extract tech tree unlocks and milestones."""
        return {
            "milestonesCompleted": len(self.data.get('milestones', [])),
            "schematicsUnlocked": len(self.data.get('schematics', []))
        }

    @staticmethod
    def _is_factory_building(hdr: Dict[str, Any]) -> bool:
        """Check if a header's typePath represents a player-built factory building.

        All buildable factory objects in Satisfactory use the Build_ prefix
        and live under the /Buildable/ path segment.
        """
        if not isinstance(hdr, dict):
            return False

        type_path = hdr.get('typePath', '')
        # All player-placed buildings are under /Buildable/ and have Build_ in the name
        if '/Buildable/' in type_path and 'Build_' in type_path:
            return True
        # Fallback keyword check for any edge cases
        factory_keywords = [
            'Smelter', 'Assembler', 'Foundry',
            'MinerMk', 'OilPump', 'WaterExtractor',
            'Constructor', 'Manufacturer', 'Refinery',
            'Packager', 'Blender', 'HadronCollider',
            'Generator', 'PowerStorage',
        ]
        return any(kw in type_path for kw in factory_keywords)


if __name__ == "__main__":
    import sys
    debug_mode = '--debug' in sys.argv
    save_file = sys.argv[1] if len(sys.argv) > 1 else None

    if save_file and save_file != '--debug':
        data = parse_save_file(save_file, debug=debug_mode)
        if data:
            print(json.dumps(data, indent=2))
        else:
            sys.exit(1)
    else:
        print("Usage: python parse_save.py <save-file> [--debug]")
        sys.exit(1)
