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
from typing import Dict, List, Any, Optional


def parse_save_file(save_path: str) -> Optional[Dict[str, Any]]:
    """
    Parse a Satisfactory save file and extract factory data.
    
    Args:
        save_path: Path to .sav file
        
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
        
        # Extract factory data from JSON
        extractor = FactoryDataExtractor(json_data)
        return extractor.extract_all()
    
    except Exception as e:
        error_msg = str(e)
        
        # Check for version errors
        if "Unsupported save header version" in error_msg:
            print(f"Error: Your save file is from an unsupported Satisfactory version.", file=sys.stderr)
            print(f"Details: {error_msg}", file=sys.stderr)
            print(f"\nSupported versions: Satisfactory 1.1.0 and later (1.1.x, 1.2.x)", file=sys.stderr)
            print(f"Your save appears to be from an older version.", file=sys.stderr)
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
            print(f"Error: sat_sav_parse submodule not found.", file=sys.stderr)
            print(f"Run: git submodule update --init --recursive", file=sys.stderr)
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
            data = json.load(f)
        
        # Cleanup temp file
        Path(json_output_path).unlink()
        
        return data
    
    except subprocess.TimeoutExpired:
        print(f"Error: Save file parsing timed out (>60 seconds)", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON from parser: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error converting save to JSON: {e}", file=sys.stderr)
        return None


class FactoryDataExtractor:
    """Extract relevant factory data from Satisfactory save JSON."""
    
    def __init__(self, json_data: Dict[str, Any]):
        """
        Initialize with parsed save JSON data.
        
        Args:
            json_data: JSON structure from sav_cli.py --to-json
        """
        self.data = json_data
    
    def extract_all(self) -> Dict[str, Any]:
        """Extract all factory data from JSON."""
        return {
            "session": self._extract_session_info(),
            "buildings": self._extract_buildings(),
            "powerGrid": self._extract_power_grid(),
            "resources": self._extract_resources(),
            "production": self._estimate_production_rates(),
            "unlocks": self._extract_unlocks()
        }
    
    def _extract_session_info(self) -> Dict[str, Any]:
        """Extract session metadata."""
        # Top-level save metadata
        return {
            "name": self.data.get('sessionName', 'Unknown'),
            "playTime": self.data.get('playTime', 0),
            "saveDate": self.data.get('saveDate', ''),
            "gamePhase": self.data.get('gamePhase', 0),
            "activeMilestone": self.data.get('activeMilestone', '')
        }
    
    def _extract_buildings(self) -> List[Dict[str, Any]]:
        """Extract all constructed buildings from objects."""
        buildings = []
        
        try:
            # Building data is in 'objects' list
            objects = self.data.get('objects', [])
            
            for obj in objects:
                if self._is_factory_building(obj):
                    building_data = {
                        "type": obj.get('className', 'Unknown'),
                        "location": [
                            obj.get('location', {}).get('x', 0),
                            obj.get('location', {}).get('y', 0),
                            obj.get('location', {}).get('z', 0)
                        ],
                        "name": obj.get('pathName', ''),
                    }
                    buildings.append(building_data)
        except Exception as e:
            print(f"Warning: Could not extract buildings: {e}", file=sys.stderr)
        
        return buildings
    
    def _extract_power_grid(self) -> Dict[str, Any]:
        """Extract power grid stats."""
        power_data = {
            "totalProduction": 0,
            "totalConsumption": 0,
            "storage": 0,
            "batteries": 0,
            "generators": []
        }
        
        try:
            objects = self.data.get('objects', [])
            
            for obj in objects:
                obj_type = obj.get('className', '')
                
                # Count generators
                if 'Generator' in obj_type or 'Coal' in obj_type:
                    power_data['generators'].append(obj_type)
                
                # Count batteries
                if 'Battery' in obj_type:
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
        
        except Exception as e:
            print(f"Warning: Could not extract resources: {e}", file=sys.stderr)
        
        return resources
    
    def _estimate_production_rates(self) -> Dict[str, Any]:
        """Estimate production rates based on building counts."""
        rates = {
            "estimated": True,
            "buildingCounts": {}
        }
        
        try:
            # Count each building type
            for building in self._extract_buildings():
                btype = building.get('type', 'Unknown')
                rates['buildingCounts'][btype] = rates['buildingCounts'].get(btype, 0) + 1
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
    def _is_factory_building(obj: Dict[str, Any]) -> bool:
        """Check if object is a factory building."""
        factory_types = [
            'Smelter', 'Assembler', 'Foundry',
            'Miner', 'Extractor', 'Pump',
            'Storage', 'Container', 'Chest',
            'Conveyor', 'Merger', 'Splitter',
            'Generator', 'Battery', 'PowerBank',
            'PowerPole', 'PowerLine', 'Wire',
            'Distributor', 'Refinery', 'Constructor'
        ]
        
        obj_type = obj.get('className', '')
        return any(factory_type in obj_type for factory_type in factory_types)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        data = parse_save_file(sys.argv[1])
        if data:
            print(json.dumps(data, indent=2))
        else:
            sys.exit(1)
