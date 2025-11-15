# SubAgent Registry - Developer Guide

This guide will help you create, register, and maintain your own subagents in the SubAgent Registry.

## Table of Contents

1. [SubAgent Anatomy](#subagent-anatomy)
2. [Creating a SubAgent YAML](#creating-a-subagent-yaml)
3. [Metadata Best Practices](#metadata-best-practices)
4. [Installation Methods](#installation-methods)
5. [Activation Types](#activation-types)
6. [Prompt Templates](#prompt-templates)
7. [Interface Specifications](#interface-specifications)
8. [Testing Your SubAgent](#testing-your-subagent)
9. [Publishing to the Registry](#publishing-to-the-registry)

---

## SubAgent Anatomy

A SubAgent consists of several components:

```yaml
metadata:          # Core information about the subagent
prompts:           # Template prompts for LLM interactions
interface:         # Tools and structured outputs
installations:     # How to install the subagent
activations:       # How to run the subagent
examples:          # Usage examples
dependencies:      # Required dependencies
```

## Creating a SubAgent YAML

### Minimal Example

```yaml
metadata:
  name: my-simple-agent
  version: 1.0.0
  description: "A simple example subagent"
  domain: example
  tags: [simple, example]
  capabilities:
    - "Demonstrate basic subagent structure"
  use_cases:
    - "When you need a simple example"

installations:
  - method: pip
    package_name: my-simple-agent
    package_version: "1.0.0"

activations:
  - activation_type: stdio
    command: python
    args: [-m, my_simple_agent]
```

### Complete Example

See `examples/research-agent.yaml` for a comprehensive example with all fields.

## Metadata Best Practices

### Name

- Use lowercase with hyphens: `research-agent`, `code-reviewer`
- Be descriptive but concise
- Avoid generic names like `agent` or `helper`

### Version

- Follow semantic versioning: `MAJOR.MINOR.PATCH`
- Increment MAJOR for breaking changes
- Increment MINOR for new features
- Increment PATCH for bug fixes

### Description

- Start with a verb: "Analyzes...", "Generates...", "Reviews..."
- Be specific about what it does
- Keep it under 100 characters
- Example: "Deep research agent with web search and citation management"

### Domain

Choose from common domains or create a new one:
- `research` - Research and information gathering
- `coding` - Code generation and analysis
- `data-science` - Data analysis and ML
- `writing` - Document and content creation
- `testing` - QA and testing
- `security` - Security and auditing
- `communication` - Email, chat, etc.
- `translation` - Language translation
- `database` - Database operations

### Tags

Include relevant tags for better discoverability:

```yaml
tags:
  - web-search          # Technical capability
  - academic-research   # Use case
  - citation           # Feature
  - python             # Technology
```

### Capabilities

List specific capabilities in active voice:

```yaml
capabilities:
  - "Conduct deep web research using Tavily API"
  - "Search academic databases"
  - "Manage citations and references"
  - "Generate formatted bibliographies"
```

### Use Cases

Describe when to use this subagent:

```yaml
use_cases:
  - "When user requests in-depth research"
  - "When academic citations are needed"
  - "For comprehensive literature reviews"
```

### Priority

Set priority (0-100) for search ranking:
- `0-5`: Low priority, specialized use cases
- `6-10`: Medium priority, common utilities
- `11-15`: High priority, frequently used
- `16+`: Critical, core functionality

## Installation Methods

### Git

For repositories:

```yaml
installations:
  - method: git
    repository: https://github.com/user/my-agent
    branch: main
    commit: abc123  # optional, pin to specific commit
    post_install_commands:
      - pip install -r requirements.txt
      - python setup.py install
```

### NPM

For Node.js packages:

```yaml
installations:
  - method: npm
    package_name: "@myorg/my-agent"
    package_version: "1.2.0"
    registry_url: https://registry.npmjs.org  # optional
```

### Pip

For Python packages:

```yaml
installations:
  - method: pip
    package_name: my-agent
    package_version: ">=1.0.0,<2.0.0"
```

### Docker

For containerized agents:

```yaml
installations:
  - method: docker
    image: myorg/my-agent:1.0.0
```

### Remote API

For hosted services:

```yaml
installations:
  - method: remote
    url: https://api.myservice.com/agent
    auth:
      type: bearer
      token_env: MY_SERVICE_TOKEN
```

### Multiple Installation Methods

Provide alternatives:

```yaml
installations:
  - method: pip
    package_name: my-agent
    package_version: "1.0.0"

  - method: docker
    image: myorg/my-agent:1.0.0

  - method: git
    repository: https://github.com/user/my-agent
    branch: main
```

## Activation Types

### stdio

For command-line agents:

```yaml
activations:
  - activation_type: stdio
    command: python
    args: [src/agent.py, --mode=production]
    working_dir: "{install_path}"
    env_vars:
      API_KEY:
        required: true
        description: "API key for external service"
      DEBUG:
        required: false
        default: "false"
```

### http

For HTTP API servers:

```yaml
activations:
  - activation_type: http
    command: npm
    args: [start]
    working_dir: "{install_path}"
    env_vars:
      PORT:
        required: false
        default: "3000"
    health_check:
      endpoint: /health
      interval_seconds: 30
      timeout_seconds: 5
```

### mcp

For Model Context Protocol:

```yaml
activations:
  - activation_type: mcp
    protocol: mcp
    capabilities: [read, write, execute]
    url: unix:///tmp/my-agent.sock
```

### sse

For Server-Sent Events:

```yaml
activations:
  - activation_type: sse
    url: https://api.myservice.com/stream
    auth:
      type: bearer
      token_env: SERVICE_TOKEN
```

### websocket

For WebSocket connections:

```yaml
activations:
  - activation_type: websocket
    url: wss://api.myservice.com/ws
```

## Prompt Templates

### Basic Prompt

```yaml
prompts:
  - name: system
    template: |
      You are a professional {{ role }}.
      Your task: {{ task }}
    variables:
      role: "The role of the agent"
      task: "The specific task to perform"
    format: jinja2
    description: "Main system prompt"
```

### Multiple Prompts

```yaml
prompts:
  - name: system
    template: "You are a code reviewer."

  - name: user_template
    template: |
      Review the following code:

      ```{{ language }}
      {{ code }}
      ```

      Focus on: {{ focus_areas }}
    variables:
      language: "Programming language"
      code: "Code to review"
      focus_areas: "Areas to focus on"

  - name: few_shot_example
    template: |
      Example review:
      Issue: Variable name is unclear
      Suggestion: Rename 'x' to 'user_count'
```

### Template Best Practices

1. **Use descriptive variable names**: `{{ task }}` not `{{ t }}`
2. **Provide variable descriptions**: Help users understand what to provide
3. **Use multiline templates**: More readable with `|` syntax
4. **Include context**: Give the LLM enough information
5. **Be specific**: "You are a Python code reviewer" vs "You are a reviewer"

## Interface Specifications

### Defining Tools

```yaml
interface:
  protocol: langchain
  tools:
    - name: search_web
      description: "Search the web using Tavily API"
      parameters:
        query:
          type: string
          description: "Search query"
        max_results:
          type: integer
          description: "Maximum number of results"
          default: 10
        include_images:
          type: boolean
          default: false
      required_params: [query]

    - name: extract_text
      description: "Extract text from a URL"
      parameters:
        url:
          type: string
          format: uri
      required_params: [url]
```

### Structured Outputs

Define expected output schemas:

```yaml
interface:
  structured_outputs:
    - name: ResearchReport
      schema_type: pydantic
      description: "Research report with citations"
      schema:
        properties:
          title:
            type: string
          summary:
            type: string
          key_findings:
            type: array
            items:
              type: string
          citations:
            type: array
            items:
              type: object
              properties:
                title:
                  type: string
                authors:
                  type: array
                  items:
                    type: string
                year:
                  type: integer
                url:
                  type: string
        required: [title, summary, citations]
```

### Protocol Types

- `langchain`: LangChain framework
- `mcp`: Model Context Protocol
- `openai_function`: OpenAI function calling
- `custom`: Custom protocol

## Testing Your SubAgent

### 1. Validate YAML

```bash
registry-cli validate my-agent.yaml
```

### 2. Import to Test Registry

```bash
# Start test server
registry-server

# Import your subagent
registry-cli import my-agent.yaml
```

### 3. Test Discovery

```bash
# Search for your subagent
registry-cli search "description of what your agent does"

# Verify it appears in results
registry-cli list
```

### 4. Test Prompts

```bash
# Get prompts
curl http://localhost:8000/prompts/my-agent

# Render a prompt
curl -X POST http://localhost:8000/prompts/my-agent/system/render \
  -H "Content-Type: application/json" \
  -d '{"variables": {"task": "test task"}}'
```

### 5. Check Metadata

```bash
curl http://localhost:8000/subagents/my-agent
```

## Publishing to the Registry

### 1. Prepare Your YAML

- Validate with `registry-cli validate`
- Test thoroughly
- Add comprehensive examples
- Include all dependencies

### 2. Create a Pull Request

```bash
# Fork the registry repository
git clone https://github.com/your-username/subagent-registry
cd subagent-registry

# Add your YAML file
cp /path/to/my-agent.yaml registry-data/community/

# Commit and push
git add registry-data/community/my-agent.yaml
git commit -m "Add my-agent subagent"
git push origin main

# Create PR on GitHub
```

### 3. Documentation

Include in your PR:
- Description of the subagent
- Use cases and examples
- Installation requirements
- Any special configuration needed

### 4. Checklist

- [ ] YAML validates successfully
- [ ] All required fields are present
- [ ] Version follows semantic versioning
- [ ] Installation instructions are clear
- [ ] At least 2 examples provided
- [ ] Dependencies are documented
- [ ] Prompts use clear variable names
- [ ] Priority is set appropriately
- [ ] Tags are relevant and helpful

---

## Examples

### Example 1: Simple API Wrapper

```yaml
metadata:
  name: weather-agent
  version: 1.0.0
  description: "Get weather information for any location"
  domain: utilities
  tags: [weather, api, information]
  capabilities:
    - "Get current weather for a location"
    - "Get weather forecast"
  use_cases:
    - "When weather information is needed"
  priority: 5

prompts:
  - name: system
    template: |
      You are a weather information assistant.
      Location: {{ location }}
      Provide clear, concise weather information.
    variables:
      location: "Location to get weather for"

interface:
  protocol: langchain
  tools:
    - name: get_weather
      description: "Get current weather"
      parameters:
        location:
          type: string
      required_params: [location]

installations:
  - method: pip
    package_name: weather-agent
    package_version: "1.0.0"

activations:
  - activation_type: stdio
    command: python
    args: [-m, weather_agent]
    env_vars:
      WEATHER_API_KEY:
        required: true
        description: "API key for weather service"

examples:
  - input: "What's the weather in Tokyo?"
    output: "Currently 22°C and sunny in Tokyo, Japan"

dependencies:
  - dep_type: python
    name: requests
    version: ">=2.28.0"
    required: true

  - dep_type: api
    name: openweather
    required: true
    description: "OpenWeather API access"
```

### Example 2: Data Processing Agent

```yaml
metadata:
  name: csv-analyzer
  version: 2.0.0
  description: "Analyze CSV files and generate insights"
  domain: data-science
  tags: [csv, data-analysis, statistics]
  capabilities:
    - "Parse and analyze CSV files"
    - "Generate statistical summaries"
    - "Create visualizations"
  use_cases:
    - "When CSV data needs analysis"
    - "For data exploration"
  priority: 10

prompts:
  - name: system
    template: |
      You are a data analyst.
      Dataset: {{ dataset_name }}
      Columns: {{ columns }}

      Provide clear insights and visualizations.
    variables:
      dataset_name: "Name of the dataset"
      columns: "List of columns in the dataset"

interface:
  protocol: langchain
  tools:
    - name: load_csv
      description: "Load and parse CSV file"
      parameters:
        file_path:
          type: string
      required_params: [file_path]

    - name: get_statistics
      description: "Calculate statistics"
      parameters:
        columns:
          type: array
          items:
            type: string
      required_params: [columns]

  structured_outputs:
    - name: DataAnalysis
      schema_type: pydantic
      schema:
        properties:
          summary:
            type: string
          row_count:
            type: integer
          column_count:
            type: integer
          statistics:
            type: object
          insights:
            type: array
            items:
              type: string
        required: [summary, row_count, column_count]

installations:
  - method: pip
    package_name: csv-analyzer
    package_version: "2.0.0"

activations:
  - activation_type: http
    command: uvicorn
    args: [csv_analyzer.api:app, --host, "0.0.0.0", --port, "8000"]
    health_check:
      endpoint: /health

examples:
  - input: "Analyze sales_data.csv"
    output: "Dataset has 10,000 rows, 8 columns. Top insight: Sales increased 25% in Q3"

dependencies:
  - dep_type: python
    name: pandas
    version: ">=2.0.0"
    required: true

  - dep_type: python
    name: numpy
    version: ">=1.24.0"
    required: true
```

---

## Common Patterns

### Pattern 1: Multi-Step Agent

For agents that perform multiple steps:

```yaml
prompts:
  - name: planning
    template: "Create a plan for: {{ task }}"

  - name: execution
    template: "Execute step {{ step_number }}: {{ step_description }}"

  - name: review
    template: "Review the results: {{ results }}"
```

### Pattern 2: Configurable Behavior

For agents with different modes:

```yaml
prompts:
  - name: system
    template: |
      Mode: {{ mode }}
      {% if mode == "strict" %}
      Be very precise and formal.
      {% elif mode == "casual" %}
      Be friendly and conversational.
      {% endif %}
    variables:
      mode: "Operation mode (strict, casual, balanced)"
```

### Pattern 3: Domain-Specific Agent

For specialized domains:

```yaml
metadata:
  domain: medical-research
  tags: [medical, research, pubmed, clinical-trials]
  capabilities:
    - "Search PubMed and clinical trial databases"
    - "Summarize medical research papers"

interface:
  tools:
    - name: search_pubmed
      description: "Search PubMed database"
    - name: search_clinical_trials
      description: "Search clinical trials database"
```

---

## Tips and Tricks

1. **Start Simple**: Begin with minimal YAML, add complexity as needed
2. **Test Locally**: Always test before publishing
3. **Use Examples**: Provide clear, realistic examples
4. **Version Carefully**: Follow semantic versioning strictly
5. **Document Dependencies**: Be explicit about all requirements
6. **Optimize for Search**: Use relevant tags and clear descriptions
7. **Consider Users**: Write prompts that are easy to understand and customize

## Getting Help

- Check existing examples in `examples/` directory
- Read the [User Guide](USER_GUIDE.md)
- Open an issue on GitHub
- Join the community discussions

---

## Appendix: Full YAML Schema

```yaml
metadata:
  name: string (required)
  version: string (required, semver)
  description: string (required)
  author: string (optional)
  license: string (optional)
  domain: string (required)
  tags: array of strings (optional)
  capabilities: array of strings (optional)
  use_cases: array of strings (optional)
  priority: integer 0-100 (default: 0)

prompts: array (optional)
  - name: string (required)
    template: string (required)
    variables: object (optional)
    format: "jinja2" | "f-string" (default: "jinja2")
    description: string (optional)

interface: object (optional)
  protocol: "langchain" | "mcp" | "openai_function" | "custom"
  tools: array (optional)
    - name: string
      description: string
      parameters: object
      required_params: array of strings
  structured_outputs: array (optional)
    - name: string
      schema_type: "pydantic" | "json_schema" | "openai_function"
      schema: object
      description: string

installations: array (optional)
  - method: "git" | "npm" | "pip" | "docker" | "remote"
    # Git-specific
    repository: string
    branch: string
    commit: string
    # Package-specific
    package_name: string
    package_version: string
    registry_url: string
    # Docker-specific
    image: string
    # Remote-specific
    url: string
    auth: object
    # Common
    post_install_commands: array of strings

activations: array (optional)
  - activation_type: "stdio" | "http" | "mcp" | "sse" | "websocket"
    command: string
    args: array of strings
    working_dir: string
    env_vars: object
    health_check: object
    protocol: string
    capabilities: array of strings
    url: string
    auth: object

examples: array (optional)
  - input: string
    output: string
    description: string

dependencies: array (optional)
  - dep_type: "python" | "npm" | "system" | "api"
    name: string
    version: string
    required: boolean
    description: string
```
