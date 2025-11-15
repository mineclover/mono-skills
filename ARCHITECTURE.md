# SubAgent Registry - 올바른 아키텍처 설계

## 핵심 역할 정의

**Registry는 정보 제공자/검색 엔진입니다:**
- ❌ 도구를 실행하지 않음
- ❌ 에이전트를 운영하지 않음
- ✅ **설치 방법 정보** 제공
- ✅ **사용법(프롬프트)** 제공
- ✅ **입출력 스펙** 제공
- ✅ **도구 검색** 기능

**실제 운영은 클라이언트(예: DeepAgents)가 담당:**
- Registry에서 정보를 조회
- 설치 방법에 따라 설치
- 프롬프트를 사용해 도구 호출
- Structured Output으로 결과 파싱

## 올바른 개념 모델

```
SubAgent Registry (정보 저장소)
│
├── SubAgents (패키지 메타데이터)
│   ├── 기본 정보 (이름, 버전, 설명)
│   ├── Installation (어떻게 설치하나?)
│   │   ├── Python: pip install
│   │   ├── Node.js: npm install
│   │   ├── Go: go get
│   │   ├── Rust: cargo install
│   │   ├── Docker: docker pull
│   │   ├── Binary: download from URL
│   │   └── Remote API: HTTP endpoint
│   ├── Activation (어떻게 실행하나?)
│   │   ├── CLI: command + args
│   │   ├── HTTP Server: port, health check
│   │   ├── gRPC: endpoint
│   │   └── WebSocket: connection info
│   └── Tools[] (제공하는 도구들)
│
└── Tools (기능 단위 - 검색 대상)
    ├── 메타데이터 (이름, 설명, 카테고리)
    ├── Prompts[] (이 도구를 어떻게 사용하나?)
    │   └── LangChain 호환 템플릿
    ├── Parameters (입력 스펙 - JSON Schema)
    ├── StructuredOutput (출력 스펙 - Pydantic/JSON Schema)
    └── SubAgent 참조 (어디서 설치하나?)
```

## 데이터 모델

### SubAgent (패키지/설치 단위)

```python
class SubAgent(BaseModel):
    """도구 패키지의 메타데이터 - 설치/실행 정보"""

    # 기본 정보
    name: str  # "tavily-toolkit"
    version: str  # "1.0.0"
    description: str
    author: str
    license: str

    # 분류
    category: str  # "search", "analysis", "generation"
    tags: List[str]

    # 설치 방법 (다중 지원)
    installations: List[Installation]

    # 실행 방법
    activation: Activation

    # 의존성
    dependencies: List[Dependency]

    # 제공하는 도구들 (참조)
    provides_tools: List[str]  # Tool 이름들
```

### Installation (언어/플랫폼 독립적)

```python
class Installation(BaseModel):
    """설치 방법 정보 - 다양한 플랫폼 지원"""

    method: Literal[
        "pip",       # Python
        "npm",       # Node.js
        "yarn",      # Node.js
        "go",        # Go
        "cargo",     # Rust
        "docker",    # 컨테이너
        "binary",    # 바이너리 다운로드
        "git",       # Git clone
        "remote",    # Remote API (설치 불필요)
    ]

    # 언어별 정보
    package_name: Optional[str]  # pip: pkg-name, npm: @org/pkg
    package_version: Optional[str]  # ">=1.0.0,<2.0.0"
    registry_url: Optional[str]  # Custom registry

    # Git
    repository: Optional[str]
    branch: Optional[str]

    # Docker
    image: Optional[str]

    # Binary
    download_url: Optional[str]
    checksum: Optional[str]

    # Remote
    api_endpoint: Optional[str]
    auth_method: Optional[str]

    # 후처리
    post_install_commands: List[str]

    # 플랫폼 제약
    platforms: Optional[List[str]]  # ["linux", "darwin", "win32"]
    arch: Optional[List[str]]  # ["x64", "arm64"]
```

### Activation (실행 방법)

```python
class Activation(BaseModel):
    """실행 방법 정보"""

    type: Literal[
        "cli",        # Command line
        "http",       # HTTP Server
        "grpc",       # gRPC Server
        "websocket",  # WebSocket
        "stdio",      # stdin/stdout
        "library",    # Import as library
        "remote",     # Remote API
    ]

    # CLI/stdio
    command: Optional[str]
    args: List[str]
    working_dir: Optional[str]

    # Server types
    host: Optional[str]
    port: Optional[int]
    protocol: Optional[str]
    health_check_endpoint: Optional[str]

    # Remote
    base_url: Optional[str]
    auth: Optional[Dict[str, Any]]

    # 환경 변수
    env_vars: Dict[str, EnvVar]
```

