"""Terrain data access service for loading and querying DEM and catchment zones."""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.models.terrain_models import TerrainZoneModel


class TerrainServiceError(Exception):
    """Base exception for terrain service failures."""
    pass


class TerrainFileNotFoundError(TerrainServiceError):
    """Raised when the requested terrain dataset file cannot be located."""
    pass


class InvalidTerrainDataFormatError(TerrainServiceError):
    """Raised when terrain dataset fails validation or structural requirements."""
    pass


class TerrainService:
    """Service to load, resolve, and query terrain and catchment datasets."""

    def __init__(self, data_file_path: Optional[Path] = None):
        self.data_file_path = data_file_path or self._resolve_default_dataset_path()
        self._cached_data: Optional[Dict[str, Any]] = None

    def _resolve_default_dataset_path(self) -> Path:
        """Locates the demo terrain dataset across project directory roots."""
        candidate_root = Path(__file__).resolve().parent.parent.parent / "data" / "demo_terrain.json"
        if candidate_root.exists():
            return candidate_root

        candidate_backend = Path(__file__).resolve().parent.parent / "data" / "demo_terrain.json"
        if candidate_backend.exists():
            return candidate_backend

        return candidate_root

    def load_dataset(self, force_reload: bool = False) -> Dict[str, Any]:
        """Loads and validates JSON content from the configured terrain dataset."""
        if self._cached_data and not force_reload:
            return self._cached_data

        if not self.data_file_path.exists():
            raise TerrainFileNotFoundError(
                f"Terrain dataset not found at expected path: {self.data_file_path}"
            )

        try:
            with open(self.data_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as err:
            raise InvalidTerrainDataFormatError(f"Corrupted JSON in terrain dataset: {err}") from err
        except Exception as err:
            raise TerrainServiceError(f"Failed to read terrain dataset: {err}") from err

        if not isinstance(data, dict) or "zones" not in data or not isinstance(data["zones"], list):
            raise InvalidTerrainDataFormatError(
                "Terrain data must contain a top-level dictionary with a 'zones' list"
            )

        self._cached_data = data
        return data

    def get_all_zones(self) -> List[TerrainZoneModel]:
        """Retrieves and parses all catchment zones as Pydantic models."""
        data = self.load_dataset()
        zones: List[TerrainZoneModel] = []
        for item in data.get("zones", []):
            zones.append(TerrainZoneModel(**item))
        return zones

    def get_zone_by_id(self, zone_id: str) -> Optional[TerrainZoneModel]:
        """Retrieves an individual zone by its unique identifier."""
        zones = self.get_all_zones()
        for zone in zones:
            if zone.zone_id.lower() == zone_id.lower():
                return zone
        return None

    def get_low_lying_zones(self) -> List[TerrainZoneModel]:
        """Filters zones flagged as low-lying topographical depressions."""
        return [zone for zone in self.get_all_zones() if zone.is_low_lying]


# Global singleton instance
default_terrain_service = TerrainService()
