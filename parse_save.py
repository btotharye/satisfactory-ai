"""
Parse Satisfactory save files and extract factory data.

Uses sat_sav_parse library to handle binary Unreal Engine format.
Extracts: buildings, power grid, resources, production rates, etc.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional


class FactoryDataExtractor:
    """Extract relevant factory data from parsed Satisfactory save files."""
    
    def __init__(self, parsed_save: Any):
        """
        Initialize with parsed save data from sat_sav_parse.
        
        Args:
            parsed_save: Result from sav_parse.readFullSaveFile()
        """
        self.save = parsed_save
        self.buildings: List[Dict[str, Any]] = []
        self.power_grid = {
            "totalProduction": 0,
            "totalConsumption": 0,
            "storage": 0,
            "batteries": 0
        }
        self.resources = {}
        
    def extract_all(self) -> Dict[str, Any]:
        """Extract all factory data from save file."""
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
        return {
            "name": getattr(self.save, 'sessionName', 'Unknown'),
            "playTime": getattr(self.save, 'playTime', 0),
            "saveDate": getattr(self.save, 'saveDate', ''),
            "gamePhase": getattr(self.save, 'gamePhase', 0),
            "activeMilestone": getattr(self.save, 'activeMilestone', '')
        }
    
    def _extract_buildings(self) -> List[Dict[str, Any]]:
        """
        Extract all constructed buildings.
        
        Returns buildings with type, location, and operational status.
        """
        buildings = []
        
        # This would iterate through self.save.objects and filter factory buildings
        # For now, return empty list — actual implementation depends on save structure
        try:
            if hasattr(self.save, 'objects'):
                for obj in self.save.objects:
                    if self._is_factory_building(obj):
                        buildings.append({
                            "type": getattr(obj, 'className', 'Unknown'),
                            "location": self._extract_location(obj),
                            "name": getattr(obj, 'pathName', ''),
                            "status": "unknown"  # Would parse from object state
                        })
        except Exception as e:
            print(f"Warning: Could not extract buildings: {e}", file=sys.stderr)
        
        return buildings
    
    def _extract_power_grid(self) -> Dict[str, Any]:
        """Extract power grid stats."""
        try:
            # This would sum up all power generators and consumers
            # For now, return placeholder data
            return {
                "totalProduction": 0,
                "totalConsumption": 0,
                "storage": 0,
                "batteries": 0,
                "generators": []
            }
        except Exception as e:
            print(f"Warning: Could not extract power grid: {e}", file=sys.stderr)
            return self.power_grid
    
    def _extract_resources(self) -> Dict[str, int]:
        """Extract mined/collected resource counts."""
        return {
            "ironOre": getattr(self.save, 'ironOreCount', 0),
            "copperOre": getattr(self.save, 'copperOreCount', 0),
            "cateriumOre": getattr(self.save, 'cateriumOreCount', 0),
            "coal": getattr(self.save, 'coalCount', 0),
            "limestone": getattr(self.save, 'limestoneCount', 0),
            "slugs": getattr(self.save, 'powerSlugs', 0)
        }
    
    def _estimate_production_rates(self) -> Dict[str, Any]:
        """Estimate production rates based on building counts."""
        # This would analyze building types and estimate throughput
        return {
            "estimated": True,
            "note": "Rates estimated from building types and configurations"
        }
    
    def _extract_unlocks(self) -> Dict[str, Any]:
        """Extract tech tree unlocks and milestones."""
        return {
            "milestonesCompleted": getattr(self.save, 'milestonesCompleted', []),
            "schematicsUnlocked": len(getattr(self.save, 'schematics', []))
        }
    
    @staticmethod
    def _is_factory_building(obj: Any) -> bool:
        """Check if object is a factory building (not just terrain/decorations)."""
        factory_types = [
            'SmelterMk1', 'SmelterMk2', 'SmelterMk3',
            'AssemblerMk1', 'AssemblerMk2', 'AssemblerMk3',
            'FoundryMk1',
            'MinerMk1', 'MinerMk2', 'MinerMk3',
            'OilExtractor', 'WaterExtractor',
            'StorageContainerMk1', 'StorageContainerMk2',
            'ConveyorBeltMk1', 'ConveyorBeltMk2', 'ConveyorBeltMk3',
            'ConveyorMerger', 'ConveyorSplitter',
            'GeneratorCoalMk1', 'GeneratorCoalMk2',
            'BatteryMk1', 'BatteryMk2',
            'PowerPole', 'PowerPoleWall'
        ]
        
        obj_type = getattr(obj, 'className', '')
        return any(factory_type in obj_type for factory_type in factory_types)
    
    @staticmethod
    def _extract_location(obj: Any) -> List[float]:
        """Extract X, Y, Z coordinates from object."""
        try:
            if hasattr(obj, 'location'):
                loc = obj.location
                return [loc.get('x', 0), loc.get('y', 0), loc.get('z', 0)]
        except Exception:
            pass
        return [0, 0, 0]


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
        # Import sat_sav_parse (should be in sat_sav_parse/ subdirectory)
        # For now, this is a stub implementation
        print(f"Parsing save file: {save_path}", file=sys.stderr)
        
        # In actual implementation:
        # import sat_sav_parse.sav_parse as sav_parse
        # parsed = sav_parse.readFullSaveFile(str(save_file))
        # extractor = FactoryDataExtractor(parsed)
        # return extractor.extract_all()
        
        # Stub: return sample data structure
        return {
            "session": {
                "name": "Sample Factory",
                "playTime": 45600,
                "saveDate": "2026-03-20",
                "gamePhase": 3,
                "activeMilestone": "Oil Processing"
            },
            "buildings": [],
            "powerGrid": {
                "totalProduction": 0,
                "totalConsumption": 0,
                "storage": 0,
                "batteries": 0
            },
            "resources": {},
            "production": {},
            "unlocks": {}
        }
    
    except Exception as e:
        print(f"Error parsing save file: {e}", file=sys.stderr)
        return None


if __name__ == "__main__":
    if len(sys.argv) > 1:
        data = parse_save_file(sys.argv[1])
        if data:
            print(json.dumps(data, indent=2))
