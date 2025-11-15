# SubAgent Registry & Search Engine

**Tool-centric** RAG 기반 레지스트리 및 검색 엔진 - AI 도구와 에이전트를 발견하고 관리하는 통합 플랫폼

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 개요 (Overview)

SubAgent Registry는 **도구(Tools) 중심**의 아키텍처로 설계된 AI 도구 레지스트리입니다:

### 핵심 기능

- 🔍 **의미 검색 (Semantic Search)**: RAG 기반 자연어 검색으로 원하는 도구 찾기
- 🛠️ **Tool-Centric 아키텍처**: 개별 도구(함수)가 검색의 주요 대상
- 🌐 **멀티 플랫폼 지원**: Python, Node.js, Rust, Go, Docker, Remote API 등
- 📝 **프롬프트 관리**: LangChain 호환 프롬프트 템플릿 제공
- 📦 **설치 정보 제공**: 플랫폼별 설치 및 실행 방법 안내
- 🔌 **구조화된 출력**: Pydantic + TypeScript + JSON Schema 스키마
- 🎯 **고급 검색**: 카테고리, 태그, 프로토콜 기반 필터링
- 🤝 **사용자 기여**: YAML/JSON을 통한 도구 추가 API

### 레지스트리의 역할

레지스트리는 **정보 카탈로그**로서 동작합니다:
- ✅ 도구의 설치 방법 제공
- ✅ 도구의 실행 방법 안내
- ✅ 프롬프트 템플릿 제공
- ✅ 파라미터 스키마 제공
- ❌ 도구를 직접 실행하지 않음 (사용자가 설치 후 실행)

## 빠른 시작 (Quick Start)

### 1. 의존성 설치

```bash
pip install fastapi uvicorn sqlalchemy pydantic qdrant-client \
    sentence-transformers python-multipart pyyaml httpx
```

### 2. 서버 실행

```bash
python -m registry_engine.api.app_v2

# 또는 uvicorn 사용
uvicorn registry_engine.api.app_v2:app --reload
```

서버가 http://localhost:8000 에서 실행됩니다.

### 3. 도구 검색

```bash
# 의미 검색
curl -X POST "http://localhost:8000/search/tools" \
  -H "Content-Type: application/json" \
  -d '{"query": "search the web", "top_k": 5}'

# 카테고리별 검색
curl "http://localhost:8000/search/tools/by-category?category=security"
```

### 4. 도구 정보 조회

```bash
# 도구 상세 정보
curl "http://localhost:8000/tools/web_search"

# 설치 방법
curl "http://localhost:8000/tools/web_search/install"
```

더 자세한 내용은 [QUICKSTART.md](QUICKSTART.md) 참조

## 문서 (Documentation)

| 문서 | 설명 |
|------|------|
| [QUICKSTART.md](QUICKSTART.md) | 5분 빠른 시작 가이드 |
| [USER_GUIDE.md](USER_GUIDE.md) | 상세 사용자 가이드 (검색, API, 예제) |
| [CONTRIBUTION_GUIDE.md](CONTRIBUTION_GUIDE.md) | 도구 기여 가이드 (YAML 구조, 검증) |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Tool-centric 아키텍처 설계 |
| [INSTALLATION_ACTIVATION.md](INSTALLATION_ACTIVATION.md) | 설치-실행 관계 설명 |
| [PRD.md](PRD.md) | 원본 제품 요구사항 문서 |

## 주요 기능

### 🔍 의미 검색 (Semantic Search)

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/search/tools",
        json={"query": "이미지 배경 제거", "top_k": 5}
    )
    tools = response.json()['results']
```

### 🎯 고급 검색 (Advanced Search)

```bash
curl -X POST "http://localhost:8000/search/advanced" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "process images",
    "categories": ["image-processing"],
    "tags": ["ai"],
    "protocols": ["langchain"],
    "sort_by": "relevance"
  }'
```

### 🤝 도구 기여 (Contribution)

```bash
# YAML 검증
curl -X POST "http://localhost:8000/contribute/yaml/validate" \
  -F "file=@my-toolkit.yaml"

# 도구 임포트 (자동 인덱싱)
curl -X POST "http://localhost:8000/contribute/yaml/import" \
  -F "file=@my-toolkit.yaml"
