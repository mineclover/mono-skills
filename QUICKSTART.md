# Quick Start Guide

이 가이드는 5분 안에 SubAgent Registry를 시작하는 방법을 안내합니다.

## 1단계: 서버 실행

```bash
# 저장소 클론
git clone <repository-url>
cd mono-skills

# 의존성 설치
pip install fastapi uvicorn sqlalchemy pydantic qdrant-client sentence-transformers python-multipart pyyaml httpx

# 서버 실행
python -m registry_engine.api.app_v2
```

서버가 http://localhost:8000 에서 실행됩니다.

## 2단계: 예제 도구 임포트

```bash
# YAML 예제 검증
python validate_yaml_examples.py

# 브라우저에서 API 문서 열기
open http://localhost:8000/docs

# 또는 curl로 예제 임포트
curl -X POST "http://localhost:8000/contribute/yaml/import" \
  -F "file=@examples_v2/tavily-search-toolkit.yaml"
```

## 3단계: 도구 검색

### 웹 인터페이스

http://localhost:8000/docs 에서 `POST /search/tools` 엔드포인트 사용

### cURL

```bash
curl -X POST "http://localhost:8000/search/tools" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "search the web",
    "top_k": 5
  }'
```

### Python

```python
import httpx
import asyncio

async def search():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/search/tools",
            json={"query": "암호화", "top_k": 3}
        )
        print(response.json())

asyncio.run(search())
```

## 4단계: 도구 정보 조회

```bash
# 도구 상세 정보
curl "http://localhost:8000/tools/web_search"

# 설치 방법
curl "http://localhost:8000/tools/web_search/install"

# 프롬프트 템플릿
curl "http://localhost:8000/tools/web_search/prompts"
```

## 다음 단계

### 더 많은 검색 기능

```bash
# 카테고리별 검색
curl "http://localhost:8000/search/tools/by-category?category=security"

# 고급 검색 (필터)
curl -X POST "http://localhost:8000/search/advanced" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "image processing",
    "categories": ["image-processing"],
    "tags": ["ai"],
    "limit": 10
  }'

# 자동완성
curl "http://localhost:8000/search/suggest?q=enc"

# 유사 도구
curl "http://localhost:8000/search/similar/encrypt_data"

# 통계
curl "http://localhost:8000/search/statistics"
```

### 모든 예제 임포트

```bash
# 모든 YAML 예제 임포트
for file in examples_v2/*.yaml; do
  echo "Importing $file..."
  curl -X POST "http://localhost:8000/contribute/yaml/import" \
    -F "file=@$file"
done
```

### 사용 가능한 도구 확인

```bash
# 모든 도구 목록
curl "http://localhost:8000/tools/?limit=100"

# 모든 SubAgent 목록
curl "http://localhost:8000/subagents/?limit=100"

# 필터 옵션 확인
curl "http://localhost:8000/search/facets"
```

## 실전 예제

### Python으로 도구 검색 및 사용

```python
import httpx
import asyncio
from typing import List, Dict

class RegistryClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    async def search_tools(self, query: str, top_k: int = 5) -> List[Dict]:
        """도구 검색"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/search/tools",
                json={"query": query, "top_k": top_k}
            )
            return response.json()['results']

    async def get_tool_info(self, tool_name: str) -> Dict:
        """도구 상세 정보"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/tools/{tool_name}"
            )
            return response.json()

    async def get_install_info(self, tool_name: str) -> Dict:
        """설치 정보"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/tools/{tool_name}/install"
            )
            return response.json()

    async def get_prompts(self, tool_name: str) -> List[Dict]:
        """프롬프트 템플릿"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/tools/{tool_name}/prompts"
            )
            return response.json()['prompts']

# 사용 예제
async def main():
    client = RegistryClient()

    # 1. 도구 검색
    tools = await client.search_tools("웹 검색")
    print(f"검색 결과: {len(tools)}개\n")

    if tools:
        tool = tools[0]
        print(f"도구: {tool['display_name']}")
        print(f"설명: {tool['description']}\n")

        # 2. 상세 정보
        info = await client.get_tool_info(tool['name'])
        print(f"카테고리: {info['category']}")
        print(f"태그: {', '.join(info['tags'])}\n")

        # 3. 설치 방법
        install = await client.get_install_info(tool['name'])
        print("설치 방법:")
        for inst in install['installations']:
            print(f"  - {inst['method']}: {inst.get('package_name', 'N/A')}")
        print()

        # 4. 프롬프트
        prompts = await client.get_prompts(tool['name'])
        if prompts:
            print(f"프롬프트 템플릿: {prompts[0]['name']}")
            print(f"  {prompts[0]['human_message_template'][:100]}...")

asyncio.run(main())
```

### CLI 스크립트

```bash
#!/bin/bash
# registry-search.sh - 간단한 검색 스크립트

REGISTRY_URL="http://localhost:8000"

case "$1" in
  search)
    curl -s -X POST "$REGISTRY_URL/search/tools" \
      -H "Content-Type: application/json" \
      -d "{\"query\": \"$2\", \"top_k\": 5}" | \
      python -m json.tool
    ;;
  info)
    curl -s "$REGISTRY_URL/tools/$2" | python -m json.tool
    ;;
  install)
    curl -s "$REGISTRY_URL/tools/$2/install" | python -m json.tool
    ;;
  stats)
    curl -s "$REGISTRY_URL/search/statistics" | python -m json.tool
    ;;
  *)
    echo "Usage: $0 {search|info|install|stats} [args]"
    echo ""
    echo "Examples:"
    echo "  $0 search 'web search'"
    echo "  $0 info web_search"
    echo "  $0 install web_search"
    echo "  $0 stats"
    exit 1
    ;;
esac
```

**사용법:**
```bash
chmod +x registry-search.sh

./registry-search.sh search "암호화"
./registry-search.sh info encrypt_data
./registry-search.sh install encrypt_data
./registry-search.sh stats
```

## 문제 해결

### 서버가 시작되지 않음

```bash
# 포트 사용 중 확인
lsof -i :8000

# 다른 포트로 실행
uvicorn registry_engine.api.app_v2:app --port 8001
```

### 검색 결과가 없음

```bash
# 데이터베이스에 도구가 있는지 확인
curl "http://localhost:8000/tools/"

# 예제 임포트
curl -X POST "http://localhost:8000/contribute/yaml/import" \
  -F "file=@examples_v2/tavily-search-toolkit.yaml"
```

### Qdrant 연결 오류

Qdrant는 자동으로 메모리 모드로 실행됩니다. 별도 설정 불필요.

## 다음 문서

- **상세 사용 가이드**: [USER_GUIDE.md](USER_GUIDE.md)
- **도구 기여**: [CONTRIBUTION_GUIDE.md](CONTRIBUTION_GUIDE.md)
- **아키텍처**: [ARCHITECTURE.md](ARCHITECTURE.md)
