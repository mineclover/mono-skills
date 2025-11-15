# Agno Integration Guide

SubAgent Registry와 Agno (또는 다른 실행 플랫폼)를 통합하여 **도구 발견**과 **에이전트 실행**을 연결하는 방법을 설명합니다.

## 개요

### 아키텍처 관계

```
┌─────────────────────────────────────────┐
│   SubAgent Registry                     │
│   (도구 발견 및 메타데이터)               │
│                                          │
│   • 도구 검색 (RAG)                      │
│   • 설치 방법 정보                       │
│   • 프롬프트 템플릿                      │
│   • 실행 중인 인스턴스 조회              │
└──────────────┬──────────────────────────┘
               │
               │ 배포 등록 & 상태 업데이트
               │
┌──────────────▼──────────────────────────┐
│   Agno (또는 다른 실행 플랫폼)            │
│                                          │
│   • 에이전트 실행                        │
│   • 메모리 관리                          │
│   • LLM 통합                             │
│   • 워크플로우 오케스트레이션             │
└─────────────────────────────────────────┘
```

### 역할 분담

| 시스템 | 역할 | 제공하는 것 |
|--------|------|------------|
| **SubAgent Registry** | 정보 카탈로그 | • 도구 검색 및 발견<br>• 설치/실행 방법 정보<br>• 프롬프트 템플릿<br>• 실행 중인 인스턴스 위치 |
| **Agno** | 실행 플랫폼 | • 에이전트 직접 실행<br>• 세션/메모리 관리<br>• LLM 호출<br>• 워크플로우 관리 |

## 통합 시나리오

### 시나리오 1: Agno에서 도구 발견

사용자가 Agno에서 에이전트를 만들 때 필요한 도구를 Registry에서 검색:

```python
import httpx

# 1. Registry에서 도구 검색
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://registry.example.com/search/tools",
        json={"query": "웹 검색", "top_k": 5}
    )
    tools = response.json()['results']

# 2. 도구 정보 확인
tool = tools[0]  # "web_search"

# 3. 설치 방법 조회
install_info = await client.get(
    f"http://registry.example.com/tools/{tool['name']}/install"
)

# 4. Agno에서 도구 사용
from agno import Agent, Toolkit

agent = Agent(
    name="Web Search Agent",
    tools=[
        Toolkit.from_registry(
            tool_name="web_search",
            registry_url="http://registry.example.com"
        )
    ]
)
```

### 시나리오 2: Agno 배포를 Registry에 등록

Agno에서 에이전트를 배포한 후 Registry에 등록하여 다른 사용자가 발견할 수 있게:

```python
# 1. Agno에서 에이전트 배포
from agno import Agent

agent = Agent(
    name="production-web-search",
    tools=["web_search"]
)

deployment = agent.deploy(environment="production")
# → https://api.agno.example.com/agents/production-web-search

# 2. Registry에 배포 정보 등록
import httpx

async with httpx.AsyncClient() as client:
    await client.post(
        "http://registry.example.com/deployments/",
        json={
            "tool_name": "web_search",
            "subagent_name": "tavily-search-toolkit",
            "deployment_name": "production-web-search",
            "environment": "production",
            "endpoint": {
                "url": "https://api.agno.example.com/agents/production-web-search",
                "method": "POST",
                "auth_type": "bearer"
            },
            "metadata": {
                "platform": "agno",
                "platform_version": "1.0.0"
            }
        }
    )
```

### 시나리오 3: 실행 중인 에이전트 발견 및 사용

사용자가 로컬 설치 대신 이미 실행 중인 에이전트를 찾아서 사용:

```python
# 1. 실행 중인 도구 검색
response = await client.get(
    "http://registry.example.com/tools/running",
    params={"environment": "production"}
)

running_tools = response.json()['results']

# 2. 특정 도구의 배포 정보 조회
response = await client.get(
    "http://registry.example.com/tools/web_search/deployments"
)

deployments = response.json()['deployments']

# 3. 실행 중인 인스턴스 직접 호출
deployment = deployments[0]
endpoint = deployment['endpoint']['url']

# Agno 에이전트 호출
response = await client.post(
    endpoint,
    json={"query": "Find AI news"},
    headers={"Authorization": f"Bearer {api_key}"}
)
```

