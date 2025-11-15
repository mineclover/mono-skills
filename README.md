# SubAgent Registry & Search Engine

A RAG-based registry and search engine for managing subagent metadata, installation methods, prompts, and execution specifications.

## Overview

SubAgent Registry provides centralized management for:
- **Search Engine**: RAG-based semantic search for finding subagents
- **Metadata Management**: Installation methods, execution specs, and interfaces
- **Prompt Templates**: Jinja2-based prompt storage and version control
- **Multiple Installation Methods**: Git, NPM, Pip, Docker, Remote API support
- **Structured Output Specs**: Pydantic models and JSON Schema management

## Installation

```bash
pip install -e .
```

## Quick Start

### Start the API Server

```bash
registry-server
```

The API will be available at `http://localhost:8000`

### Use the CLI

```bash
# Import a subagent from YAML
registry-cli import examples/research-agent.yaml

# List all subagents
registry-cli list

# Search for subagents
registry-cli search "research with citations"

# Rebuild vector index
registry-cli reindex
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
registry_engine/
├── api/              # FastAPI application
├── database/         # SQLite and Qdrant operations
├── search/           # RAG search engine
├── prompts/          # Prompt management
└── models/           # Pydantic models
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .
ruff check .

# Type checking
mypy registry_engine
```

## License

MIT
