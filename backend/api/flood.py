from fastapi import APIRouter, HTTPException
import json
from pathlib import Path

router = APIRouter(tags=["Flood"])


def get_data_file_path() -> Path:
    """Resolve the path to the baseline flood data JSON file."""
    # Check project root data directory first
    root_candidate = Path(__file__).resolve().parent.parent.parent / "data" / "flood_data.json"
    if root_candidate.exists():
        return root_candidate
    # Fallback to backend-local data directory if present
    backend_candidate = Path(__file__).resolve().parent.parent / "data" / "flood_data.json"
    if backend_candidate.exists():
        return backend_candidate
    return root_candidate


@router.get("/flood")
def get_flood_data():
    """Retrieve flood overview data, preserving original contract."""
    data_path = get_data_file_path()
    if not data_path.exists():
        raise HTTPException(status_code=404, detail="Flood baseline data file not found")

    with open(data_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data