## API 엔드포인트

### 배포 등록

```bash
POST /deployments/
```

**Request:**
```json
{
  "tool_name": "web_search",
  "subagent_name": "tavily-search-toolkit",
  "deployment_name": "production-web-search",
  "environment": "production",
  "region": "us-east-1",
  "endpoint": {
    "url": "https://api.agno.example.com/agents/web-search",
    "method": "POST",
    "auth_type": "bearer",
    "headers": {
      "Content-Type": "application/json"
    },
    "health_check_url": "https://api.agno.example.com/agents/web-search/health",
    "timeout_ms": 30000
  },
  "metadata": {
    "platform": "agno",
    "platform_version": "1.0.0",
    "deployed_by": "devops-team",
    "deployment_config": {
      "agent_id": "agno_agent_123",
      "memory_enabled": true
    },
    "tags": ["production", "web-search"]
  }
}
```

### 상태 업데이트

```bash
POST /deployments/{deployment_id}/health
```

**Request:**
```json
{
  "status": "running",
  "uptime_seconds": 86400,
  "request_count": 1523,
  "avg_latency_ms": 245.3
}
```

### 실행 중인 도구 조회

```bash
GET /tools/running?environment=production
```

**Response:**
```json
{
  "results": [
    {
      "name": "web_search",
      "display_name": "Web Search",
      "category": "search",
      "total_deployments": 3,
      "running_deployments": 3,
      "production_deployments": 2,
      "deployments": [
        {
          "deployment_id": "deploy_abc123",
          "deployment_name": "production-web-search",
          "environment": "production",
          "endpoint": {
            "url": "https://api.agno.example.com/agents/web-search",
            "method": "POST"
          },
          "status": {
            "status": "running",
            "uptime_seconds": 86400
          },
          "metadata": {
            "platform": "agno"
          }
        }
      ]
    }
  ],
  "total": 1
}
```

### 플랫폼별 조회

```bash
GET /tools/by-platform/agno?environment=production
```

Agno에 배포된 모든 도구 조회

## 구현 예제

### 완전한 통합 예제

`examples_v2/agno_integration_example.py` 참조:

```bash
# 배포 + 모니터링 모드
python examples_v2/agno_integration_example.py

# 발견 모드
python examples_v2/agno_integration_example.py discover
```

### 자동 등록 스크립트

```python
"""Agno 배포 시 자동으로 Registry에 등록"""

from agno import Agent
import httpx

REGISTRY_URL = "http://registry.example.com"

async def deploy_and_register(agent_config):
    # 1. Agno 배포
    agent = Agent(**agent_config)
    agno_deployment = agent.deploy(environment="production")

    # 2. Registry 자동 등록
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{REGISTRY_URL}/deployments/",
            json={
                "tool_name": agent_config["primary_tool"],
                "subagent_name": agent_config["subagent"],
                "deployment_name": f"{agent_config['name']}-prod",
                "environment": "production",
                "endpoint": {
                    "url": agno_deployment.url,
                    "method": "POST",
                    "auth_type": "bearer"
                },
                "metadata": {
                    "platform": "agno",
                    "agent_id": agno_deployment.agent_id
                }
            }
        )

        if response.status_code == 201:
            deployment_id = response.json()["deployment_id"]
            print(f"✓ Registered: {deployment_id}")

            # 3. 상태 모니터링 시작
            await start_health_monitoring(deployment_id, agno_deployment)

        return deployment_id
```

### Health 모니터링

```python
"""주기적으로 상태 업데이트"""

import asyncio

async def start_health_monitoring(deployment_id: str, agno_deployment):
    while True:
        try:
            # Agno에서 메트릭 수집
            metrics = await agno_deployment.get_metrics()

            # Registry 업데이트
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{REGISTRY_URL}/deployments/{deployment_id}/health",
                    json={
                        "status": "running",
                        "uptime_seconds": metrics.uptime,
                        "request_count": metrics.requests,
                        "avg_latency_ms": metrics.latency
                    }
                )

            await asyncio.sleep(60)  # 60초마다 업데이트

        except Exception as e:
            print(f"Health update failed: {e}")
            await asyncio.sleep(60)
```

## 사용 사례

### 1. 엔터프라이즈 배포

**문제**: 여러 팀이 각자 에이전트를 배포하는데 어떤 에이전트가 어디에 있는지 모름

**해결**:
1. 각 팀이 Agno에서 에이전트 배포
2. 배포 정보를 중앙 Registry에 등록
3. 다른 팀이 Registry에서 검색하여 재사용

```python
# DevOps 팀: 배포
await deploy_and_register({
    "name": "data-processor",
    "primary_tool": "process_data",
    "subagent": "data-toolkit"
})

# Data Science 팀: 발견 및 사용
tools = await search_registry("data processing")
endpoint = tools[0]['deployments'][0]['endpoint']['url']

# 직접 사용
result = await call_agent(endpoint, {"data": my_data})
```

### 2. 개발 → 프로덕션 워크플로우

```python
# 개발 환경에서 테스트
dev_deployment = await deploy_and_register({
    "name": "web-search-dev",
    "environment": "development",
    ...
})

# 테스트 통과 후 프로덕션 배포
prod_deployment = await deploy_and_register({
    "name": "web-search-prod",
    "environment": "production",
    ...
})

# Registry에서 환경별 조회 가능
dev_agents = await get_deployments(environment="development")
prod_agents = await get_deployments(environment="production")
```

### 3. 멀티 리전 배포

```python
# US 리전
us_deployment = await deploy_and_register({
    "name": "web-search",
    "region": "us-east-1",
    ...
})

# EU 리전
eu_deployment = await deploy_and_register({
    "name": "web-search",
    "region": "eu-west-1",
    ...
})

# 사용자는 가까운 리전 자동 선택
my_region = get_user_region()
deployments = await get_deployments(tool="web_search", region=my_region)
```

## 베스트 프랙티스

### 1. 배포 시 자동 등록

Agno 배포 스크립트에 Registry 등록 자동화:

```python
# deploy.py
def deploy_agent(config):
    # Agno 배포
    agno_deployment = agno.deploy(config)

    # Registry 자동 등록
    register_deployment(agno_deployment)

    return agno_deployment
```

### 2. Health Check 구성

```python
# 60초마다 상태 업데이트
await start_health_monitoring(
    deployment_id=deployment_id,
    interval_seconds=60
)
```

### 3. Graceful Shutdown

```python
# 종료 시 Registry에서 제거
import signal

async def cleanup():
    await client.delete(f"{REGISTRY_URL}/deployments/{deployment_id}")

signal.signal(signal.SIGTERM, cleanup)
```

### 4. 환경 분리

- Development: `environment=development`
- Staging: `environment=staging`
- Production: `environment=production`

각 환경별로 별도 등록하여 격리

## 보안 고려사항

### 1. API 키 관리

```python
# ❌ 하드코딩 금지
endpoint = {
    "url": "https://...",
    "headers": {"Authorization": "Bearer secret_key"}  # 위험!
}

# ✅ 환경 변수 사용
import os

endpoint = {
    "url": "https://...",
    "auth_type": "bearer"
    # 실제 키는 클라이언트가 주입
}
```

### 2. 접근 제어

Registry에 배포 정보 등록 시 인증 필요:

```python
headers = {"Authorization": f"Bearer {registry_api_key}"}

await client.post(
    f"{REGISTRY_URL}/deployments/",
    json=deployment_data,
    headers=headers  # 인증
)
```

### 3. 프로덕션 배포 제한

프로덕션 환경은 승인된 팀만 등록 가능하도록 RBAC 설정

## 다음 단계

1. **Registry 설정**: [QUICKSTART.md](QUICKSTART.md)
2. **도구 검색**: [USER_GUIDE.md](USER_GUIDE.md)
3. **Agno 문서**: https://docs.agno.com
4. **예제 실행**: `python examples_v2/agno_integration_example.py`
