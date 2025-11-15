
# Product Requirements Document (PRD)
# SubAgent Registry & Search Engine

**Version:** 1.0
**Date:** 2025-11-15
**Author:** DeepAgents Team
**Status:** Draft

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Background & Motivation](#background--motivation)
3. [Goals & Objectives](#goals--objectives)
4. [Target Users](#target-users)
5. [Core Features](#core-features)
6. [System Architecture](#system-architecture)
7. [Technical Specifications](#technical-specifications)
8. [Data Models](#data-models)
9. [API Specifications](#api-specifications)
10. [Implementation Phases](#implementation-phases)
11. [Success Metrics](#success-metrics)
12. [Constraints & Considerations](#constraints--considerations)
13. [Future Enhancements](#future-enhancements)

---

## Executive Summary

**SubAgent Registry**는 다양한 서브에이전트들의 메타데이터, 설치 방법, 실행 스펙, 프롬프트 템플릿을 중앙 집중식으로 관리하는 검색 엔진입니다. MCP(Model Context Protocol) 서버와 유사한 개념으로, 에이전트 구현체 자체를 관리하는 것이 아니라 **"어떻게 찾고, 설치하고, 실행하는가"**에 대한 정보를 제공합니다.

### Key Value Propositions

1. **검색 엔진**: RAG 기반 시맨틱 검색으로 태스크에 맞는 서브에이전트 발견
2. **메타데이터 관리**: 설치법, 실행 방법, 인터페이스 스펙의 중앙 집중 관리
3. **프롬프트 관리**: LangChain 프롬프트 템플릿 저장 및 버전 관리
4. **다양한 바인딩**: Git, NPM, Pip, Docker, 원격 API 등 다양한 설치 방법 지원
5. **Structured Output 스펙**: Pydantic 모델, JSON Schema 관리

---

## Background & Motivation

### Current Challenges

1. **서브에이전트 발견의 어려움**
   - 사용자가 특정 태스크에 적합한 서브에이전트를 찾기 어려움
   - 수동으로 코드베이스를 검색하거나 문서를 읽어야 함

2. **설치 정보 분산**
   - 각 서브에이전트마다 설치 방법이 다름 (Git clone, npm install, pip install 등)
   - 설치 문서가 README에 분산되어 있어 자동화 어려움

3. **프롬프트 관리 부재**
   - 프롬프트가 코드에 하드코딩되어 있어 수정 및 버전 관리 어려움
   - 다양한 환경(개발, 프로덕션)에서 프롬프트를 쉽게 확인/수정할 수 없음

4. **인터페이스 표준화 부족**
   - 서브에이전트가 제공하는 도구, Structured Output 스펙이 비표준화
   - 런타임에 동적으로 인터페이스를 파악하기 어려움

### Inspiration

- **Anthropic Skills Framework**: Progressive disclosure와 메타데이터 기반 라우팅
- **MCP (Model Context Protocol)**: 표준화된 인터페이스와 서버 발견 메커니즘
- **NPM Registry**: 패키지 검색, 버전 관리, 의존성 해결
- **Docker Hub**: 컨테이너 이미지 레지스트리 및 검색

---

## Goals & Objectives

### Primary Goals

1. **G1: 서브에이전트 검색 엔진 구축**
   - 자연어 쿼리로 태스크에 맞는 서브에이전트를 찾을 수 있음
   - RAG 기반 시맨틱 검색으로 정확도 90% 이상

2. **G2: 메타데이터 중앙 집중 관리**
   - 모든 서브에이전트의 설치법, 실행법, 인터페이스를 한 곳에서 관리
   - YAML/JSON 기반 선언적 정의

3. **G3: 프롬프트 템플릿 관리 시스템**
   - Jinja2 템플릿 기반 프롬프트 저장/조회/렌더링
   - 버전 관리 및 다중 환경 지원

4. **G4: DeepAgents 통합**
   - DeepAgents CLI/API에서 레지스트리를 클라이언트로 사용
   - 자동 설치 및 실행 지원

### Secondary Goals

- 커뮤니티 기여를 위한 관리 도구 제공
- 서브에이전트 사용 통계 및 분석
- 다중 레지스트리 지원 (Public, Private)

---

## Target Users

### Primary Users

1. **AI 에이전트 개발자**
   - DeepAgents를 사용하여 복잡한 에이전트 시스템 구축
   - 재사용 가능한 서브에이전트를 찾아 통합하고자 함

2. **DevOps 엔지니어**
   - 에이전트 배포 및 운영 자동화
   - 프롬프트 및 설정을 중앙에서 관리하고자 함

3. **연구자**
   - 다양한 도메인의 전문 에이전트 발견
   - 학술 연구를 위한 에이전트 조합 실험

### Secondary Users

4. **서브에이전트 작성자**
   - 자신의 서브에이전트를 레지스트리에 등록
   - 커뮤니티와 공유

5. **엔터프라이즈 사용자**
   - 프라이빗 레지스트리 운영
   - 조직 내부 서브에이전트 관리

---

## Core Features

### F1: RAG 기반 검색 엔진 (P0)

**Description**: 자연어 쿼리로 서브에이전트를 검색하는 시스템

**User Stories**:
- AS a developer, I WANT TO search "research with academic citations" SO THAT I can find relevant research agents
- AS a user, I WANT TO see search results ranked by relevance SO THAT I can choose the best option

**Acceptance Criteria**:
- [ ] Qdrant 벡터 DB 통합
- [ ] OpenAI/Anthropic 임베딩 지원
- [ ] 시맨틱 검색 정확도 90% 이상
- [ ] 도메인, 태그 필터링 지원
- [ ] 검색 결과 스코어 및 랭킹 제공

**Technical Details**:
- Qdrant collection: `subagents`
- Embedding dimension: 1536 (OpenAI ada-002)
- Distance metric: Cosine similarity
- Re-ranking: 메타데이터 기반 부스팅 (priority, downloads, rating)

---

### F2: 메타데이터 관리 시스템 (P0)

**Description**: 서브에이전트의 모든 메타데이터를 SQLite DB에 저장 및 관리

**User Stories**:
- AS an admin, I WANT TO import YAML files SO THAT I can add new subagents to the registry
- AS a developer, I WANT TO query subagent metadata via API SO THAT I can integrate it into my application

**Acceptance Criteria**:
- [ ] SQLite 스키마 정의 (subagents, prompts, interfaces, installations, activations 등)
- [ ] YAML/JSON 임포트 CLI 도구
- [ ] CRUD API (Create, Read, Update, Delete)
- [ ] 데이터 검증 (Pydantic)

**Data Entities**:
- SubAgent (name, version, description, domain, tags, capabilities, use_cases)
- Installation (method, repository, package, image, post_install_commands)
- Activation (type, command, args, env_vars, health_check)
- Prompt (name, template, variables, format)
- Interface (protocol, tools, structured_outputs)

---

### F3: 프롬프트 템플릿 관리 (P0)

**Description**: LangChain 프롬프트를 DB에 저장하고 조회/렌더링하는 시스템

**User Stories**:
- AS a developer, I WANT TO fetch prompt templates via API SO THAT I can use them in my agent
- AS an admin, I WANT TO update prompts without code changes SO THAT I can quickly iterate
- AS a user, I WANT TO render prompts with variables SO THAT I can preview the final output

**Acceptance Criteria**:
- [ ] Jinja2 템플릿 지원
- [ ] 변수 정의 및 검증
- [ ] 프롬프트 렌더링 API
- [ ] 버전 관리 (optional: Git 기반)
- [ ] 다중 프롬프트 지원 (system, user_template, few_shot_examples 등)

**API Endpoints**:
- `GET /prompts/{subagent_name}` - 모든 프롬프트 조회
- `GET /prompts/{subagent_name}/{prompt_name}` - 특정 프롬프트 조회
- `POST /prompts/{subagent_name}/{prompt_name}/render` - 프롬프트 렌더링

---

### F4: 설치 정보 관리 (P0)

**Description**: 다양한 설치 방법 (Git, NPM, Pip, Docker, Remote API)에 대한 메타데이터 저장

**User Stories**:
- AS a developer, I WANT TO see installation instructions SO THAT I can install the subagent
- AS a CLI, I WANT TO automatically install subagents based on metadata SO THAT users don't have to manually install

**Acceptance Criteria**:
- [ ] 지원 설치 방법: Git, NPM, Pip, Docker, Remote
- [ ] Post-install 스크립트 지원
- [ ] 대체 설치 방법 (alternatives) 지원
- [ ] 의존성 정보 저장

**Installation Methods**:

| Method | Fields | Example |
|--------|--------|---------|
| Git | repository, branch, commit | `git clone https://github.com/user/agent` |
| NPM | package_name, package_version | `npm install @deepagents/research@1.0.0` |
| Pip | package_name, package_version | `pip install deepagents-research==1.0.0` |
| Docker | image | `docker pull deepagents/research:1.0.0` |
| Remote | url, auth | `http://api.example.com/agents/research` |

---

### F5: 실행/활성화 정보 관리 (P0)

**Description**: 서브에이전트 실행 방법 (stdio, HTTP, MCP 등) 메타데이터 관리

**User Stories**:
- AS a launcher, I WANT TO know how to execute a subagent SO THAT I can start it properly
- AS a developer, I WANT TO see environment variable requirements SO THAT I can configure the subagent

**Acceptance Criteria**:
- [ ] 지원 활성화 타입: stdio, HTTP, MCP, SSE, WebSocket
- [ ] 명령어, 인자, 작업 디렉토리 정의
- [ ] 환경 변수 정의 (required, optional, default)
- [ ] Health check 설정

**Activation Types**:

| Type | Use Case | Fields |
|------|----------|--------|
| stdio | LangChain subagent | command, args, working_dir |
| HTTP | REST API server | command, args, health_check (endpoint) |
| MCP | Model Context Protocol | protocol, capabilities |
| SSE | Server-Sent Events | url, auth |
| WebSocket | Real-time communication | url, auth |

---

### F6: 인터페이스 스펙 관리 (P1)

**Description**: 서브에이전트가 제공하는 도구, Structured Output 스키마 관리

**User Stories**:
- AS a developer, I WANT TO see what tools a subagent provides SO THAT I know what it can do
- AS a system, I WANT TO load Structured Output schemas SO THAT I can validate outputs

**Acceptance Criteria**:
- [ ] 도구 스키마 저장 (name, description, parameters)
- [ ] Structured Output 스키마 저장 (Pydantic, JSON Schema)
- [ ] 프로토콜 정의 (LangChain, MCP, OpenAI Function)
- [ ] 스키마 검증

**Structured Output Schema Example**:
```json
{
  "name": "ResearchReport",
  "schema_type": "pydantic",
  "schema": {
    "properties": {
      "title": {"type": "string"},
      "summary": {"type": "string"},
      "citations": {
        "type": "array",
        "items": {"type": "string"}
      }
    },
    "required": ["title", "summary"]
  }
}
```

---

### F7: REST API 서버 (P0)

**Description**: FastAPI 기반 REST API로 레지스트리 데이터 노출

**User Stories**:
- AS a client application, I WANT TO query the registry via HTTP SO THAT I can integrate it
- AS a developer, I WANT TO use standard REST endpoints SO THAT integration is straightforward

**Acceptance Criteria**:
- [ ] FastAPI 프레임워크 사용
- [ ] OpenAPI (Swagger) 문서 자동 생성
- [ ] Authentication (optional: API Key, OAuth)
- [ ] Rate limiting
- [ ] CORS 지원

**API Categories**:
- Search API (`/search/*`)
- SubAgents API (`/subagents/*`)
- Prompts API (`/prompts/*`)
- Admin API (`/admin/*`)

---

### F8: DeepAgents 클라이언트 통합 (P0)

**Description**: DeepAgents에서 레지스트리를 클라이언트로 사용

**User Stories**:
- AS a DeepAgents user, I WANT TO automatically discover subagents SO THAT I don't need to manually configure them
- AS a DeepAgents agent, I WANT TO fetch prompts from the registry SO THAT they are centrally managed

**Acceptance Criteria**:
- [ ] `RegistryClient` 클래스 구현 (httpx 기반)
- [ ] `RegistrySubAgentMiddleware` 구현
- [ ] 자동 설치 기능
- [ ] 프롬프트 자동 로드
- [ ] CLI 명령어 추가 (`deepagents registry search`, `deepagents subagent install`)

**Integration Points**:
- `libs/deepagents/deepagents/registry/` - 클라이언트 코드
- `libs/deepagents/deepagents/middleware/registry_subagents.py` - 미들웨어
- `libs/deepagents-cli/deepagents_cli/registry_commands.py` - CLI 명령어

---

### F9: 관리 CLI 도구 (P1)

**Description**: 레지스트리 관리를 위한 CLI 도구

**User Stories**:
- AS an admin, I WANT TO import YAML files SO THAT I can bulk add subagents
- AS an admin, I WANT TO rebuild the vector index SO THAT search reflects latest changes

**Acceptance Criteria**:
- [ ] `registry-cli import <file.yaml>` - YAML 임포트
- [ ] `registry-cli list` - 서브에이전트 목록
- [ ] `registry-cli search <query>` - 검색 테스트
- [ ] `registry-cli reindex` - 벡터 인덱스 재구축
- [ ] `registry-cli validate <file.yaml>` - YAML 검증

---

### F10: Admin UI (P2)

**Description**: 웹 기반 관리 인터페이스 (Optional)

**User Stories**:
- AS an admin, I WANT TO manage subagents via web UI SO THAT I don't need to use CLI
- AS a user, I WANT TO browse subagents visually SO THAT discovery is easier

**Acceptance Criteria**:
- [ ] 서브에이전트 목록 및 검색
- [ ] 상세 정보 조회
- [ ] 프롬프트 편집기
- [ ] 사용 통계 대시보드

**Tech Stack**: React, Next.js, or Streamlit

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   External Clients                           │
│  - DeepAgents CLI                                            │
│  - DeepAgents Python API                                     │
│  - Custom Applications                                       │
└────────────────────┬────────────────────────────────────────┘
                     │ REST API (HTTP/JSON)
                     ↓
┌─────────────────────────────────────────────────────────────┐
│           SubAgent Registry Engine                           │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         API Layer (FastAPI)                          │  │
│  │  - /search/* - Search endpoints                      │  │
│  │  - /subagents/* - SubAgent CRUD                      │  │
│  │  - /prompts/* - Prompt management                    │  │
│  │  - /admin/* - Admin operations                       │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│  ┌────────────────────┴─────────────────────────────────┐  │
│  │         Business Logic Layer                         │  │
│  │  - SubAgentRetriever (RAG search)                    │  │
│  │  - SubAgentIndexer (Vector indexing)                 │  │
│  │  - PromptManager (Template rendering)                │  │
│  │  - SubAgentDB (Database operations)                  │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│  ┌────────────────────┴─────────────────────────────────┐  │
│  │         Data Layer                                   │  │
│  │  ┌──────────────┐           ┌───────────────┐       │  │
│  │  │   SQLite     │           │    Qdrant     │       │  │
│  │  │ (Metadata)   │◄─────────►│ (Vector DB)   │       │  │
│  │  └──────────────┘           └───────────────┘       │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Component Diagram

```
registry_engine/
├── api/
│   ├── app.py                    [FastAPI application]
│   ├── routes/
│   │   ├── search.py             [Search endpoints]
│   │   ├── subagents.py          [SubAgent CRUD]
│   │   ├── prompts.py            [Prompt management]
│   │   └── admin.py              [Admin operations]
│   └── dependencies.py           [DI container]
│
├── database/
│   ├── sqlite.py                 [SQLite operations]
│   ├── qdrant.py                 [Qdrant operations]
│   └── migrations/               [DB schema migrations]
│
├── search/
│   ├── indexer.py                [Vector indexing]
│   ├── retriever.py              [RAG search]
│   └── ranker.py                 [Result ranking]
│
├── prompts/
│   ├── manager.py                [Prompt CRUD]
│   └── renderer.py               [Jinja2 rendering]
│
└── models/
    ├── subagent.py               [Pydantic models]
    ├── prompt.py
    └── interface.py
```

---

## Technical Specifications

### Tech Stack

| Component | Technology | Justification |
|-----------|------------|---------------|
| **API Framework** | FastAPI | High performance, async support, auto OpenAPI docs |
| **Database (Metadata)** | SQLite | Lightweight, serverless, good for structured data |
| **Vector DB** | Qdrant | Fast similarity search, Python client, open source |
| **Embeddings** | OpenAI ada-002 | High quality, 1536 dimensions, cost-effective |
| **Template Engine** | Jinja2 | Industry standard, powerful, LangChain compatible |
| **Validation** | Pydantic v2 | Type safety, JSON schema generation |
| **HTTP Client** | httpx | Async support, modern API |
| **CLI** | Typer | User-friendly, auto-completion |
| **Testing** | pytest | Standard Python testing framework |

### Dependencies

```toml
[project]
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "sqlalchemy>=2.0.0",
    "pydantic>=2.0.0",
    "qdrant-client>=1.7.0",
    "langchain-core>=0.1.0",
    "langchain-openai>=0.0.5",
    "jinja2>=3.1.0",
    "httpx>=0.25.0",
    "typer>=0.9.0",
    "pyyaml>=6.0",
    "python-multipart>=0.0.6",
]

[dependency-groups]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]
```

### Infrastructure

**Development**:
- SQLite file: `data/registry.db`
- Qdrant: In-memory mode or local Docker container

**Production**:
- SQLite or PostgreSQL (for write-heavy workloads)
- Qdrant Cloud or self-hosted cluster
- API Server: Docker container, deployed on Cloud Run / ECS / K8s

### Performance Requirements

| Metric | Target | Notes |
|--------|--------|-------|
| **Search Latency** | < 200ms (p95) | Including embedding generation |
| **API Response Time** | < 100ms (p95) | For non-search endpoints |
| **Throughput** | 100 req/s | Single instance |
| **Vector Index Size** | < 1GB | For 10,000 subagents |
| **Database Size** | < 500MB | SQLite file |

---

## Data Models

### SQLite Schema

See [Technical Specifications Section 1](#1-데이터베이스-스키마-sqlite) for complete schema.

Key tables:
- `subagents` - Core metadata
- `prompts` - Prompt templates
- `interfaces` - Tool schemas, structured outputs
- `installations` - Installation methods
- `activations` - Execution configurations
- `examples` - Usage examples
- `dependencies` - Dependencies

### Pydantic Models

```python
class SubAgentMetadata(BaseModel):
    name: str
    version: str
    description: str
    domain: str
    tags: List[str]
    capabilities: List[str]
    use_cases: List[str]
    priority: int = 0

class Installation(BaseModel):
    method: Literal["git", "npm", "pip", "docker", "remote"]
    repository: Optional[str] = None
    package_name: Optional[str] = None
    # ...

class Activation(BaseModel):
    activation_type: Literal["stdio", "http", "mcp", "sse", "websocket"]
    command: Optional[str] = None
    args: List[str] = []
    # ...

class PromptTemplate(BaseModel):
    name: str
    template: str
    variables: Dict[str, str] = {}
    format: Literal["jinja2", "f-string"] = "jinja2"

class SubAgent(BaseModel):
    metadata: SubAgentMetadata
    prompts: List[PromptTemplate]
    interface: InterfaceSpec
    installations: List[Installation]
    activations: List[Activation]
```

---

## API Specifications

### Base URL
- Development: `http://localhost:8000`
- Production: `https://registry.deepagents.ai`

### Authentication
- Phase 1: No authentication (public read)
- Phase 2: API Key for write operations
- Phase 3: OAuth 2.0 for enterprise

### Endpoints

#### 1. Search API

**`POST /search/`**

Search for subagents using natural language.

Request:
```json
{
  "query": "I need deep research with academic citations",
  "top_k": 5,
  "domain": "research",  // optional
  "tags": ["citations", "academic"]  // optional
}
```

Response:
```json
{
  "results": [
    {
      "name": "research-agent",
      "version": "1.0.0",
      "description": "Deep research agent...",
      "domain": "research",
      "tags": ["web-search", "citations"],
      "score": 0.92
    }
  ],
  "total": 1,
  "query_time_ms": 145
}
```

**`GET /search/by-capability`**

Search by specific capability.

Query params: `capability`, `top_k`

---

#### 2. SubAgents API

**`GET /subagents/`**

List all subagents with pagination.

Query params:
- `domain` (optional)
- `skip` (default: 0)
- `limit` (default: 100)

**`GET /subagents/{name}`**

Get detailed information about a specific subagent.

Response:
```json
{
  "metadata": { ... },
  "prompts": [ ... ],
  "interface": { ... },
  "installations": [ ... ],
  "activations": [ ... ],
  "examples": [ ... ]
}
```

**`POST /subagents/`** (Admin only)

Create a new subagent.

**`PUT /subagents/{name}`** (Admin only)

Update existing subagent.

**`DELETE /subagents/{name}`** (Admin only)

Delete a subagent.

---

#### 3. Prompts API

**`GET /prompts/{subagent_name}`**

List all prompts for a subagent.

**`GET /prompts/{subagent_name}/{prompt_name}`**

Get a specific prompt template.

**`POST /prompts/{subagent_name}/{prompt_name}/render`**

Render a prompt with variables.

Request:
```json
{
  "variables": {
    "task": "Research AI safety",
    "max_sources": "10"
  }
}
```

Response:
```json
{
  "rendered": "You are a research agent. Your task: Research AI safety. Use up to 10 sources."
}
```

---

#### 4. Admin API

**`POST /admin/import`** (Admin only)

Import subagent from YAML file.

**`POST /admin/reindex`** (Admin only)

Rebuild vector index.

**`GET /admin/stats`**

Get registry statistics.

---

## Implementation Phases

### Phase 1: Core Infrastructure (4 weeks)

**Goal**: Build foundational components

**Deliverables**:
- [ ] SQLite schema and migrations
- [ ] Pydantic models
- [ ] Database layer (CRUD operations)
- [ ] Basic FastAPI app structure
- [ ] Health check endpoint

**Success Criteria**:
- Database can store and retrieve subagents
- API returns 200 OK on health check

---

### Phase 2: Search Engine (3 weeks)

**Goal**: Implement RAG-based search

**Deliverables**:
- [ ] Qdrant integration
- [ ] Embedding generation (OpenAI)
- [ ] SubAgentIndexer implementation
- [ ] SubAgentRetriever implementation
- [ ] Search API endpoints (`/search/*`)

**Success Criteria**:
- Search returns relevant results
- Search latency < 200ms (p95)

---

### Phase 3: Prompt Management (2 weeks)

**Goal**: Build prompt template system

**Deliverables**:
- [ ] PromptManager implementation
- [ ] Jinja2 renderer
- [ ] Prompts API endpoints (`/prompts/*`)
- [ ] Prompt validation

**Success Criteria**:
- Prompts can be stored and retrieved
- Templates render correctly with variables

---

### Phase 4: Installation & Activation Metadata (2 weeks)

**Goal**: Complete metadata management

**Deliverables**:
- [ ] Installation info storage and retrieval
- [ ] Activation info storage and retrieval
- [ ] SubAgents API endpoints (`/subagents/*`)
- [ ] Interface spec management

**Success Criteria**:
- All metadata fields can be stored and queried
- API returns complete subagent details

---

### Phase 5: DeepAgents Integration (3 weeks)

**Goal**: Build client and integrate with DeepAgents

**Deliverables**:
- [ ] `RegistryClient` implementation (httpx)
- [ ] `RegistrySubAgentMiddleware` implementation
- [ ] CLI commands (`deepagents registry`, `deepagents subagent`)
- [ ] Auto-install functionality
- [ ] Integration tests

**Success Criteria**:
- DeepAgents can search and install subagents from registry
- Prompts are automatically fetched from registry

---

### Phase 6: Admin Tools & Data Seeding (2 weeks)

**Goal**: Build admin tools and populate registry

**Deliverables**:
- [ ] `registry-cli` implementation
- [ ] YAML import functionality
- [ ] Sample subagent YAML files (research, coding, critique)
- [ ] Data validation
- [ ] Admin API endpoints

**Success Criteria**:
- Registry has at least 10 sample subagents
- YAML import works end-to-end

---

### Phase 7: Testing & Documentation (2 weeks)

**Goal**: Comprehensive testing and docs

**Deliverables**:
- [ ] Unit tests (80%+ coverage)
- [ ] Integration tests
- [ ] API documentation (OpenAPI)
- [ ] User guide
- [ ] Developer guide (How to add subagents)

**Success Criteria**:
- All tests pass
- Documentation is complete and published

---

### Phase 8: Production Deployment (1 week)

**Goal**: Deploy to production

**Deliverables**:
- [ ] Dockerization
- [ ] CI/CD pipeline
- [ ] Production deployment (Cloud Run / ECS)
- [ ] Monitoring and logging

**Success Criteria**:
- Registry is accessible at production URL
- Uptime > 99.9%

---

## Success Metrics

### Key Performance Indicators (KPIs)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Search Accuracy** | 90%+ relevance | User feedback / manual evaluation |
| **API Uptime** | 99.9% | Monitoring tools |
| **Search Latency** | < 200ms (p95) | API metrics |
| **Registry Size** | 100+ subagents | Database count |
| **DeepAgents Adoption** | 50%+ use registry | Telemetry |
| **Community Contributions** | 10+ external subagents | GitHub PRs |

### Success Criteria

**Milestone 1 (MVP - Week 8)**:
- ✅ Registry API is live
- ✅ 10+ sample subagents indexed
- ✅ Search works with 80%+ accuracy
- ✅ DeepAgents integration functional

**Milestone 2 (Beta - Week 12)**:
- ✅ 50+ subagents in registry
- ✅ 100+ API requests/day
- ✅ 5+ active DeepAgents users

**Milestone 3 (GA - Week 16)**:
- ✅ 100+ subagents
- ✅ Public documentation complete
- ✅ Community contributions enabled

---

## Constraints & Considerations

### Technical Constraints

1. **Embedding Costs**
   - OpenAI embeddings: $0.0001 per 1K tokens
   - Mitigation: Cache embeddings, batch processing

2. **SQLite Limitations**
   - Single-writer bottleneck for high write loads
   - Mitigation: Consider PostgreSQL for production

3. **Vector DB Size**
   - Qdrant memory usage scales with corpus size
   - Mitigation: Use quantization, regular cleanup

### Security Considerations

1. **Code Execution Risk**
   - Subagents may execute arbitrary code during installation
   - Mitigation: Sandboxing, security warnings, community review

2. **API Abuse**
   - Public API may be abused for scraping
   - Mitigation: Rate limiting, API keys for heavy users

3. **Prompt Injection**
   - Malicious prompts in templates
   - Mitigation: Template sandboxing, review process

### Privacy Considerations

1. **Search Query Logging**
   - User search queries may contain sensitive info
   - Mitigation: Anonymize logs, opt-out option

2. **Subagent Metadata**
   - Metadata may reveal proprietary information
   - Mitigation: Private registries for enterprises

---

## Future Enhancements

### Phase 9+: Advanced Features

1. **Multi-Registry Support**
   - Support for public, private, and federated registries
   - Registry mirroring and synchronization

2. **Versioning & Rollback**
   - Semantic versioning for subagents
   - Rollback to previous versions

3. **Dependency Resolution**
   - Automatic dependency installation
   - Conflict detection and resolution

4. **Analytics Dashboard**
   - Usage statistics (downloads, search queries)
   - Popularity rankings
   - Performance metrics

5. **Community Features**
   - User ratings and reviews
   - Comments and discussions
   - Featured subagents

6. **GraphQL API**
   - Alternative to REST for complex queries
   - Batch operations

7. **WebAssembly Support**
   - Run subagents in browser
   - Sandboxed execution

8. **Integration with LangSmith**
   - Prompt versioning via LangSmith
   - A/B testing

---

## Appendix

### A. Example YAML File

```yaml
metadata:
  name: research-agent
  version: 1.0.0
  description: "Deep research agent with web search and citation management"
  author: "deepagents-community"
  license: MIT
  domain: research
  tags: [web-search, academic-research, citation]
  capabilities:
    - "Conduct deep web research using Tavily API"
    - "Search academic databases"
  use_cases:
    - "When user requests in-depth research"
  priority: 10

prompts:
  - name: system
    template: |
      You are a dedicated research agent.
      Your task: {{ task }}
      Maximum sources: {{ max_sources }}
    variables:
      task: "The research task description"
      max_sources: "Maximum number of sources to use"
    format: jinja2

interface:
  protocol: langchain
  tools:
    - name: web_search
      description: "Search the web using Tavily"
      parameters:
        query: string
        max_results: integer

installations:
  - method: git
    repository: https://github.com/deepagents-community/research-agent
    branch: main
    post_install_commands:
      - pip install -r requirements.txt

activations:
  - activation_type: stdio
    command: python
    args: [src/agent.py, --mode=subagent]
    working_dir: "{install_path}"
    env_vars:
      TAVILY_API_KEY:
        required: true
        description: "Tavily API key for web search"

examples:
  - input: "Research the environmental impact of renewable energy"
    output: "15-page report with 30+ citations"

dependencies:
  - dep_type: python
    name: tavily
    version: ">=1.1.0"
    required: true
```

### B. API Client Example

```python
from deepagents.registry import RegistryClient

client = RegistryClient("https://registry.deepagents.ai")

# Search
results = await client.search("research with citations", top_k=3)
print(results[0].metadata.name)  # "research-agent"

# Get details
subagent = await client.get_subagent("research-agent")
print(subagent.installations[0].method)  # "git"

# Get prompt
prompt = await client.get_prompt("research-agent", "system")
print(prompt.template)

# Render prompt
rendered = await client.render_prompt(
    "research-agent",
    "system",
    {"task": "AI safety", "max_sources": "10"}
)
print(rendered)
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-15 | DeepAgents Team | Initial PRD |

---

## Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Manager | TBD | | |
| Engineering Lead | TBD | | |
| Tech Lead | TBD | | |

---

**End of Document**