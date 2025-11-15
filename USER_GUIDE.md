# SubAgent Registry & Search Engine - User Guide

## 목차 (Table of Contents)

- [소개](#소개)
- [빠른 시작](#빠른-시작)
- [도구 검색](#도구-검색)
- [도구 정보 조회](#도구-정보-조회)
- [도구 설치 및 실행](#도구-설치-및-실행)
- [고급 검색](#고급-검색)
- [API 레퍼런스](#api-레퍼런스)
- [사용 예제](#사용-예제)

## 소개

SubAgent Registry는 다양한 AI 도구(Tools)와 에이전트 패키지(SubAgents)를 검색하고 관리할 수 있는 **도구 중심 레지스트리**입니다.

### 핵심 개념

- **Tools (도구)**: 개별 기능 단위 (예: `web_search`, `encrypt_data`, `classify_text`)
- **SubAgents (서브에이전트)**: 도구들을 제공하는 패키지/툴킷
- **Semantic Search (의미 검색)**: 자연어로 원하는 도구 검색
- **Multi-Platform (멀티 플랫폼)**: Python, Node.js, Rust, Go, Docker, Remote API 등 지원

### 레지스트리의 역할

레지스트리는 **정보 카탈로그**로서:
- ✅ 도구의 설치 방법 제공
- ✅ 도구의 실행 방법 안내
- ✅ 프롬프트 템플릿 제공
- ✅ 파라미터 스키마 제공
- ❌ 도구를 직접 실행하지 않음 (사용자가 설치 후 실행)

## 빠른 시작

### 1. 서버 실행

```bash
# 레지스트리 서버 시작
python -m registry_engine.api.app_v2

# 또는 uvicorn 사용
uvicorn registry_engine.api.app_v2:app --reload
```

서버 실행 후 브라우저에서 API 문서 확인:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 2. 첫 검색

```bash
# 웹 검색 도구 찾기
curl -X POST "http://localhost:8000/search/tools" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "search the web",
    "top_k": 5
  }'
```

### 3. 도구 정보 조회

```bash
# 특정 도구의 상세 정보
curl "http://localhost:8000/tools/web_search"
```

### 4. 설치 방법 확인

```bash
# 도구의 설치 및 실행 방법
curl "http://localhost:8000/tools/web_search/install"
```

## 도구 검색

### 기본 검색 (Semantic Search)

자연어로 원하는 기능을 검색합니다.

```bash
curl -X POST "http://localhost:8000/search/tools" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "암호화하고 싶어요",
    "top_k": 10
  }'
```

**Python 예제:**

```python
import httpx
import asyncio

async def search_tools(query: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/search/tools",
            json={"query": query, "top_k": 5}
        )
        result = response.json()

        print(f"검색어: {query}")
        print(f"결과: {result['total']}개")

        for tool in result['results']:
            print(f"\n- {tool['display_name']}")
            print(f"  설명: {tool['description']}")
            print(f"  카테고리: {tool['category']}")
            print(f"  점수: {tool.get('score', 'N/A')}")

# 사용
asyncio.run(search_tools("이미지 배경 제거"))
```

### 카테고리별 검색

```bash
curl "http://localhost:8000/search/tools/by-category?category=security&limit=20"
```

### 자동완성 (Autocomplete)

```bash
curl "http://localhost:8000/search/suggest?q=encr"
```

**응답 예시:**
```json
{
  "suggestions": [
    {
      "name": "encrypt_data",
      "display_name": "Data Encryption",
      "category": "security"
    }
  ],
  "total": 1
}
```

### 유사 도구 찾기

```bash
curl "http://localhost:8000/search/similar/web_search"
```

## 도구 정보 조회

### 도구 상세 정보

```bash
curl "http://localhost:8000/tools/classify_text"
```

**응답 예시:**
```json
{
  "name": "classify_text",
  "display_name": "Text Classification",
  "description": "Classify text using fine-tuned transformer models",
  "category": "machine-learning",
  "tags": ["nlp", "classification", "transformers"],
  "subagent_name": "ml-inference-service",
  "protocol": "openai",
  "parameters": {
    "type": "object",
    "properties": {
      "text": {
        "type": "string",
        "description": "Text to classify"
      }
    },
    "required": ["text"]
  }
}
```

### 프롬프트 템플릿 조회

```bash
curl "http://localhost:8000/tools/classify_text/prompts"
```

**응답 예시:**
```json
{
  "tool_name": "classify_text",
  "prompts": [
    {
      "name": "default",
      "description": "Standard classification prompt",
      "template_type": "chat",
      "system_message": "You are a text classification assistant...",
      "human_message_template": "Classify this text: {text}...",
      "input_variables": ["text", "model_name"],
      "partial_variables": {
        "model_name": "distilbert-base-uncased"
      }
    }
  ]
}
```

### Structured Output 스키마

```bash
curl "http://localhost:8000/tools/classify_text/schema"
```

**응답 예시:**
```json
{
  "tool_name": "classify_text",
  "structured_output": {
    "name": "ClassificationResult",
    "json_schema": {
      "type": "object",
      "properties": {
        "predicted_class": {"type": "string"},
        "confidence_score": {"type": "number"}
      }
    },
    "pydantic_code": "class ClassificationResult(BaseModel): ...",
    "typescript_type": "interface ClassificationResult { ... }"
  }
}
```

### 설치 및 실행 정보

```bash
curl "http://localhost:8000/tools/classify_text/install"
```

**응답 예시:**
```json
{
  "tool_name": "classify_text",
  "subagent": {
    "name": "ml-inference-service",
    "version": "1.5.2"
  },
  "installations": [
    {
      "method": "docker",
      "platform_id": "docker-http",
      "image": "mlops/inference-service:1.5.2",
      "requires_install": true
    }
  ],
  "activations": [
    {
      "type": "http_endpoint",
      "platform_id": "docker-http",
      "endpoint": "/api/classify",
      "method": "POST"
    }
  ],
  "usage_example": "docker run -p 8080:8080 mlops/inference-service:1.5.2"
}
```

## 도구 설치 및 실행

### 설치 단계

1. **설치 정보 확인**
   ```bash
   curl "http://localhost:8000/tools/{tool_name}/install"
   ```

2. **플랫폼별 설치**

   **Python (pip):**
   ```bash
   pip install tavily-search-toolkit
   ```

   **Node.js (npm):**
   ```bash
   npm install @vision-tools/image-processor
   ```

   **Rust (cargo):**
   ```bash
   cargo install crypto-toolkit
   ```

   **Go:**
   ```bash
   go install github.com/dbtools/migration-toolkit@v2.3.0
   ```

   **Docker:**
   ```bash
   docker pull mlops/inference-service:1.5.2
   docker run -p 8080:8080 mlops/inference-service:1.5.2
   ```

   **Binary (직접 다운로드):**
   ```bash
   wget https://github.com/.../crypto-toolkit-linux-x64
   chmod +x crypto-toolkit-linux-x64
   ```

3. **환경 변수 설정**
   ```bash
   export API_KEY="your-api-key"
   export MODEL_CACHE_DIR="/path/to/cache"
   ```

4. **도구 실행**

   **CLI 도구:**
   ```bash
   # 기본 실행
   tavily-toolkit search "AI news"

   # 서브커맨드 방식
   crypto-toolkit encrypt --input data.txt
   ```

   **HTTP API:**
   ```bash
   curl -X POST http://localhost:8080/api/classify \
     -H "Content-Type: application/json" \
     -d '{"text": "This is amazing!"}'
   ```

### Remote API (설치 불필요)

Remote API는 설치가 필요 없습니다:

```python
import httpx

async def use_remote_tool():
    headers = {"Authorization": f"Bearer {API_KEY}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.weathertech.ai/v3/weather/current",
            params={"location": "Seoul"},
            headers=headers
        )
    return response.json()
```

## 고급 검색

### 다중 필터 검색 (Faceted Search)

```bash
curl -X POST "http://localhost:8000/search/advanced" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "process images",
    "categories": ["image-processing"],
    "tags": ["ai", "enhancement"],
    "protocols": ["langchain"],
    "sort_by": "relevance",
    "limit": 20
  }'
```

**응답:**
```json
{
  "results": [...],
  "total": 15,
  "facets": {
    "categories": [
      {"value": "image-processing", "count": 10},
      {"value": "computer-vision", "count": 5}
    ],
    "tags": [
      {"value": "ai", "count": 12},
      {"value": "enhancement", "count": 8}
    ],
    "protocols": [
      {"value": "langchain", "count": 15}
    ]
  },
  "query_time_ms": 45.2
}
```

### 사용 가능한 필터 조회

```bash
curl "http://localhost:8000/search/facets"
```

### 통계 정보

```bash
curl "http://localhost:8000/search/statistics"
```

**응답:**
```json
{
  "total_tools": 127,
  "total_subagents": 34,
  "recent_tools_30d": 12,
  "categories": {
    "search": 15,
    "security": 22,
    "image-processing": 18,
    "machine-learning": 31
  },
  "protocols": {
    "langchain": 89,
    "openai": 38
  }
}
```

## API 레퍼런스

### 검색 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|----------|--------|------|
| `/search/tools` | POST | 의미 검색 (Semantic) |
| `/search/tools/by-category` | GET | 카테고리별 검색 |
| `/search/advanced` | POST | 다중 필터 검색 |
| `/search/facets` | GET | 필터 옵션 조회 |
| `/search/suggest` | GET | 자동완성 |
| `/search/similar/{tool_name}` | GET | 유사 도구 찾기 |
| `/search/statistics` | GET | 통계 정보 |

### 도구 정보 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|----------|--------|------|
| `/tools/` | GET | 도구 목록 |
| `/tools/{name}` | GET | 도구 상세 정보 |
| `/tools/{name}/prompts` | GET | 프롬프트 템플릿 |
| `/tools/{name}/schema` | GET | Structured Output 스키마 |
| `/tools/{name}/install` | GET | 설치 및 실행 정보 |

### SubAgent 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|----------|--------|------|
| `/subagents/` | GET | SubAgent 목록 |
| `/subagents/{name}` | GET | SubAgent 상세 정보 |
| `/subagents/{name}/tools` | GET | SubAgent의 도구 목록 |

## 사용 예제

### 예제 1: 웹 검색 도구 찾고 사용하기

```python
import httpx
import asyncio

async def find_and_use_web_search():
    # 1. 웹 검색 도구 찾기
    async with httpx.AsyncClient() as client:
        # 검색
        search_response = await client.post(
            "http://localhost:8000/search/tools",
            json={"query": "search the web", "top_k": 1}
        )
        tools = search_response.json()['results']

        if not tools:
            print("웹 검색 도구를 찾을 수 없습니다.")
            return

        tool = tools[0]
        print(f"찾은 도구: {tool['display_name']}")

        # 2. 설치 정보 확인
        install_response = await client.get(
            f"http://localhost:8000/tools/{tool['name']}/install"
        )
        install_info = install_response.json()

        print("\n설치 방법:")
        for installation in install_info['installations']:
            if installation['method'] == 'pip':
                print(f"  pip install {installation['package_name']}")

        # 3. 프롬프트 템플릿 가져오기
        prompts_response = await client.get(
            f"http://localhost:8000/tools/{tool['name']}/prompts"
        )
        prompts = prompts_response.json()['prompts']

        print(f"\n프롬프트 템플릿: {prompts[0]['name']}")
        print(f"  {prompts[0]['human_message_template']}")

asyncio.run(find_and_use_web_search())
```

### 예제 2: 카테고리별 도구 탐색

```python
async def explore_by_category(category: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:8000/search/tools/by-category",
            params={"category": category, "limit": 10}
        )
        result = response.json()

        print(f"\n{category} 카테고리의 도구들:")
        print(f"총 {result['total']}개")

        for tool in result['results']:
            print(f"\n• {tool['display_name']}")
            print(f"  {tool['description']}")
            print(f"  태그: {', '.join(tool['tags'])}")

# 사용
asyncio.run(explore_by_category("security"))
asyncio.run(explore_by_category("image-processing"))
```

### 예제 3: 도구 비교하기

```python
async def compare_similar_tools(tool_name: str):
    async with httpx.AsyncClient() as client:
        # 원본 도구 정보
        tool_response = await client.get(
            f"http://localhost:8000/tools/{tool_name}"
        )
        original = tool_response.json()

        # 유사 도구 찾기
        similar_response = await client.get(
            f"http://localhost:8000/search/similar/{tool_name}"
        )
        similar_tools = similar_response.json()['results']

        print(f"'{original['display_name']}' 와 유사한 도구들:\n")

        for tool in similar_tools[:5]:
            print(f"• {tool['display_name']} (유사도: {tool.get('score', 'N/A')})")
            print(f"  {tool['description']}")
            print(f"  SubAgent: {tool['subagent_name']}\n")

asyncio.run(compare_similar_tools("encrypt_data"))
```

### 예제 4: 고급 검색 with 필터

```python
async def advanced_search_example():
    async with httpx.AsyncClient() as client:
        # 먼저 사용 가능한 필터 확인
        facets_response = await client.get(
            "http://localhost:8000/search/facets"
        )
        facets = facets_response.json()

        print("사용 가능한 카테고리:")
        for cat in facets['categories'][:5]:
            print(f"  - {cat['value']} ({cat['count']}개)")

        # 필터를 적용한 검색
        search_response = await client.post(
            "http://localhost:8000/search/advanced",
            json={
                "query": "process and enhance",
                "categories": ["image-processing"],
                "tags": ["ai"],
                "sort_by": "relevance",
                "limit": 5
            }
        )
        result = search_response.json()

        print(f"\n검색 결과: {result['total']}개")
        print(f"검색 시간: {result['query_time_ms']:.2f}ms\n")

        for tool in result['results']:
            print(f"• {tool['display_name']}")
            print(f"  점수: {tool.get('score', 'N/A')}")

asyncio.run(advanced_search_example())
```

### 예제 5: CLI 래퍼 만들기

```python
#!/usr/bin/env python3
"""Simple CLI wrapper for the registry."""

import click
import httpx
import asyncio
from rich import print
from rich.table import Table

@click.group()
def cli():
    """SubAgent Registry CLI"""
    pass

@cli.command()
@click.argument('query')
@click.option('--limit', default=5, help='Number of results')
def search(query, limit):
    """Search for tools"""
    async def _search():
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/search/tools",
                json={"query": query, "top_k": limit}
            )
            return response.json()

    result = asyncio.run(_search())

    table = Table(title=f"Search Results for '{query}'")
    table.add_column("Tool", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Category", style="green")

    for tool in result['results']:
        table.add_row(
            tool['display_name'],
            tool['description'][:50] + "...",
            tool['category']
        )

    print(table)

@cli.command()
@click.argument('tool_name')
def info(tool_name):
    """Get tool information"""
    async def _info():
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://localhost:8000/tools/{tool_name}"
            )
            return response.json()

    tool = asyncio.run(_info())

    print(f"\n[bold cyan]{tool['display_name']}[/bold cyan]")
    print(f"[dim]{tool['description']}[/dim]\n")
    print(f"Category: {tool['category']}")
    print(f"Tags: {', '.join(tool['tags'])}")
    print(f"SubAgent: {tool['subagent_name']}")
    print(f"Protocol: {tool['protocol']}")

@cli.command()
@click.argument('tool_name')
def install(tool_name):
    """Get installation instructions"""
    async def _install():
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://localhost:8000/tools/{tool_name}/install"
            )
            return response.json()

    info = asyncio.run(_install())

    print(f"\n[bold]Installation for {info['tool_name']}[/bold]\n")

    for installation in info['installations']:
        print(f"[cyan]{installation['method'].upper()}[/cyan]")
        if installation['method'] == 'pip':
            print(f"  pip install {installation['package_name']}")
        elif installation['method'] == 'docker':
            print(f"  docker pull {installation.get('image')}")
        print()

if __name__ == '__main__':
    cli()
```

**사용법:**
```bash
# 도구 검색
python registry_cli.py search "encrypt files"

# 도구 정보
python registry_cli.py info encrypt_data

# 설치 방법
python registry_cli.py install encrypt_data
```

## 문제 해결

### 검색 결과가 없을 때

1. **더 일반적인 검색어 사용**
   ```bash
   # ❌ 너무 구체적
   "AES-256-GCM encryption with PBKDF2"

   # ✅ 적절함
   "encrypt data"
   ```

2. **카테고리 확인**
   ```bash
   curl "http://localhost:8000/search/facets"
   ```

3. **태그로 필터링**
   ```bash
   curl -X POST "http://localhost:8000/search/advanced" \
     -d '{"tags": ["encryption"]}'
   ```

### 서버 연결 실패

```bash
# 서버 상태 확인
curl http://localhost:8000/health

# 로그 확인
python -m registry_engine.api.app_v2 --log-level debug
```

### 도구 설치 실패

1. 설치 정보 재확인
2. 환경 변수 확인
3. 의존성 확인 (dependencies 필드)

## 다음 단계

- **기여하기**: 새로운 도구를 추가하려면 [CONTRIBUTION_GUIDE.md](CONTRIBUTION_GUIDE.md) 참조
- **아키텍처**: 시스템 구조는 [ARCHITECTURE.md](ARCHITECTURE.md) 참조
- **설치-실행 관계**: [INSTALLATION_ACTIVATION.md](INSTALLATION_ACTIVATION.md) 참조

## 지원 및 문의

- **예제**: `examples_v2/` 디렉토리의 YAML 파일 참조
- **API 문서**: http://localhost:8000/docs
- **이슈**: GitHub Issues에 문의