### Tool (기능 단위 - 검색 대상)

```python
class Tool(BaseModel):
    """개별 도구/기능 - 검색의 핵심 단위"""

    # 기본 정보
    name: str  # "web_search"
    display_name: str  # "Web Search"
    description: str
    category: str  # "search", "analysis", "generation"
    tags: List[str]

    # 소속 SubAgent (설치 정보 참조)
    subagent_name: str
    subagent_version: str

    # 프롬프트 (이 도구 사용법)
    prompts: List[ToolPrompt]

    # 입력 스펙
    parameters: ParameterSchema  # JSON Schema

    # 출력 스펙
    structured_output: StructuredOutputSchema

    # 프로토콜 정보
    protocol: str  # "langchain", "openai-function", "mcp"
    implementation_hint: Optional[str]  # "module.Class.method"
```

### ToolPrompt (도구별 프롬프트)

```python
class ToolPrompt(BaseModel):
    """도구를 사용하는 프롬프트 템플릿"""

    name: str  # "default", "detailed", "concise"
    description: str

    # LangChain 호환 포맷
    template_type: Literal["chat", "string", "few_shot"]

    # Chat template
    system_message: Optional[str]
    human_message_template: str
    ai_message_prefix: Optional[str]

    # Few-shot examples
    examples: List[Dict[str, str]]

    # Variables
    input_variables: List[str]
    partial_variables: Dict[str, Any]

    # 원본 템플릿 (Jinja2)
    template: str
```

### StructuredOutputSchema (출력 스펙)

```python
class StructuredOutputSchema(BaseModel):
    """구조화된 출력 스펙 - 여러 환경에서 재사용"""

    name: str
    description: str

    # JSON Schema (범용)
    json_schema: Dict[str, Any]

    # Pydantic 코드 (Python 환경)
    pydantic_code: Optional[str]

    # TypeScript 타입 (Node.js 환경)
    typescript_type: Optional[str]

    # JSON 예제
    examples: List[Dict[str, Any]]
```

## YAML 구조 (재설계)

```yaml
# SubAgent: 패키지/설치 단위
subagent:
  name: tavily-search-toolkit
  version: 1.0.0
  description: "Web search toolkit using Tavily API"
  category: search
  tags: [web-search, tavily, api]
  author: deepagents-team
  license: MIT

  # 설치 방법들 (다중 지원)
  installations:
    # Python
    - method: pip
      package_name: tavily-search-toolkit
      package_version: ">=1.0.0"

    # Node.js
    - method: npm
      package_name: "@deepagents/tavily-toolkit"
      package_version: "^1.0.0"

    # Docker
    - method: docker
      image: deepagents/tavily-toolkit:1.0.0

    # Remote API (설치 불필요)
    - method: remote
      api_endpoint: https://api.tavily.com/v1
      auth_method: bearer

  # 실행 방법
  activation:
    type: http
    port: 8080
    health_check_endpoint: /health
    env_vars:
      TAVILY_API_KEY:
        required: true
        description: "Tavily API key"

  dependencies:
    - type: api
      name: tavily
      required: true

# Tools: 개별 기능들 (검색 대상)
tools:
  - name: web_search
    display_name: "Web Search"
    description: "Search the web for current information"
    category: search
    tags: [web, search, real-time]

    # 어디서 설치?
    subagent_name: tavily-search-toolkit
    subagent_version: "1.0.0"

    # 어떻게 사용? (프롬프트)
    prompts:
      - name: default
        description: "Standard web search prompt"
        template_type: chat
        system_message: |
          You are a web search assistant.
          Use the web_search tool to find current information.
        human_message_template: |
          Search for: {query}
          Max results: {max_results}
          Include domains: {domains}
        input_variables: [query, max_results, domains]
        examples:
          - human: "Search for latest AI news, max 5 results"
            ai: "I'll search for latest AI news with max 5 results"

      - name: academic
        description: "Academic-focused search"
        template_type: chat
        system_message: |
          Focus on academic and scholarly sources.
        human_message_template: |
          Academic search: {query}
        input_variables: [query]

    # 입력 스펙
    parameters:
      type: object
      properties:
        query:
          type: string
          description: "Search query"
        max_results:
          type: integer
          default: 10
          minimum: 1
          maximum: 100
        domains:
          type: array
          items:
            type: string
      required: [query]

    # 출력 스펙 (다양한 형식 제공)
    structured_output:
      name: SearchResults
      description: "Web search results"

      # JSON Schema (범용)
      json_schema:
        type: object
        properties:
          results:
            type: array
            items:
              type: object
              properties:
                title:
                  type: string
                url:
                  type: string
                snippet:
                  type: string
                score:
                  type: number
        required: [results]

      # Pydantic (Python)
      pydantic_code: |
        from pydantic import BaseModel, HttpUrl
        from typing import List

        class SearchResult(BaseModel):
            title: str
            url: HttpUrl
            snippet: str
            score: float

        class SearchResults(BaseModel):
            results: List[SearchResult]

      # TypeScript (Node.js)
      typescript_type: |
        interface SearchResult {
          title: string;
          url: string;
          snippet: string;
          score: number;
        }

        interface SearchResults {
          results: SearchResult[];
        }

      examples:
        - results:
            - title: "AI News Today"
              url: "https://example.com"
              snippet: "Latest developments..."
              score: 0.95

    # 프로토콜 정보
    protocol: langchain
    implementation_hint: "tavily_toolkit.tools.WebSearchTool"

  - name: news_search
    # ... 다른 도구
```

