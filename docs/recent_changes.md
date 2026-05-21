# 최근 변경 이력 (Recent Changes)

> 이 문서는 TeamTeam Backend의 최근 머지(merge)된 주요 변경사항을 정리한 문서입니다.

---

## [feat] Gemini API 모델 버전 수정 — `31004f5`

- **날짜**: 2026-05-21
- **작성자**: PYO

### 개요
AI 기능에서 사용하는 Gemini 모델명이 실제 존재하지 않는 버전(`gemini-2.5-flash`)으로 잘못 설정되어 있어 API 호출 시 에러가 발생하던 문제를 수정했습니다.

### 변경 내용

| 파일 | 변경 사항 |
|------|----------|
| `app/routers/ai_schedule.py` | `gemini-2.5-flash` → `gemini-2.0-flash` |
| `app/routers/chat.py` | `gemini-2.5-flash` → `gemini-2.0-flash` |
| `README.md` | 기술스택 명세 동기화 |

### 영향 범위
- `POST /api/teams/{team_id}/ai-sessions` — AI 일정 자동 추천
- `POST /api/chat-rooms/{room_id}/ai-prompt` — 채팅 내용 AI 요약 및 프롬프트 생성

---

## [feat] Prometheus / Grafana 모니터링 스택 + 비즈니스 메트릭 — `2e3338c` (merge commit)

- **날짜**: 2026-05-21
- **작성자**: xihxxn

### 개요
Prometheus + Grafana 기반 모니터링 스택을 추가하고, 비즈니스 핵심 엔드포인트에 커스텀 메트릭 계측 및 구조화 로깅을 적용합니다.  
이 커밋은 아래 두 커밋(`24dfa3c`, `7e479e8`)을 통합한 merge commit입니다.

---

### 1단계 — 인프라 구성 (`24dfa3c`)

Docker Compose에 Prometheus 및 Grafana 서비스를 추가하고 모니터링 설정 파일을 구성했습니다.

#### 새로운 파일

| 파일 | 설명 |
|------|------|
| `monitoring/prometheus.yml` | Prometheus 스크래핑 설정 (FastAPI `/metrics` 엔드포인트 대상) |
| `monitoring/alert.rules.yml` | 알림 규칙 정의 (레이턴시, 에러율, 이탈 등) |
| `monitoring/grafana/provisioning/dashboards/teamteam.json` | TeamTeam 전용 Grafana 대시보드 |
| `monitoring/grafana/provisioning/dashboards/dashboard.yml` | Grafana 대시보드 자동 프로비저닝 설정 |
| `monitoring/grafana/provisioning/datasources/prometheus.yml` | Grafana → Prometheus 데이터소스 연결 설정 |

#### 수정된 파일
- **`docker-compose.yml`** — `prometheus` (포트 9090), `grafana` (포트 3000) 서비스 추가

---

### 2단계 — 애플리케이션 코드 계측 (`7e479e8`)

각 라우터에 Prometheus 커스텀 메트릭을 삽입하고 구조화 로깅을 강화했습니다.

#### 새로운 파일

| 파일 | 설명 |
|------|------|
| `app/core/metrics.py` | 비즈니스 핵심 엔드포인트별 Prometheus 커스텀 메트릭 정의 |

#### 수정된 파일

| 파일 | 변경 사항 |
|------|----------|
| `app/core/logging.py` | HTTP 4xx/5xx 발생 시 `http_requests_errors_total` 카운터 증가, `user_id` 로그 컨텍스트 추가 |
| `app/dependencies.py` | 인증 의존성에서 `user_id` 로깅 컨텍스트 주입 |
| `app/routers/ai_schedule.py` | AI 일정 추천 E2E 레이턴시, 실패/수용/기각/태스크 수정 카운터 계측 |
| `app/routers/chat.py` | AI 채팅 요약 E2E 레이턴시, 외부 API 레이턴시, 클라이언트 이탈 카운터 계측 |
| `app/routers/evaluations.py` | 동료 평가 제출 성공/실패 카운터 계측 |
| `app/routers/tasks.py` | 개인 투두 조회(`mine_only=true`) 레이턴시 및 DAU 프록시 카운터 계측 |

