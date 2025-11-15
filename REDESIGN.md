# SubAgent Registry - 재설계 문서

## 현재 문제점

현재 구현은 "SubAgent"를 중심으로 설계되었지만, 실제 목적은:
- **표준화된 도구(Tools)의 검색 엔진**
- **도구별 프롬프트 및 Structured Output 관리**
- **설치/설정 정보 제공**

## 올바른 개념 모델

```
Registry (검색 엔진)
├── Tools (핵심 - 1급 시민)
│   ├── Metadata (이름, 설명, 카테고리)
│   ├── Prompt (이 도구를 사용하는 프롬프트)
│   ├── Parameters (입력 스펙)
│   ├── StructuredOutput (출력 스펙)
│   └── Installation (어떻게 설치/실행하는가)
└── SubAgents (도구의 그룹/패키지)
    └── Tools[] (포함된 도구들)
```

## 새로운 데이터 모델

### Tool (핵심 엔티티)

```python
class Tool(BaseModel):
    """표준화된 도구 정의"""

    # 메타데이터
    name: str  # "web_search", "code_analyzer"
    display_name: str  # "Web Search"
    description: str  # "Search the web using Tavily API"
    category: str  # "search", "analysis", "generation"
    tags: List[str]

    # 프롬프트 (도구별)
    prompts: List[ToolPrompt]  # 이 도구를 사용하는 프롬프트들

    # 인터페이스
    parameters: ParameterSchema  # JSON Schema
    structured_output: StructuredOutputSchema  # Pydantic 스키마

    # 실행 정보
    provider: str  # "langchain", "mcp", "openai-function"
    implementation: ToolImplementation

    # 소속
    subagent_name: str  # 어떤 SubAgent에 속하는지
```

### ToolPrompt

```python
class ToolPrompt(BaseModel):
    """도구별 프롬프트 (LangChain 포맷)"""

    name: str  # "default", "detailed", "concise"
    template_type: Literal["chat", "string", "few-shot"]

    # LangChain 호환
    system_message: Optional[str]
    human_message_template: str
    few_shot_examples: List[Dict[str, str]]

    # 변수
    input_variables: List[str]
    partial_variables: Dict[str, str]

    # Jinja2 템플릿
    template: str
```

### StructuredOutputSchema

```python
class StructuredOutputSchema(BaseModel):
    """구조화된 출력 스펙"""

    name: str
    description: str

    # Pydantic 클래스를 JSON으로 저장
    schema_type: Literal["pydantic", "json_schema"]
    schema_def: Dict[str, Any]  # JSON Schema

    # 실제 Pydantic 코드 (선택적)
    pydantic_code: Optional[str]  # 재사용 가능한 코드

    # 예제
    examples: List[Dict[str, Any]]
```

### SubAgent (도구의 그룹)

```python
class SubAgent(BaseModel):
    """도구들의 패키지/그룹"""

    name: str
    version: str
    description: str

    # 제공하는 도구들
    tools: List[str]  # Tool 이름들

    # 설치 정보 (SubAgent 레벨)
    installation: Installation
    activation: Activation
    dependencies: List[Dependency]
```

## 새로운 YAML 구조

```yaml
# SubAgent 정의
subagent:
  name: research-toolkit
  version: 1.0.0
  description: "Research tools collection"

  # 설치 정보 (SubAgent 전체)
  installation:
    method: pip
    package_name: research-toolkit

  activation:
    type: stdio
    command: python
    args: [-m, research_toolkit]

# 도구들 (핵심)
tools:
  - name: web_search
    display_name: "Web Search"
    description: "Search the web using Tavily API"
    category: search
    tags: [web, search, tavily]

    # 이 도구의 프롬프트
    prompts:
      - name: default
        template_type: chat
        system_message: "You are a web search assistant."
        human_message_template: |
          Search for: {query}
          Max results: {max_results}
        input_variables: [query, max_results]

    # 파라미터 (입력)
    parameters:
      type: object
      properties:
        query:
          type: string
          description: "Search query"
        max_results:
          type: integer
          default: 10
      required: [query]

    # Structured Output (출력)
    structured_output:
      name: SearchResults
      schema_type: pydantic
      schema_def:
        properties:
          results:
            type: array
            items:
              type: object
              properties:
                title: {type: string}
                url: {type: string}
                snippet: {type: string}
      pydantic_code: |
        class SearchResult(BaseModel):
            title: str
            url: str
            snippet: str

        class SearchResults(BaseModel):
            results: List[SearchResult]

    # 구현 정보
    provider: langchain
    implementation:
      module: research_toolkit.tools
      class: WebSearchTool

  - name: academic_search
    # ... 다른 도구
```

## 검색 방식 변경

### 현재 (SubAgent 검색)
```
Query: "I need research capabilities"
→ SubAgent: research-agent (score: 0.92)
```

### 새로운 (Tool 검색)
```
Query: "I need to search academic papers"
→ Tool: academic_search (category: search)
  SubAgent: research-toolkit
  Prompt: default
  Output: AcademicPapers (Pydantic schema 제공)
  Installation: pip install research-toolkit
```

## API 변경

### 새로운 엔드포인트

```
GET  /tools/                      # 모든 도구 목록
GET  /tools/{tool_name}           # 도구 상세 정보
POST /search/tools                # 도구 검색 (핵심)
GET  /tools/{tool_name}/prompts   # 도구의 프롬프트들
GET  /tools/{tool_name}/schema    # Structured Output 스키마
GET  /tools/{tool_name}/install   # 설치 정보

GET  /subagents/                  # SubAgent 목록
GET  /subagents/{name}/tools      # SubAgent의 도구들
```

## 사용 시나리오

### 1. 도구 검색
```python
# "웹 검색 도구"를 찾고 싶음
results = client.post("/search/tools", json={
    "query": "search the web for information",
    "category": "search"
})

tool = results[0]
print(tool["name"])  # web_search
print(tool["subagent"])  # research-toolkit
```

### 2. 프롬프트 가져오기
```python
# 이 도구를 사용하는 프롬프트
prompts = client.get("/tools/web_search/prompts")

# LangChain에서 사용
from langchain.prompts import ChatPromptTemplate
template = ChatPromptTemplate.from_template(
    prompts[0]["human_message_template"]
)
```

### 3. Structured Output 스키마
```python
# Pydantic 스키마 가져오기
schema = client.get("/tools/web_search/schema")

# 코드 생성
exec(schema["pydantic_code"])
# 이제 SearchResults 클래스 사용 가능

# 또는 JSON Schema만 사용
json_schema = schema["schema_def"]
```

### 4. 설치 정보
```python
# 이 도구를 사용하려면?
install_info = client.get("/tools/web_search/install")
print(install_info["method"])  # pip
print(install_info["package"])  # research-toolkit
```

## 장점

1. **도구 중심 검색** - "X 기능을 하는 도구" 직접 검색
2. **프롬프트 재사용** - 도구별 최적화된 프롬프트
3. **Structured Output 공유** - Pydantic 코드를 여러 환경에서 재사용
4. **표준화** - 모든 도구가 동일한 인터페이스
5. **확장성** - 새로운 도구 추가가 쉬움

## 다음 단계

이 설계로 재구현하시겠습니까? 확인해주시면 진행하겠습니다.
