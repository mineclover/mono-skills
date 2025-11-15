"""Main FastAPI application - V2 with Tool-centric architecture."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from registry_engine.database.models_v2 import Base
from sqlalchemy import create_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown events.

    Args:
        app: FastAPI application

    Yields:
        None
    """
    # Startup: Initialize database
    print("Initializing database (v2 schema)...")
    engine = create_engine("sqlite:///data/registry_v2.db", echo=False)
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully")

    yield

    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="SubAgent Registry API (V2)",
    description="Tool-centric registry and search engine for managing tools, prompts, and installation metadata",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint.

    Returns:
        Welcome message
    """
    return {
        "message": "SubAgent Registry API (V2 - Tool-centric)",
        "version": "2.0.0",
        "docs": "/docs",
        "features": [
            "Tool-focused search engine",
            "Multi-platform installation support",
            "Tool-level prompts and schemas",
            "User contributions via YAML/JSON",
            "Advanced metadata search",
        ],
    }


@app.get("/health")
async def health_check():
    """Health check endpoint.

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "subagent-registry-v2",
        "version": "2.0.0",
    }


# Import and include routers
from registry_engine.api.routes import (
    tools,
    search_v2,
    search_advanced,
    contributions,
)
from registry_engine.api.routes.subagents import router as subagents_router_v1

# V2 routes
app.include_router(tools.router, prefix="/tools", tags=["Tools"])
app.include_router(search_v2.router, prefix="/search", tags=["Search"])
app.include_router(search_advanced.router, prefix="/search", tags=["Advanced Search"])
app.include_router(contributions.router, prefix="/contribute", tags=["Contributions"])

# V1 compat (SubAgents)
app.include_router(subagents_router_v1, prefix="/subagents", tags=["SubAgents"])


def main() -> None:
    """Run the API server."""
    uvicorn.run(
        "registry_engine.api.app_v2:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