#### 수집 메트릭 목록

| 메트릭 이름 | 타입 | 설명 |
|-------------|------|------|
| `ai_chat_summary_latency_seconds` | Histogram | AI 채팅 요약 E2E 레이턴시 |
| `ai_chat_external_api_latency_seconds` | Histogram | 외부 Gemini API 순수 호출 레이턴시 |
| `ai_chat_client_disconnect_total` | Counter | 스트리밍 중 클라이언트 이탈 수 |
| `ai_schedule_latency_seconds` | Histogram | AI 일정 추천 E2E 레이턴시 |
| `ai_schedule_failure_total` | Counter | AI 일정 추천 외부 API 실패 수 (에러 타입별) |
| `ai_schedule_accept_total` | Counter | AI 추천 일정 수용 횟수 |
| `ai_schedule_reject_total` | Counter | AI 추천 일정 기각 횟수 |
| `ai_schedule_task_modify_total` | Counter | 추천 태스크 수동 수정 횟수 |
| `task_list_mine_latency_seconds` | Histogram | 개인 투두 조회 레이턴시 (DAU 프록시 지표) |
| `evaluation_submit_total` | Counter | 동료 평가 제출 성공/실패 (결과별) |
| `http_requests_errors_total` | Counter | 전체 HTTP 에러 수 (엔드포인트/상태코드별) |

#### 알림 규칙 (`monitoring/alert.rules.yml`)

| 알림명 | 조건 | 심각도 |
|--------|------|--------|
| `AIChatSummarySlowP95` | AI 채팅 요약 p95 레이턴시 5초 초과 | warning |
| `AIScheduleSlowP95` | AI 일정 추천 p95 레이턴시 5초 초과 | warning |
| `AIScheduleAPIFailureSurge` | AI 일정 추천 실패 급증 | critical |
| `EvaluationSubmitFailure` | 동료 평가 제출 실패 1건 이상 | critical |
| `TaskListMineSlowP99` | 개인 투두 조회 p99 레이턴시 1초 초과 | critical |
| `HighServerErrorRate` | 5xx 에러율 급증 | critical |
| `AIChatDisconnectSurge` | AI 채팅 클라이언트 이탈 급증 | warning |

---

## [feat] GitHub Actions CI/CD 및 docs 초기 구성 — `5130f86`

- **날짜**: 2026-05-20
- **작성자**: PYO

### 개요
GitHub Actions를 활용한 EC2 자동 배포 파이프라인과 `docs/Project Walkthrough` 문서를 최초 구성했습니다.

### 변경 내용

| 파일 | 설명 |
|------|------|
| `.github/workflows/deploy.yml` | `main`/`master` 브랜치 push 시 EC2 자동 배포 워크플로우 |
| `docs/Project Walkthrough` | 프로젝트 전반 구조 설명 문서 초안 |

### 배포 파이프라인 흐름

```
push to main
    │
    ▼
① GitHub Secrets에서 환경변수 읽어 .env 파일 생성
    │  (SUPABASE_URL, SUPABASE_KEY, GEMINI_API_KEY, CORS_ORIGINS)
    ▼
② scp-action으로 소스 전체를 EC2 서버로 복사
    │
    ▼
③ ssh-action으로 EC2 접속 → docker compose up --build -d 실행
```

### GitHub Secrets 연동 목록

| Secret 이름 | 용도 |
|-------------|------|
| `EC2_HOST` | EC2 퍼블릭 IP 주소 |
| `EC2_USERNAME` | EC2 SSH 접속 사용자명 |
| `EC2_SSH_KEY` | EC2 SSH 개인키 |
| `SUPABASE_URL` | Supabase 프로젝트 URL |
| `SUPABASE_KEY` | Supabase anon key |
| `GEMINI_API_KEY` | Google Gemini API 키 |