```

## 지원 플랫폼

| 플랫폼 | 설치 방법 | 실행 방법 |
|--------|----------|----------|
| Python | `pip` | CLI, Library |
| Node.js | `npm`, `yarn` | CLI, Library |
| Rust | `cargo`, Binary | CLI |
| Go | `go install`, Binary | CLI |
| Docker | `docker pull` | HTTP Server |
| Remote | 설치 불필요 | HTTP, SSE, WebSocket |

## 예제 (Examples)

`examples_v2/` 디렉토리에 다양한 플랫폼 예제가 있습니다:

- **tavily-search-toolkit.yaml** - Python/npm/docker/remote (멀티 플랫폼)
- **npm-image-processor.yaml** - Node.js 이미지 처리
- **docker-ml-inference.yaml** - Docker ML 추론 서비스
- **cargo-crypto-tools.yaml** - Rust 암호화 툴킷
- **remote-weather-api.yaml** - Remote API (설치 불필요)
- **go-database-tools.yaml** - Go 데이터베이스 마이그레이션

## 프로젝트 구조

```
mono-skills/
├── registry_engine/
│   ├── api/
│   │   ├── app_v2.py              # FastAPI 애플리케이션
│   │   └── routes/
│   │       ├── tools.py           # 도구 API
│   │       ├── search_v2.py       # 검색 API
│   │       ├── search_advanced.py # 고급 검색 API
│   │       └── contributions.py   # 기여 API
│   ├── database/
│   │   ├── models_v2.py           # SQLAlchemy ORM
│   │   ├── tool_db.py             # Tool CRUD
│   │   └── qdrant_v2.py           # Vector DB
│   ├── search/
│   │   ├── tool_indexer.py        # 인덱싱
│   │   └── tool_retriever.py      # RAG 검색
│   └── models/
│       └── tool_centric.py        # Pydantic 모델
├── examples_v2/                   # YAML 예제
├── QUICKSTART.md                  # 빠른 시작
├── USER_GUIDE.md                  # 사용자 가이드
└── CONTRIBUTION_GUIDE.md          # 기여 가이드
```

## API 엔드포인트

### 검색

- `POST /search/tools` - 의미 검색
- `GET /search/tools/by-category` - 카테고리별 검색
- `POST /search/advanced` - 다중 필터 검색
- `GET /search/facets` - 사용 가능한 필터
- `GET /search/suggest` - 자동완성
- `GET /search/similar/{tool_name}` - 유사 도구
- `GET /search/statistics` - 통계

### 도구 정보

- `GET /tools/` - 도구 목록
- `GET /tools/{name}` - 도구 상세 정보
- `GET /tools/{name}/prompts` - 프롬프트 템플릿
- `GET /tools/{name}/schema` - Structured Output 스키마
- `GET /tools/{name}/install` - 설치 및 실행 정보

### 기여

- `POST /contribute/yaml/validate` - YAML 검증
- `POST /contribute/yaml/import` - YAML 임포트
- `POST /contribute/tools/submit` - 도구 제출
- `POST /contribute/subagents/submit` - SubAgent 제출

API 문서: http://localhost:8000/docs

## 개발 (Development)

### 테스트

```bash
# YAML 검증
python validate_yaml_examples.py

# API 통합 테스트
python test_contribution_api.py
```

### 새 도구 추가

1. YAML 파일 작성 ([CONTRIBUTION_GUIDE.md](CONTRIBUTION_GUIDE.md) 참조)
2. 로컬 검증: `python validate_yaml_examples.py`
3. API로 임포트: `POST /contribute/yaml/import`

## 아키텍처 특징

### Tool-Centric Design

- **Tools**: 검색의 주요 대상 (개별 함수)
- **SubAgents**: 도구를 제공하는 패키지 (메타데이터)
- **Installation**: 플랫폼별 설치 방법
- **Activation**: 플랫폼별 실행 방법

### Installation ≠ Activation

설치와 실행은 독립적입니다:
- Remote API는 설치 불필요 (`requires_install: false`)
- 하나의 SubAgent가 여러 플랫폼 지원 가능
- `platform_id`로 설치-실행 방법 연결

자세한 내용은 [ARCHITECTURE.md](ARCHITECTURE.md) 참조

## 기여하기 (Contributing)

새로운 도구를 추가하려면 [CONTRIBUTION_GUIDE.md](CONTRIBUTION_GUIDE.md)를 참조하세요.

## 라이선스 (License)

MIT
