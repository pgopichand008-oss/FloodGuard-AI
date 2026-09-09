from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import (
    drainage,
    explanations,
    flood,
    health,
    ml,
    priorities,
    propagation,
    rainfall,
    routing,
    simulation,
    terrain,
)

app = FastAPI(
    title="FloodGuard AI",
    description="Urban Flood Nowcasting and Decision Support System",
    version="0.1.0"
)

# Enable CORS for frontend integration (Vite dev server default: localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register modular routers under /api prefix
app.include_router(health.router, prefix="/api")
app.include_router(flood.router, prefix="/api")
app.include_router(rainfall.router, prefix="/api")
app.include_router(terrain.router, prefix="/api")
app.include_router(drainage.router, prefix="/api")
app.include_router(ml.router, prefix="/api")
app.include_router(explanations.router, prefix="/api")
app.include_router(simulation.router, prefix="/api")
app.include_router(priorities.router, prefix="/api")
app.include_router(propagation.router, prefix="/api")
app.include_router(routing.router, prefix="/api")


@app.get("/")
def root():
    """Root metadata endpoint."""
    return {
        "name": "FloodGuard AI API",
        "status": "online",
        "version": "0.1.0",
        "docs_url": "/docs"
    }