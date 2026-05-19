# TeamTeam 백엔드 로깅 가이드

## 개요

TeamTeam 백엔드는 `app/core/logging.py`에 구현된 **구조화 JSON 로깅(Structured JSON Logging)** 미들웨어를 사용합니다.  
모든 HTTP 요청/응답을 자동으로 기록하며, 각 로그는 검색·분석이 쉬운 JSON 한 줄 형태로 출력됩니다.

---

## 구현 위치

| 파일 | 역할 |
|------|------|
| `app/core/logging.py` | 로거 정의, JSON 포매터, 미들웨어 구현 |
| `app/main.py` | 미들웨어 등록 (`app.add_middleware(RequestLoggingMiddleware)`) |

---

## 로그 형식

모든 로그는 **JSON 한 줄(one-line JSON)** 형태로 `stdout`에 출력됩니다.

```json
{
  "timestamp": "2026-05-19 23:08:22,946",
  "level": "INFO",
  "message": "POST /api/auth/signup → 201",
  "logger": "teamteam",
  "request_id": "e2134bb1",
  "method": "POST",
  "path": "/api/auth/signup",
  "status_code": 201,
  "latency_ms": 453.58,
  "client_ip": "127.0.0.1"
}
```

### 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| `timestamp` | string | 요청이 완료된 시각 |
| `level` | string | 로그 레벨 (`INFO` / `WARNING` / `ERROR`) |
| `message` | string | `{METHOD} {path} → {status_code}` 형태의 요약 |
| `logger` | string | 항상 `"teamteam"` 고정 |
| `request_id` | string | 요청마다 생성되는 8자리 고유 ID (트레이싱용) |
| `method` | string | HTTP 메서드 (`GET`, `POST`, `PATCH`, `DELETE`) |
| `path` | string | 요청 URL 경로 |
| `status_code` | int | HTTP 응답 상태 코드 |
| `latency_ms` | float | 서버 처리 시간 (밀리초) |
| `client_ip` | string | 클라이언트 IP 주소 |

---

## 로그 레벨 규칙

응답 상태 코드에 따라 자동으로 로그 레벨이 결정됩니다.

| 상태 코드 범위 | 로그 레벨 | 의미 |
|:---:|:---:|------|
| `2xx`, `3xx` | `INFO` | 정상 처리 |
| `4xx` | `WARNING` | 클라이언트 오류 (잘못된 요청, 권한 없음 등) |
| `5xx` | `ERROR` | 서버 내부 오류 |

---

## Request ID 트레이싱

`RequestLoggingMiddleware`는 요청마다 8자리 UUID를 생성하여:
1. **로그 JSON에 `request_id` 필드**로 기록
2. **응답 헤더 `X-Request-ID`**에 포함하여 클라이언트에 반환

```
HTTP/1.1 201 Created
X-Request-ID: e2134bb1
```

이를 활용하면 특정 요청과 관련된 모든 로그를 `request_id`로 필터링할 수 있습니다.

---

## 라우터 내 수동 로깅

미들웨어의 자동 로깅 외에, AI 관련 기능처럼 상세한 추적이 필요한 경우 아래와 같이 수동으로 로그를 남깁니다.

```python
import logging
logger = logging.getLogger("teamteam")

# AI API 응답 지연 시간 기록
logger.info(f"AI schedule API latency: {latency:.2f}s")

# AI API 에러 기록
logger.error(f"AI schedule API failed after {latency:.2f}s: {e}")
```

> `logging.getLogger("teamteam")`을 사용하면 동일한 JSON 포매터가 적용됩니다.

---

## Prometheus 메트릭 (별도)

HTTP 로깅과 별개로, `/metrics` 엔드포인트에서 Prometheus 포맷의 메트릭을 확인할 수 있습니다.

```
GET http://<host>:8000/metrics
```

`prometheus-fastapi-instrumentator` 라이브러리가 자동으로 아래 메트릭을 수집합니다:
- 요청 수 (`http_requests_total`)
- 응답 시간 분포 (`http_request_duration_seconds`)
- 진행 중인 요청 수 (`http_requests_inprogress`)

---

## 로그 확인 방법

### Docker 환경

```bash
# 실시간 로그 스트리밍
docker compose logs -f backend

# 최근 100줄만 확인
docker compose logs --tail=100 backend
```

### 로컬 개발 환경

```bash
uvicorn app.main:app --reload
# stdout에 JSON 로그가 출력됩니다.
```

### request_id로 특정 요청 추적 (예시)

```bash
# Docker 로그에서 특정 request_id 필터링
docker compose logs backend | grep "e2134bb1"
```
