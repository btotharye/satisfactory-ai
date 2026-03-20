"""
Parse Satisfactory save files and extract factory data.

Uses sat_sav_parse library to handle binary Unreal Engine format.
Extracts: buildings, power grid, resources, production rates, etc.
"""

import json
import sys
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
        # Import sat_sav_parse from submodule
        import sys
        from pathlib import Path as PathlibPath
        
        # Add sat_sav_parse to path
        sat_sav_path = PathlibPath(__file__).parent.parent / "sat_sav_parse"
        if sat_sav_path.exists():
            sys.path.insert(0, str(sat_sav_path))
        
        import sav_parse
        
        print(f"Parsing save file: {save_path}", file=sys.stderr)
        
        # Parse the save file
        parsed = sav_parse.readFullSaveFile(str(save_file))
        
        # Extract factory data
        extractor = FactoryDataExtractor(parsed)
        return extractor.extract_all()
    
    except ImportError as e:
        print(f"Error: Could not import sat_sav_parse. Make sure submodule is initialized:", file=sys.stderr)
        print(f"  git submodule update --init --recursive", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error parsing save file: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return None


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
            "batteries": 0,
            "generators": []
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
        # sat_sav_parse.ParsedSave has these attributes
        return {
            "name": getattr(self.save, 'sessionName', 'Unknown'),
            "playTime": getattr(self.save, 'playTime', 0),
            "saveDate": str(getattr(self.save, 'saveDate', '')),
            "gamePhase": getattr(self.save, 'gamePhase', 0),
            "activeMilestone": getattr(self.save, 'activeMilestone', '')
        }
    
    def _extract_buildings(self) -> List[Dict[str, Any]]:
        """
        Extract all constructed buildings.
        
        Returns buildings with type, location, and operational status.
        """
        buildings = []
        
        try:
            if hasattr(self.save, 'objects') and self.save.objects:
                for obj in self.save.objects:
                    if self._is_factory_building(obj):
                        building_data = {
                            "type": getattr(obj, 'className', 'Unknown'),
                            "location": self._extract_location(obj),
                            "name": getattr(obj, 'pathName', ''),
                        }
                        buildings.append(building_data)
        except Exception as e:
            print(f"Warning: Could not extract buildings: {e}", file=sys.stderr)
        
        return buildings
    
    def _extract_power_grid(self) -> Dict[str, Any]:
        """Extract power grid stats."""
        try:
            # Count power producers and consumers
            power_data = {
                "totalProduction": 0,
                "totalConsumption": 0,
                "storage": 0,
                "batteries": 0,
                "generators": []
            }
            
            # This would sum up all power generators and consumers from objects
            # For now, return structure with counts from buildings
            if hasattr(self.save, 'objects') and self.save.objects:
                for obj in self.save.objects:
                    obj_type = getattr(obj, 'className', '')
                    
                    # Count generators
                    if 'Generator' in obj_type or 'Coal' in obj_type:
                        power_data['generators'].append(obj_type)
                    
                    # Count batteries
                    if 'Battery' in obj_type:
                        power_data['batteries'] += 1
            
            return power_data
        except Exception as e:
            print(f"Warning: Could not extract power grid: {e}", file=sys.stderr)
            return self.power_grid
    
    def _extract_resources(self) -> Dict[str, int]:
        """Extract mined/collected resource counts."""
        resources = {}
        
        try:
            # sat_sav_parse provides resource counts
            if hasattr(self.save, 'minedResources'):
                resources = self.save.minedResources
            elif hasattr(self.save, 'resourceCounts'):
                resources = self.save.resourceCounts
            
            # Fallback: try individual attributes
            if not resources:
                resources = {
                    "ironOre": getattr(self.save, 'ironOreCount', 0),
                    "copperOre": getattr(self.save, 'copperOreCount', 0),
                    "limestone": getattr(self.save, 'limestoneCount', 0),
                    "coal": getattr(self.save, 'coalCount', 0),
                }
        except Exception as e:
            print(f"Warning: Could not extract resources: {e}", file=sys.stderr)
        
        return resources
    
    def _estimate_production_rates(self) -> Dict[str, Any]:
        """Estimate production rates based on building counts."""
        # Analyze buildings to estimate throughput
        rates = {
            "estimated": True,
            "buildingCounts": {}
        }
        
        try:
            # Count each building type
            for building in self.buildings:
                btype = building.get('type', 'Unknown')
                rates['buildingCounts'][btype] = rates['buildingCounts'].get(btype, 0) + 1
        except Exception as e:
            print(f"Warning: Could not estimate production rates: {e}", file=sys.stderr)
        
        return rates
    
    def _extract_unlocks(self) -> Dict[str, Any]:
        """Extract tech tree unlocks and milestones."""
        return {
            "milestonesCompleted": len(getattr(self.save, 'milestones', [])),
            "schematicsUnlocked": len(getattr(self.save, 'schematics', []))
        }
    
    @staticmethod
    def _is_factory_building(obj: Any) -> bool:
        """Check if object is a factory building (not just terrain/decorations)."""
        factory_types = [
            'Smelter', 'Assembler', 'Foundry',
            'Miner', 'Extractor',
            'Storage', 'Container',
            'Conveyor', 'Merger', 'Splitter',
            'Generator', 'Battery',
            'PowerPole', 'PowerLine',
            'Pump', 'Distributor',
            'Refinery'
        ]
        
        obj_type = getattr(obj, 'className', '')
        return any(factory_type in obj_type for factory_type in factory_types)
    
    @staticmethod
    def _extract_location(obj: Any) -> List[float]:
        """Extract X, Y, Z coordinates from object."""
        try:
            if hasattr(obj, 'location'):
                loc = obj.location
                if isinstance(loc, dict):
                    return [loc.get('x', 0), loc.get('y', 0), loc.get('z', 0)]
                elif hasattr(loc, 'x'):
                    return [loc.x, loc.y, loc.z]
        except Exception:
            pass
        return [0, 0, 0]


if __name__ == "__main__":
    if len(sys.argv) > 1:
        data = parse_save_file(sys.argv[1])
        if data:
            print(json.dumps(data, indent=2))
        else:
            sys.exit(1)
