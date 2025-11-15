"""Main FastAPI application."""

import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from registry_engine.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown events.

    Args:
        app: FastAPI application

    Yields:
        None
    """
    # Startup: Initialize database
    print("Initializing database...")
    init_db()
    print("Database initialized successfully")

    yield

    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="SubAgent Registry API",
    description="RAG-based registry and search engine for managing subagent metadata",
    version="0.1.0",
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
        "message": "SubAgent Registry API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint.

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "subagent-registry",
        "version": "0.1.0",
    }


# Import and include routers
from .routes import subagents, prompts, search, admin

app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(subagents.router, prefix="/subagents", tags=["SubAgents"])
app.include_router(prompts.router, prefix="/prompts", tags=["Prompts"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])


def main() -> None:
    """Run the API server."""
    uvicorn.run(
        "registry_engine.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
