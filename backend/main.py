from fastapi import FastAPI
import json
from pathlib import Path

app = FastAPI(
    title="FloodGuard AI",
    description="Urban Flood Nowcasting and Decision Support System",
    version="0.1.0"
)


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "message": "FloodGuard backend is running",
        "version": "0.1.0"
    }


@app.get("/api/flood")
def get_flood_data():
    data_path = Path(__file__).parent.parent / "data" / "flood_data.json"

    with open(data_path, "r") as file:
        data = json.load(file)

    return data