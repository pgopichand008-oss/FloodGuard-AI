"""Drainage data access service for loading and querying drainage network datasets."""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.models.drainage_models import DrainageEdgeModel, DrainageNodeModel


class DrainageServiceError(Exception):
    """Base exception for drainage service failures."""
    pass


class DrainageFileNotFoundError(DrainageServiceError):
    """Raised when the requested drainage dataset file cannot be located."""
    pass


class InvalidDrainageDataFormatError(DrainageServiceError):
    """Raised when drainage dataset fails structural or validation requirements."""
    pass


class DrainageService:
    """Service to load, resolve, and query urban drainage network datasets."""

    def __init__(self, data_file_path: Optional[Path] = None):
        self.data_file_path = data_file_path or self._resolve_default_dataset_path()
        self._cached_data: Optional[Dict[str, Any]] = None

    def _resolve_default_dataset_path(self) -> Path:
        """Locates the demo drainage dataset across project directory roots."""
        candidate_root = Path(__file__).resolve().parent.parent.parent / "data" / "drainage_demo.json"
        if candidate_root.exists():
            return candidate_root

        candidate_backend = Path(__file__).resolve().parent.parent / "data" / "drainage_demo.json"
        if candidate_backend.exists():
            return candidate_backend

        return candidate_root

    def load_dataset(self, force_reload: bool = False) -> Dict[str, Any]:
        """Loads and validates JSON content from the configured drainage dataset."""
        if self._cached_data and not force_reload:
            return self._cached_data

        if not self.data_file_path.exists():
            raise DrainageFileNotFoundError(
                f"Drainage dataset not found at expected path: {self.data_file_path}"
            )

        try:
            with open(self.data_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as err:
            raise InvalidDrainageDataFormatError(f"Corrupted JSON in drainage dataset: {err}") from err
        except Exception as err:
            raise DrainageServiceError(f"Failed to read drainage dataset: {err}") from err

        if not isinstance(data, dict):
            raise InvalidDrainageDataFormatError("Drainage data must be a top-level dictionary")

        if "nodes" not in data or not isinstance(data["nodes"], list):
            raise InvalidDrainageDataFormatError("Drainage data must contain a 'nodes' list")

        if "edges" not in data or not isinstance(data["edges"], list):
            raise InvalidDrainageDataFormatError("Drainage data must contain an 'edges' list")

        self._cached_data = data
        return data

    def get_raw_nodes(self) -> List[Dict[str, Any]]:
        """Returns raw node dictionaries."""
        data = self.load_dataset()
        return data.get("nodes", [])

    def get_raw_edges(self) -> List[Dict[str, Any]]:
        """Returns raw edge dictionaries."""
        data = self.load_dataset()
        return data.get("edges", [])

    def get_node_models(self) -> List[DrainageNodeModel]:
        """Parses and validates all nodes as Pydantic models."""
        raw_nodes = self.get_raw_nodes()
        nodes: List[DrainageNodeModel] = []
        for n in raw_nodes:
            nodes.append(DrainageNodeModel(**n))
        return nodes

    def get_edge_models(self) -> List[DrainageEdgeModel]:
        """Parses and validates all edges as Pydantic models."""
        raw_edges = self.get_raw_edges()
        edges: List[DrainageEdgeModel] = []
        for e in raw_edges:
            edges.append(DrainageEdgeModel(**e))
        return edges


# Global singleton instance
default_drainage_service = DrainageService()
