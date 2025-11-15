# Contribution Guide

## Adding Tools to the Registry

This guide explains how to contribute new tools and SubAgents to the registry. The registry uses a **Tool-centric architecture** where individual tools (functions) are the primary searchable entities, while SubAgents represent the packages that provide these tools.

## Table of Contents

- [Understanding the Architecture](#understanding-the-architecture)
- [YAML File Structure](#yaml-file-structure)
- [Multi-Platform Support](#multi-platform-support)
- [Contribution Methods](#contribution-methods)
- [Validation](#validation)
- [Examples](#examples)

## Understanding the Architecture

### Key Concepts

1. **Tools** are individual functions that users search for (e.g., `web_search`, `encrypt_data`)
2. **SubAgents** are packages/toolkits that provide installation and execution methods
3. **Installation** describes how to install the package (pip, npm, docker, remote API, etc.)
4. **Activation** describes how to execute the tools (CLI, HTTP, SSE, etc.)
5. **Installation and Activation are independent** - remote APIs don't need installation

### Architecture Principles

- Registry is an **information catalog**, NOT an execution engine
- Provides "how to install" and "how to use" information
- Supports multiple platforms: Python (pip), Node.js (npm), Rust (cargo), Go, Docker, binaries, remote APIs
- Tools can have platform-specific activation methods

## YAML File Structure

### Complete Example

```yaml
# SubAgent: Package metadata
subagent:
  name: example-toolkit
  version: 1.0.0
  description: "Example toolkit description"
  author: your-name
  license: MIT
  category: search  # or security, database, image-processing, etc.
  tags: [tag1, tag2]
  priority: 10  # Higher = more important

  # Installation methods (can be multiple)
  installations:
    - method: pip  # pip, npm, yarn, cargo, go, docker, binary, git, remote
      platform_id: pip-python  # Unique ID linking to activation
      package_name: example-toolkit
      package_version: ">=1.0.0"
      requires_install: true

    - method: remote
      platform_id: remote-api
      api_endpoint: https://api.example.com/v1
      auth_method: bearer
      requires_install: false  # No installation needed!

  # Activation methods (platform-specific)
  activations:
    - type: cli
      platform_id: pip-python  # Links to installation above
      command: example-toolkit
      env_vars:
        API_KEY:
          required: true
          description: "API key for authentication"

    - type: http_endpoint
      platform_id: remote-api
      base_url: https://api.example.com/v1
      env_vars:
        API_KEY:
          required: true

  # Dependencies (optional)
  dependencies:
    - dep_type: api  # api, system, database, hardware
      name: external-service
      required: true
      description: "External service description"

# Tools: Individual functions
tools:
  - name: tool_function_name
    display_name: "Human-Readable Tool Name"
    description: "What this tool does"
    category: search
    tags: [specific, tool, tags]

    subagent_name: example-toolkit
    subagent_version: "1.0.0"

    # Prompts for this tool (LangChain compatible)
    prompts:
      - name: default
        description: "Standard prompt"
        template_type: chat
        system_message: |
          System instructions for the tool.
        human_message_template: |
          User query template: {input_variable}
        input_variables: [input_variable]
        partial_variables:
          default_var: "default value"
        template: |
          System: {system_message}
          Human: {human_message_template}

    # Input parameters (JSON Schema)
    parameters:
      type: object
      properties:
        param1:
          type: string
          description: "Parameter description"
        param2:
          type: integer
          default: 10
      required: [param1]

    # Structured output (optional)
    structured_output:
      name: OutputSchema
      description: "Output schema description"

      json_schema:
        type: object
        properties:
          result:
            type: string

      pydantic_code: |
        from pydantic import BaseModel

        class OutputSchema(BaseModel):
            result: str

      typescript_type: |
        interface OutputSchema {
          result: string;
        }

      examples:
        - result: "example output"

    # Tool-specific activations (optional, overrides SubAgent)
    activations:
      - type: cli_subcommand
        platform_id: pip-python
        command: example-toolkit
        subcommand: tool-name

    protocol: langchain  # or openai
    implementation_hint: "example_toolkit.tools.ToolClass"
```

## Multi-Platform Support

### Supported Installation Methods

| Method | Platform ID Example | Use Case |
|--------|-------------------|----------|
| `pip` | `pip-python` | Python packages |
| `npm` | `npm-node` | Node.js packages |
| `yarn` | `yarn-node` | Yarn packages |
| `cargo` | `cargo-rust` | Rust packages |
| `go` | `go-cli` | Go modules |
| `docker` | `docker-http` | Docker containers |
| `binary` | `binary-linux`, `binary-macos` | Pre-built binaries |
| `git` | `git-clone` | Git repositories |
| `remote` | `remote-api` | Remote APIs (no install) |

### Supported Activation Types

| Type | Description | Example |
|------|-------------|---------|
| `cli` | Command-line interface | `tavily-toolkit` |
| `cli_subcommand` | CLI with subcommand | `db-migrate up` |
| `http_server` | HTTP server | Docker container with REST API |
| `http_endpoint` | Specific HTTP endpoint | `POST /api/search` |
| `grpc` | gRPC service | gRPC server |
| `websocket` | WebSocket connection | Real-time bidirectional |
| `sse` | Server-Sent Events | Real-time streaming |
| `stdio` | Standard I/O | Piped communication |
| `library` | Direct library import | Python/JS module |

### Platform ID Linking

The `platform_id` field links installations to their activation methods:

```yaml
installations:
  - method: pip
    platform_id: pip-python  # <-- Links here

activations:
  - type: cli
    platform_id: pip-python  # <-- To here
```

## Contribution Methods

### Method 1: YAML Upload (Recommended)

1. **Create YAML file** following the structure above
2. **Validate** using the API endpoint:
   ```bash
   curl -X POST http://localhost:8000/contribute/yaml/validate \
     -F "file=@your-toolkit.yaml"
   ```
3. **Import** (creates SubAgent + Tools, auto-indexes):
   ```bash
   curl -X POST http://localhost:8000/contribute/yaml/import \
     -F "file=@your-toolkit.yaml"
   ```

### Method 2: JSON API

#### Submit SubAgent First

```bash
curl -X POST http://localhost:8000/contribute/subagents/submit \
  -H "Content-Type: application/json" \
  -d @subagent.json
```

#### Then Submit Tools

```bash
curl -X POST http://localhost:8000/contribute/tools/submit \
  -H "Content-Type: application/json" \
  -d @tool.json
```

### Method 3: Python Script

```python
import httpx

async def contribute_toolkit(yaml_path: str):
    async with httpx.AsyncClient() as client:
        # Validate first
        with open(yaml_path, 'rb') as f:
            response = await client.post(
                "http://localhost:8000/contribute/yaml/validate",
                files={'file': (yaml_path, f)}
            )
        print(response.json())

        # Import if valid
        with open(yaml_path, 'rb') as f:
            response = await client.post(
                "http://localhost:8000/contribute/yaml/import",
                files={'file': (yaml_path, f)}
            )
        print(response.json())
```

## Validation

### Validation Checks

The API validates:

1. **YAML Syntax** - Valid YAML format
2. **Required Fields** - All mandatory fields present
3. **Schema Compliance** - Data types match schema
4. **Platform Consistency** - Platform IDs properly linked
5. **Dependencies** - Valid dependency declarations

### Common Validation Errors

| Error | Solution |
|-------|----------|
| `Missing required field 'name'` | Add the missing field |
| `Missing 'subagent' section` | Include subagent metadata |
| `Missing or empty 'tools' section` | Add at least one tool |
| `SubAgent 'X' already exists` | Use a different name or update existing |
| `Tool 'X' already exists` | Use a different name |

### Validation Script

Use the provided validation script to test locally:

```bash
python validate_yaml_examples.py
```

## Examples

### Example 1: Python CLI Tool (pip)

```yaml
subagent:
  name: tavily-search-toolkit
  version: 1.0.0
  description: "Web search toolkit"
  category: search

  installations:
    - method: pip
      platform_id: pip-python
      package_name: tavily-search-toolkit
      requires_install: true

  activations:
    - type: cli
      platform_id: pip-python
      command: tavily-toolkit

tools:
  - name: web_search
    display_name: "Web Search"
    description: "Search the web"
    category: search
    subagent_name: tavily-search-toolkit
    # ... rest of tool definition
```

### Example 2: Docker Container (HTTP API)

```yaml
subagent:
  name: ml-inference-service
  version: 1.5.2
  description: "ML inference service"
  category: machine-learning

  installations:
    - method: docker
      platform_id: docker-http
      image: mlops/inference:1.5.2
      requires_install: true

  activations:
    - type: http_server
      platform_id: docker-http
      host: "0.0.0.0"
      port: 8080

tools:
  - name: classify_text
    activations:
      - type: http_endpoint
        platform_id: docker-http
        endpoint: /api/classify
        method: POST
```

### Example 3: Remote API (No Installation)

```yaml
subagent:
  name: weather-api
  version: 3.0.0
  description: "Weather data API"
  category: weather

  installations:
    - method: remote
      platform_id: remote-api
      api_endpoint: https://api.weather.com/v3
      requires_install: false  # KEY: No installation needed!

  activations:
    - type: http_server
      platform_id: remote-api
      host: api.weather.com
      port: 443
      protocol: https

tools:
  - name: get_current_weather
    activations:
      - type: http_endpoint
        platform_id: remote-api
        endpoint: /weather/current
        method: GET
```

### Example 4: Rust Binary (Cargo + Binary)

```yaml
subagent:
  name: crypto-toolkit
  version: 0.4.1
  description: "Cryptography toolkit"
  category: security

  installations:
    - method: cargo
      platform_id: cargo-rust
      package_name: crypto-toolkit
      requires_install: true

    - method: binary
      platform_id: binary-linux
      download_url: https://example.com/crypto-toolkit-linux
      requires_install: true

  activations:
    - type: cli
      platform_id: cargo-rust
      command: crypto-toolkit

    - type: cli
      platform_id: binary-linux
      command: ./crypto-toolkit
```

## Full Examples

See the `examples_v2/` directory for complete examples:

- `tavily-search-toolkit.yaml` - Python, npm, docker, remote API
- `npm-image-processor.yaml` - Node.js (npm/yarn)
- `docker-ml-inference.yaml` - Docker container with HTTP API
- `cargo-crypto-tools.yaml` - Rust (cargo) with binaries
- `remote-weather-api.yaml` - Remote API only (no installation)
- `go-database-tools.yaml` - Go module with binaries

## Auto-Indexing

When you import tools via the contribution API, they are automatically indexed in the vector database for semantic search. This means:

1. **Immediate Searchability** - Tools appear in search results right away
2. **Semantic Search** - Users can find tools using natural language queries
3. **Category Filtering** - Tools are organized by category
4. **Tag-based Discovery** - Tags enable fine-grained filtering

## Best Practices

1. **Use Descriptive Names** - Clear, searchable tool names
2. **Comprehensive Descriptions** - Help users understand what the tool does
3. **Multiple Prompts** - Provide different prompt templates for various use cases
4. **Structured Outputs** - Define clear output schemas with Pydantic + TypeScript
5. **Platform Coverage** - Support multiple platforms when possible
6. **Examples** - Include examples in structured output schemas
7. **Environment Variables** - Document all required configuration
8. **Dependencies** - Explicitly list all dependencies

## Need Help?

- Check the examples in `examples_v2/`
- Review the architecture docs: `ARCHITECTURE.md`
- Understand installation/activation: `INSTALLATION_ACTIVATION.md`
- Test locally with: `validate_yaml_examples.py`

## API Documentation

Once the server is running, visit:

- Interactive API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc
