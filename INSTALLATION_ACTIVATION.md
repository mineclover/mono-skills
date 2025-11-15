# Installation과 Activation의 관계

## 핵심 개념

**Installation과 Activation은 독립적입니다:**

1. **설치 없이 실행** (Remote API)
   - Installation: `method: remote` (설치 불필요)
   - Activation: `type: sse` or `http` or `websocket`

2. **설치 후 다양한 실행 방법**
   - Installation: `pip install mytools`
   - Activation: `cli`, `http`, `grpc` 등 여러 방식 가능

3. **Tool별로 실행 방법이 다름**
   - SubAgent 레벨: 전체 패키지 실행 방법
   - Tool 레벨: 개별 도구 실행 방법 (다를 수 있음)

## 예시 시나리오

### 1. Remote API (설치 불필요)

```yaml
subagent:
  name: openai-toolkit
  version: 1.0.0

  # 설치 불필요
  installation:
    method: remote
    description: "Hosted API service"

  # SSE로 실행
  activation:
    type: sse
    url: https://api.openai.com/v1/stream
    auth:
      type: bearer
      token_env: OPENAI_API_KEY

tools:
  - name: gpt4_completion
    # 상속받음 (SSE로 실행)
```

### 2. CLI 서브커맨드

```yaml
subagent:
  name: deeptools-cli
  version: 2.0.0

  installation:
    method: pip
    package_name: deeptools

  # 메인 CLI 정보만
  activation:
    type: cli
    command: deeptools

tools:
  - name: search
    # CLI 서브커맨드
    activation:
      type: cli_subcommand
      command: deeptools
      subcommand: search
      args: []

  - name: analyze
    activation:
      type: cli_subcommand
      command: deeptools
      subcommand: analyze
      args: [--format, json]

  - name: translate
    activation:
      type: cli_subcommand
      command: deeptools
      subcommand: translate
```

### 3. Docker + HTTP 서버 + 개별 엔드포인트

```yaml
subagent:
  name: analysis-server
  version: 1.0.0

  installation:
    method: docker
    image: myorg/analysis-server:1.0

  # HTTP 서버로 실행
  activation:
    type: http
    port: 8080
    health_check: /health

tools:
  - name: sentiment_analysis
    # HTTP 엔드포인트
    activation:
      type: http_endpoint
      base_url: http://localhost:8080
      endpoint: /api/sentiment
      method: POST

  - name: entity_extraction
    activation:
      type: http_endpoint
      base_url: http://localhost:8080
      endpoint: /api/entities
      method: POST
```

### 4. 하이브리드 (여러 실행 방법 제공)

```yaml
subagent:
  name: versatile-toolkit

  # Python 패키지로 설치
  installation:
    method: pip
    package_name: versatile-toolkit

  # 기본 실행 방법
  activation:
    type: cli
    command: versatile-toolkit

tools:
  - name: batch_process
    # CLI로 실행
    activation:
      type: cli_subcommand
      command: versatile-toolkit
      subcommand: batch

  - name: realtime_process
    # HTTP 서버 모드로 실행 (다른 방법)
    activation:
      type: http_endpoint
      # 먼저 서버 시작: versatile-toolkit serve --port 8000
      base_url: http://localhost:8000
      endpoint: /process
      requires_server: true
      server_command: versatile-toolkit serve --port 8000
```

### 5. 여러 설치 방법 + 여러 실행 방법

```yaml
subagent:
  name: multi-platform-tools

  # 여러 설치 방법
  installations:
    - method: pip
      package_name: multi-platform-tools

    - method: npm
      package_name: "@org/multi-platform-tools"

    - method: docker
      image: org/multi-platform-tools:1.0

    - method: remote
      description: "Hosted service"

  # 설치 방법에 따라 다른 activation
  activations:
    - platform: pip
      type: cli
      command: mpt

    - platform: npm
      type: cli
      command: npx
      args: [mpt]

    - platform: docker
      type: http
      port: 8080

    - platform: remote
      type: sse
      url: https://api.mpt.io/stream

tools:
  - name: process_data
    # 플랫폼별로 다른 실행 방법
    activations:
      - platform: pip
        type: cli_subcommand
        command: mpt
        subcommand: process

      - platform: npm
        type: cli_subcommand
        command: npx
        args: [mpt, process]

      - platform: docker
        type: http_endpoint
        endpoint: /api/process

      - platform: remote
        type: sse_event
        event_type: process_data
```

## 데이터 모델 수정

### SubAgent

```python
class SubAgent(BaseModel):
    name: str
    version: str

    # 여러 설치 방법 (선택 가능)
    installations: List[Installation]

    # 설치 방법별 실행 방법
    activations: List[SubAgentActivation]

    # 또는 기본 실행 방법 (모든 설치에 공통)
    default_activation: Optional[Activation]
```

### Installation

```python
class Installation(BaseModel):
    method: Literal["pip", "npm", "docker", "remote", "binary", "git", ...]
    platform_id: str  # "pip-python", "npm-node", "remote-api"

    # 설치 상세
    package_name: Optional[str]
    # ... 기타 필드

    # 설치 불필요 표시
    requires_install: bool = True  # remote는 False
```

### Activation

```python
class Activation(BaseModel):
    """실행 방법"""

    type: Literal[
        "cli",              # 단순 CLI
        "cli_subcommand",   # CLI 서브커맨드
        "http_server",      # HTTP 서버 시작
        "http_endpoint",    # HTTP 엔드포인트 호출
        "grpc",
        "websocket",
        "sse",              # Server-Sent Events
        "stdio",            # stdin/stdout
        "library",          # 라이브러리 임포트
    ]

    # 연결된 설치 방법 (선택적)
    platform_id: Optional[str]  # 특정 설치 방법에서만 동작

    # CLI 관련
    command: Optional[str]
    subcommand: Optional[str]  # 서브커맨드
    args: List[str]

    # HTTP 관련
    base_url: Optional[str]
    endpoint: Optional[str]
    method: Optional[str]
    requires_server: bool = False
    server_command: Optional[str]  # 서버 시작 명령

    # SSE/WebSocket
    url: Optional[str]
    event_type: Optional[str]

    # 공통
    env_vars: Dict[str, EnvVar]
```

### Tool

```python
class Tool(BaseModel):
    name: str
    # ...

    # Tool별 실행 방법 (SubAgent과 다를 수 있음)
    activations: List[ToolActivation]

    # 또는 SubAgent 실행 방법 상속
    inherit_activation: bool = True
```

## 클라이언트 사용 예시

```python
# 1. 도구 검색
tool = registry.search_tools("데이터 처리")[0]

# 2. 설치 방법 선택
subagent = registry.get_subagent(tool.subagent_name)
install = subagent.choose_installation(platform="pip")  # 또는 "npm", "docker"

# 3. 설치 실행 (클라이언트가)
if install.requires_install:
    run(f"pip install {install.package_name}")

# 4. 실행 방법 가져오기
activation = tool.get_activation_for_platform(install.platform_id)

# 5. 실행 (클라이언트가)
if activation.type == "cli_subcommand":
    result = run([activation.command, activation.subcommand] + activation.args)
elif activation.type == "sse":
    # SSE 연결
    async for event in sse_client(activation.url):
        handle(event)
elif activation.type == "http_endpoint":
    if activation.requires_server:
        # 서버 먼저 시작
        start_server(activation.server_command)
    response = requests.post(f"{activation.base_url}{activation.endpoint}")
```

## 핵심 변경사항

1. **Installation과 Activation 분리**
   - 하나의 SubAgent가 여러 설치 방법
   - 각 설치 방법마다 다른 실행 방법

2. **Tool 레벨 Activation**
   - Tool마다 실행 방법이 다를 수 있음
   - CLI 서브커맨드, HTTP 엔드포인트 등

3. **플랫폼 ID로 연결**
   - Installation과 Activation을 platform_id로 매칭
   - 클라이언트가 선택한 설치 방법에 맞는 실행 방법 사용

4. **설치 불필요 케이스**
   - `requires_install: false` (Remote API)
   - 바로 SSE/HTTP로 연결

이게 맞나요?
