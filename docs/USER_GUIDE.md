# SubAgent Registry - User Guide

Welcome to the SubAgent Registry User Guide! This guide will help you get started with using the SubAgent Registry to discover, manage, and use subagents.

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Using the CLI](#using-the-cli)
5. [Using the API](#using-the-api)
6. [Searching for SubAgents](#searching-for-subagents)
7. [Managing SubAgents](#managing-subagents)
8. [Working with Prompts](#working-with-prompts)

---

## Introduction

SubAgent Registry is a RAG-based registry and search engine for managing subagent metadata, installation methods, prompts, and execution specifications. It helps you:

- **Discover** subagents using natural language search
- **Manage** subagent metadata centrally
- **Access** installation and execution information
- **Retrieve** prompt templates dynamically

## Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Install from Source

```bash
git clone https://github.com/deepagents-team/subagent-registry
cd subagent-registry
pip install -e .
```

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### Set Environment Variables

```bash
# Required for search functionality
export OPENAI_API_KEY="your-openai-api-key"

# Optional: For persistent vector database
export QDRANT_URL="http://localhost:6333"
export QDRANT_API_KEY="your-qdrant-api-key"
```

## Quick Start

### 1. Start the API Server

```bash
registry-server
```

The server will start on `http://localhost:8000`. Visit `http://localhost:8000/docs` for interactive API documentation.

### 2. Import Sample SubAgents

```bash
# Import a single subagent
registry-cli import examples/research-agent.yaml

# Import all examples
for file in examples/*.yaml; do
    registry-cli import "$file"
done
```

### 3. Search for SubAgents

```bash
# Search using the CLI
registry-cli search "research with citations"

# Or use the API
curl -X POST "http://localhost:8000/search/" \
  -H "Content-Type: application/json" \
  -d '{"query": "research with citations", "top_k": 5}'
```

## Using the CLI

The `registry-cli` tool provides command-line access to registry functions.

### Import a SubAgent

Import a subagent from a YAML file:

```bash
registry-cli import path/to/subagent.yaml
```

### List All SubAgents

```bash
# List all subagents
registry-cli list

# Filter by domain
registry-cli list --domain research
```

### Search for SubAgents

```bash
# Basic search
registry-cli search "I need code review"

# Limit results
registry-cli search "data analysis" --top-k 3

# Filter by domain
registry-cli search "translation" --domain translation
```

### Validate a YAML File

Before importing, you can validate a YAML file:

```bash
registry-cli validate examples/my-agent.yaml
```

### Rebuild Vector Index

After making many changes, rebuild the search index:

```bash
registry-cli reindex
```

## Using the API

The SubAgent Registry provides a REST API for programmatic access.

### API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Common API Operations

#### Search for SubAgents

```bash
curl -X POST "http://localhost:8000/search/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "I need a subagent for web scraping",
    "top_k": 5
  }'
```

#### Get SubAgent Details

```bash
curl "http://localhost:8000/subagents/research-agent"
```

#### List All SubAgents

```bash
curl "http://localhost:8000/subagents/"
```

#### Get Prompts

```bash
# Get all prompts for a subagent
curl "http://localhost:8000/prompts/research-agent"

# Get specific prompt
curl "http://localhost:8000/prompts/research-agent/system"
```

#### Render a Prompt Template

```bash
curl -X POST "http://localhost:8000/prompts/research-agent/system/render" \
  -H "Content-Type: application/json" \
  -d '{
    "variables": {
      "task": "Research AI safety",
      "max_sources": "10"
    }
  }'
```

## Searching for SubAgents

The registry uses RAG (Retrieval-Augmented Generation) for semantic search.

### How Search Works

1. Your query is embedded using OpenAI's embedding model
2. Similar subagents are found using vector similarity
3. Results are re-ranked based on relevance and priority
4. Top results are returned with scores

### Search Tips

**Use natural language:**
```bash
registry-cli search "I need to translate documents to Japanese"
```

**Describe your use case:**
```bash
registry-cli search "analyze sales data and create visualizations"
```

**Be specific:**
```bash
# Good
registry-cli search "review GitHub pull requests automatically"

# Less specific
registry-cli search "code review"
```

### Search by Capability

Search for specific capabilities:

```bash
curl "http://localhost:8000/search/by-capability?capability=translate%20text"
```

### Filtering

Filter search results by domain or tags:

```bash
curl -X POST "http://localhost:8000/search/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "data processing",
    "domain": "data-science",
    "tags": ["visualization"]
  }'
```

## Managing SubAgents

### Create a New SubAgent

You can create subagents via the API:

```bash
curl -X POST "http://localhost:8000/subagents/" \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {
      "name": "my-custom-agent",
      "version": "1.0.0",
      "description": "My custom subagent",
      "domain": "custom",
      "tags": ["custom"],
      "capabilities": ["Do custom things"],
      "use_cases": ["When custom work is needed"]
    }
  }'
```

### Update a SubAgent

```bash
curl -X PUT "http://localhost:8000/subagents/my-custom-agent" \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {
      "name": "my-custom-agent",
      "version": "1.1.0",
      "description": "Updated description",
      "domain": "custom"
    }
  }'
```

### Delete a SubAgent

```bash
curl -X DELETE "http://localhost:8000/subagents/my-custom-agent"
```

## Working with Prompts

Prompts are templates that can be rendered with variables.

### Get All Prompts for a SubAgent

```bash
curl "http://localhost:8000/prompts/research-agent"
```

### Get a Specific Prompt

```bash
curl "http://localhost:8000/prompts/research-agent/system"
```

### Render a Prompt

```bash
curl -X POST "http://localhost:8000/prompts/research-agent/system/render" \
  -H "Content-Type: application/json" \
  -d '{
    "variables": {
      "task": "Analyze market trends in renewable energy",
      "max_sources": "15"
    }
  }'
```

Response:
```json
{
  "rendered": "You are a dedicated research agent.\nYour task: Analyze market trends in renewable energy\nMaximum sources: 15\n..."
}
```

### Prompt Template Formats

The registry supports two template formats:

1. **Jinja2** (recommended):
   ```jinja2
   Hello {{ name }}, your task is {{ task }}.
   ```

2. **f-string**:
   ```python
   Hello {name}, your task is {task}.
   ```

---

## Advanced Usage

### Using with Python

```python
import httpx

# Create a client
client = httpx.Client(base_url="http://localhost:8000")

# Search for subagents
response = client.post("/search/", json={
    "query": "I need code review",
    "top_k": 3
})
results = response.json()["results"]

for result in results:
    print(f"{result['name']}: {result['description']}")
    print(f"Score: {result['score']}\n")

# Get subagent details
subagent = client.get(f"/subagents/{results[0]['name']}").json()
print(f"Installation: {subagent['installations'][0]}")

# Get and render prompt
prompt = client.get(f"/prompts/{results[0]['name']}/system").json()
rendered = client.post(
    f"/prompts/{results[0]['name']}/system/render",
    json={"variables": {"task": "Review this code"}}
).json()
print(f"Rendered prompt: {rendered['rendered']}")
```

### Batch Operations

Import multiple subagents:

```bash
#!/bin/bash
for file in /path/to/subagents/*.yaml; do
    registry-cli import "$file"
done
```

### Monitoring

Get registry statistics:

```bash
curl "http://localhost:8000/admin/stats"
```

Response:
```json
{
  "subagents_count": 10,
  "vector_db_stats": {
    "collection_name": "subagents",
    "points_count": 10,
    "vectors_count": 10
  }
}
```

---

## Troubleshooting

### Search Returns No Results

1. Make sure OPENAI_API_KEY is set
2. Check that subagents are indexed: `curl http://localhost:8000/admin/stats`
3. Rebuild the index: `registry-cli reindex`

### Import Fails

1. Validate YAML first: `registry-cli validate file.yaml`
2. Check YAML syntax
3. Ensure all required fields are present

### API Not Responding

1. Check if server is running: `curl http://localhost:8000/health`
2. Check logs for errors
3. Verify database is accessible

---

## Next Steps

- Read the [Developer Guide](DEVELOPER_GUIDE.md) to learn how to create your own subagents
- Explore the [API Documentation](http://localhost:8000/docs)
- Check out example subagents in the `examples/` directory

## Support

For issues and questions:
- GitHub Issues: https://github.com/deepagents-team/subagent-registry/issues
- Documentation: https://docs.deepagents.ai