## 사용 시나리오 (클라이언트 관점)

### 1. 도구 검색
```python
# Registry에서 검색
results = registry.search_tools("웹에서 최신 정보 검색")

tool = results[0]
# name: web_search
# subagent: tavily-search-toolkit
```

### 2. 설치 정보 조회
```python
# 이 도구를 사용하려면 어떻게 설치?
subagent = registry.get_subagent(tool.subagent_name)

# Python 환경
install = subagent.get_installation_for_platform("pip")
# → pip install tavily-search-toolkit>=1.0.0

# Node.js 환경
install = subagent.get_installation_for_platform("npm")
# → npm install @deepagents/tavily-toolkit

# Docker 환경
install = subagent.get_installation_for_platform("docker")
# → docker pull deepagents/tavily-toolkit:1.0.0
```

### 3. 프롬프트 사용
```python
# 프롬프트 가져오기
prompt = registry.get_tool_prompt("web_search", "default")

# LangChain에서 사용
from langchain.prompts import ChatPromptTemplate
template = ChatPromptTemplate.from_messages([
    ("system", prompt.system_message),
    ("human", prompt.human_message_template)
])

# 실제 사용
filled = template.format_messages(
    query="AI developments",
    max_results=5,
    domains=["arxiv.org"]
)
```

### 4. Structured Output 활용
```python
# 출력 스펙 가져오기
output_spec = registry.get_tool_output_schema("web_search")

# Python: Pydantic 클래스 생성
exec(output_spec.pydantic_code)
result = SearchResults(results=[...])

# Node.js: TypeScript 타입 사용
# (typescript_type을 파일로 저장)

# 범용: JSON Schema로 검증
from jsonschema import validate
validate(result_data, output_spec.json_schema)
```

### 5. 도구 실행 (클라이언트가 담당)
```python
# Registry는 정보만 제공, 실행은 클라이언트가 함
subagent = registry.get_subagent("tavily-search-toolkit")

if subagent.activation.type == "http":
    # HTTP 서버로 실행
    url = f"http://localhost:{subagent.activation.port}"
    response = requests.post(
        f"{url}/tools/web_search",
        json={"query": "AI news", "max_results": 5}
    )
elif subagent.activation.type == "cli":
    # CLI로 실행
    result = subprocess.run(
        [subagent.activation.command] + subagent.activation.args,
        input=json.dumps(params),
        capture_output=True
    )
```

## API 엔드포인트

```
# Tool 검색 (핵심)
POST /search/tools
  body: {query, category, tags, limit}
  return: [{tool, score, subagent_summary}]

# Tool 정보
GET /tools
GET /tools/{tool_name}
GET /tools/{tool_name}/prompts
GET /tools/{tool_name}/prompts/{prompt_name}
GET /tools/{tool_name}/schema
GET /tools/{tool_name}/parameters

# SubAgent 정보 (설치/실행)
GET /subagents
GET /subagents/{name}
GET /subagents/{name}/installations
GET /subagents/{name}/activation
GET /subagents/{name}/tools

# 통합 조회
GET /tools/{tool_name}/install
  → tool + subagent installation 정보 함께 반환
```

## 핵심 차이점

### 이전 설계 (잘못됨)
- SubAgent가 중심
- Registry가 실행 주체처럼 보임
- Python 중심적

### 새로운 설계 (올바름)
- **Tool이 검색 대상** (기능 중심)
- **SubAgent는 설치 메타데이터** (패키지 정보)
- **Registry는 카탈로그** (정보 제공자)
- **언어/플랫폼 독립적** (pip, npm, docker, binary, remote 등)
- **클라이언트가 실행** (Registry는 방법만 알려줌)

이 설계가 맞나요?
