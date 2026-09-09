"""Rainfall data access service for loading and caching rainfall datasets."""
import json
from pathlib import Path
from typing import Any, Dict, Optional


class RainfallServiceError(Exception):
    """Base exception for rainfall service failures."""
    pass


class RainfallFileNotFoundError(RainfallServiceError):
    """Raised when the requested rainfall data file cannot be located."""
    pass


class InvalidRainfallDataFormatError(RainfallServiceError):
    """Raised when rainfall data payload fails structural or validation checks."""
    pass


class RainfallService:
    """Service to load, resolve, and manage rainfall datasets."""

    def __init__(self, data_file_path: Optional[Path] = None):
        self.data_file_path = data_file_path or self._resolve_default_dataset_path()
        self._cached_data: Optional[Dict[str, Any]] = None

    def _resolve_default_dataset_path(self) -> Path:
        """Locates the demo rainfall dataset across project directory roots."""
        # Candidate 1: FloodGuard-AI/data/demo_rainfall.json
        candidate_root = Path(__file__).resolve().parent.parent.parent / "data" / "demo_rainfall.json"
        if candidate_root.exists():
            return candidate_root

        # Candidate 2: FloodGuard-AI/backend/data/demo_rainfall.json
        candidate_backend = Path(__file__).resolve().parent.parent / "data" / "demo_rainfall.json"
        if candidate_backend.exists():
            return candidate_backend

        # Default fallback
        return candidate_root

    def load_dataset(self, force_reload: bool = False) -> Dict[str, Any]:
        """Loads and validates JSON content from the configured rainfall dataset."""
        if self._cached_data and not force_reload:
            return self._cached_data

        if not self.data_file_path.exists():
            raise RainfallFileNotFoundError(
                f"Rainfall dataset not found at expected path: {self.data_file_path}"
            )

        try:
            with open(self.data_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as err:
            raise InvalidRainfallDataFormatError(f"Corrupted JSON in rainfall dataset: {err}") from err
        except Exception as err:
            raise RainfallServiceError(f"Failed to read rainfall dataset: {err}") from err

        if not isinstance(data, dict) or "series" not in data or not isinstance(data["series"], list):
            raise InvalidRainfallDataFormatError(
                "Rainfall data must contain a top-level dictionary with a 'series' list"
            )

        self._cached_data = data
        return data


# Global singleton instance for injection
default_rainfall_service = RainfallService()
