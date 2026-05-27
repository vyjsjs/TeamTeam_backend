# TeamTeam 클라우드 컴퓨팅 프로젝트 — 팀원 공유 문서

> 최종 업데이트: 2026-05-28  
> 발표까지: D-14

---

## 목차

1. [최종 아키텍처](#1-최종-아키텍처)
2. [아키텍처 변경 이유](#2-아키텍처-변경-이유)
3. [현재 구현된 것](#3-현재-구현된-것)
4. [구현해야 할 것](#4-구현해야-할-것)
5. [데모 발표 계획](#5-데모-발표-계획)
6. [역할 분배](#6-역할-분배)

---

## 1. 최종 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                          INTERNET                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                   ┌─────────▼──────────┐
                   │    CloudFront      │  CDN + HTTPS 종단
                   │  (ACM 인증서 연결) │
                   └─────────┬──────────┘
                             │
                   ┌─────────▼──────────┐
                   │   S3 버킷          │  React SPA 정적 호스팅
                   │  (프론트엔드)      │
                   └─────────┬──────────┘
                             │ API 요청
                   ┌─────────▼──────────┐
                   │   ALB + WAF        │  HTTPS 443, XSS/SQLi 차단
                   └────┬──────────┬────┘
                        │          │
           ┌────────────▼──┐  ┌────▼────────────┐
           │ EC2 (AZ-a)    │  │ EC2 (AZ-c)      │
           │ t3.small      │  │ t3.small        │
           │ ─────────     │  │ ─────────       │
           │ FastAPI       │  │ FastAPI         │  Auto Scaling Group
           │ Prometheus    │  │ Prometheus      │  min:1 / max:2
           │ Grafana       │  │                 │
           └──────┬────────┘  └────────┬────────┘
                  │                    │
     ┌────────────┼────────────────────┤
     │            │                    │
     ▼            ▼                    ▼
 Supabase    Gemini Flash API    Secrets Manager
 (외부 DB)   (외부 AI API)       (API Key 보관)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  DevOps:   GitHub Actions → ECR → EC2 Rolling Deploy
  SRE:      Prometheus → Grafana ─→ CloudWatch Alarms → SNS → 이메일
  SecOps:   WAF + CloudTrail + IAM + Secrets Manager
  FinOps:   AWS Budgets + Cost Allocation Tags + Cost Explorer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 2. 아키텍처 변경 이유

중간발표 계획에서 실제 구현으로 변경된 사항과 그 이유입니다.

### 변경 사항 요약

| 구분 | 중간발표 계획 | 최종 아키텍처 | 변경 이유 |
|------|-------------|--------------|-----------|
| 데이터베이스 | AWS RDS (PostgreSQL) | **Supabase** (외부 관리형 DB) | 개발 초기에 이미 Supabase로 구현 완료. AWS Academy에서 RDS 마이그레이션 시 데이터 손실 위험 및 비용 증가. Supabase가 관리형 PostgreSQL로 동일 기능 제공 |
| AI 연동 | AWS Lambda + Bedrock | **Gemini Flash API** (직접 호출) | Gemini 2.0 Flash가 이미 FastAPI에 연동 완료. Bedrock 대비 응답 품질이 우수하고 AWS Academy에서 Bedrock 사용 제한이 있음 |
| 모니터링 | CloudWatch 중심 | **Prometheus + Grafana** (주) + CloudWatch (보조) | Prometheus + Grafana가 이미 Docker Compose에 구성 완료. 커스텀 메트릭 9개 구현됨. CloudWatch는 로그 중앙화 보조용으로 유지 |
| 컨테이너 오케스트레이션 | ECS Fargate | **EC2 + Docker Compose + ASG** | AWS Academy에서 ECS 사용 제한. Docker Compose로 이미 운영 중이며, ASG로 이중화 충분히 달성 가능 |
| 프론트엔드 | EC2에서 서빙 | **S3 + CloudFront** | 정적 파일은 S3가 99.999% SLA로 더 안정적. 비용도 EC2 대비 ~95% 절감 (FinOps) |

### 핵심 원칙
> "이미 잘 동작하는 것은 유지하고, AWS 서비스는 그 위에 더한다."

---

## 3. 현재 구현된 것

### 백엔드 (FastAPI) ✅ 완료

| 기능 | 엔드포인트 | 상태 |
|------|-----------|------|
| 인증 (JWT) | POST /api/auth/login, /register, /refresh | ✅ |
| 팀 관리 | GET/POST /api/teams, PATCH /api/teams/{id}/status | ✅ |
| 업무 관리 | GET/POST /api/teams/{id}/tasks, PATCH /api/tasks/{id} | ✅ |
| AI 일정 추천 | POST /api/teams/{id}/ai-schedule | ✅ Gemini Flash |
| 실시간 채팅 | WebSocket /ws/chat/{room_id} | ✅ |
| 공지사항 | GET/POST /api/teams/{id}/notices | ✅ |
| 자료실 | GET/POST /api/teams/{id}/references, DELETE /api/references/{id} | ✅ |
| 팀원 평가 | POST /api/evaluations | ✅ |
| 헬스체크 | GET /health | ✅ |

### SRE (모니터링) ✅ 대부분 완료

| 항목 | 상태 | 비고 |
|------|------|------|
| Prometheus 메트릭 수집 | ✅ | 9개 커스텀 메트릭 |
| Grafana 대시보드 | ✅ | provisioning JSON 존재 |
| 알림 룰 7개 | ✅ | alert.rules.yml |
| Grafana Datasource 자동 연결 | ✅ | prometheus.yml provisioning |
| 구조화 JSON 로깅 | ✅ | request_id, latency_ms, user_id |
| X-Request-ID 헤더 | ✅ | 분산 추적용 |

### 구현된 커스텀 메트릭 목록

```
ai_chat_summary_latency_seconds        (AI 요약 응답시간)
ai_schedule_latency_seconds            (AI 일정 추천 응답시간)
ai_schedule_failure_total              (AI 실패 횟수)
ws_chat_active_connections             (실시간 채팅 접속자 수)
ws_chat_messages_received_total        (채팅 메시지 수)
task_list_mine_latency_seconds         (업무 목록 응답시간)
evaluation_submit_total                (평가 제출 횟수)
http_requests_errors_total             (HTTP 에러 횟수)
```

### 프론트엔드 (React + TypeScript) ✅ 완료

| 페이지 | 파일 | 상태 |
|--------|------|------|
| 메인/랜딩 | MainPage.tsx | ✅ |
| 대시보드 | Dashboard.tsx | ✅ |
| 업무 관리 | Tasks.tsx | ✅ |
| 실시간 채팅 | Chat.tsx | ✅ |
| 공지사항 | Announcements.tsx | ✅ |
| 자료실 | FileStorage.tsx | ✅ |
| 일정/AI | Schedule.tsx | ✅ |
| 팀원 평가 | Evaluation.tsx | ✅ |
| 프로필 | Profile.tsx | ✅ |

### 인프라 현황

| 항목 | 상태 |
|------|------|
| EC2 (FastAPI 운영 중) | ✅ AWS Academy ap-northeast-2 |
| Docker Compose (FastAPI + Prometheus + Grafana) | ✅ |
| Supabase PostgreSQL | ✅ 외부 연결 |
| Gemini Flash API | ✅ 외부 연결 |
| `.env` 파일로 설정 관리 | ⚠️ 보안 취약 (개선 필요) |

---

## 4. 구현해야 할 것

### 우선순위 표

| 우선순위 | 항목 | 담당 | 이유 |
|---------|------|------|------|
| 🔴 Critical | Secrets Manager 이전 | 팀원B (SecOps) | `.env`에 실제 API Key 노출 — 발표 중 화면에 보이면 보안 사고 |
| 🔴 Critical | S3 프론트 배포 | 팀원E | 현재 로컬에서만 동작. 발표 시 데모 불가 |
| 🔴 Critical | CORS `*` → 실제 URL 교체 | 팀원B (SecOps) | 모든 도메인 허용은 보안 위반. 발표에서 지적받을 수 있음 |
| 🟡 High | ALB 생성 + EC2 연결 | 팀원A (인프라) | 이중화(Multi-AZ) 구현의 핵심. 교수님 피드백 "이중화" 대응 |
| 🟡 High | Auto Scaling Group 설정 | 팀원A (인프라) | 교수님 피드백 "이중화" 대응. 장애 자동 복구 시연 가능 |
| 🟡 High | CloudFront 배포 | 팀원E | S3 단독보다 HTTPS + CDN으로 더 완성된 구조 |
| 🟡 High | ECR 레포 생성 + GitHub Actions CI/CD 완성 | 팀원D (총괄) | 교수님 DevOps 강조. 이미 어느 정도 구현됨 → 팀원D가 마무리 |
| 🟡 High | CloudWatch Alarms → SNS | 팀원C (SRE) | 알림 전달 체계 없이는 Alert Rule이 의미 없음 |
| 🟢 Medium | CloudTrail 활성화 | 팀원B (SecOps) | AWS API 호출 감사. SecOps 발표 자료로 활용 |
| 🟢 Medium | WAF 기본 룰 연결 | 팀원B (SecOps) | ALB 앞단 보호. SecOps 시각화 자료 |
| 🟢 Medium | AWS Budgets 알림 설정 | 팀원F | FinOps 실제 구현 증거. 콘솔에서 5분이면 설정 가능 |
| 🟢 Medium | Cost Allocation Tags | 팀원F | 서비스별 비용 추적. FinOps 발표 자료 |
| 🔵 Optional | JWT Secret .env 추가 확인 | 팀원B (SecOps) | config.py에 정의되어 있으나 .env에 없을 수 있음 |

### 각 항목 상세 설명

#### Secrets Manager 이전 (🔴 Critical)
현재 `TeamTeam_backend/.env` 파일에 GEMINI_API_KEY, SUPABASE_KEY 등이 평문으로 저장되어 있습니다.
발표 중 화면을 공유할 때 이 파일이 노출되면 실제 API Key가 유출됩니다.
AWS Secrets Manager로 이전하면 EC2가 IAM 역할을 통해 키를 가져오고, 코드에는 키가 존재하지 않습니다.

#### ALB + Auto Scaling Group (🟡 High)
교수님 피드백 "이중화"에 직접 대응합니다.
ALB가 두 AZ의 EC2를 동시에 바라보고, 하나가 죽으면 자동으로 다른 AZ로 트래픽을 전환합니다.
발표 중 EC2 하나를 강제 종료하고 서비스가 계속 동작하는 것을 시연할 수 있습니다.

#### GitHub Actions CI/CD (🟡 High)
코드를 main 브랜치에 push하면 자동으로 Docker 이미지가 빌드되고 EC2에 배포됩니다.
발표 중 라이브로 코드 한 줄 수정 → push → 자동 배포 완료를 시연하면 DevOps 구현의 가장 강력한 증거가 됩니다.

---

## 5. 데모 발표 계획

### 시간 배분 (총 15분)

```
[0:00 - 2:00]  차별점 분석          (2분)  팀원D
[2:00 - 5:00]  아키텍처 + 4 Ops     (3분)  팀원D
[5:00 - 13:00] 데모 시연            (8분)  팀원D
[13:00 - 15:00] 버퍼 / 마무리       (2분)  여유 시간
```

> 버퍼 2분은 질문 대응, 시연 오류 복구, 자연스러운 전환에 사용합니다.

---

### [0:00 - 2:00] 차별점 분석 (2분)

**발표자: 팀원D (총괄)**

비교 대상 서비스와의 차별점을 1~2분으로 소개합니다.

| 비교 항목 | 기존 서비스 (Notion, Jira 등) | TeamTeam |
|----------|------------------------------|---------|
| AI 일정 추천 | ❌ 없음 | ✅ Gemini Flash로 일정 자동 생성 |
| 실시간 채팅 | 별도 앱 필요 (Slack 등) | ✅ 프로젝트 내 통합 |
| 팀원 상호 평가 | ❌ 없음 | ✅ 익명 상호 평가 내장 |
| 클라우드 네이티브 | SaaS (블랙박스) | ✅ AWS 직접 구성, 완전 가시성 |
| 모니터링 | ❌ 사용자에게 비공개 | ✅ Prometheus + Grafana 실시간 |

---

### [2:00 - 5:00] 아키텍처 + 4 Ops (3분)

**발표자: 팀원D (총괄)**

슬라이드 1장으로 아키텍처 전체를 보여주고, 각 영역을 20~30초씩 설명합니다.

```
DevOps  (30초): GitHub Actions → ECR → EC2 자동 배포
SRE     (40초): Prometheus 9개 메트릭, Grafana 대시보드, 알림 7개 룰
SecOps  (40초): Secrets Manager, WAF, CloudTrail, IAM 최소권한
FinOps  (30초): S3 vs EC2 비용 비교, AWS Budgets 알림
```

---

### [5:00 - 13:00] 데모 시연 (8분)

#### 시연 흐름

```
Step 1  [0:00 - 1:00]  로그인 → 팀 대시보드 진입
Step 2  [1:00 - 2:30]  AI 일정 추천 (Gemini Flash) ← 핵심 차별점
Step 3  [2:30 - 3:30]  실시간 채팅 (WebSocket)
Step 4  [3:30 - 4:30]  업무 관리 (상태 변경 → Grafana 실시간 반영)
Step 5  [4:30 - 5:30]  공지사항 + 자료실
Step 6  [5:30 - 7:00]  Grafana 대시보드 (SRE 메트릭 라이브)
Step 7  [7:00 - 8:00]  CI/CD 파이프라인 (GitHub Actions 배포 로그)
```

#### 각 Step 상세

**Step 1 — 로그인 → 대시보드 (1분) — 팀원D**
- 브라우저에서 CloudFront URL 접속 (S3 배포된 프론트)
- 로그인 → 팀 대시보드 화면
- 진행률 바, 오늘 일정, 팀원 목록 확인
- 포인트: "S3 + CloudFront로 배포된 React 앱이 ALB를 통해 백엔드와 통신합니다"

**Step 2 — AI 일정 추천 (1분 30초) ← 가장 중요**
- 일정 페이지 → AI 추천 요청
- Gemini Flash가 팀 상황을 분석해 일정 제안
- 승인/거절 버튼으로 반영
- 포인트: "Gemini 2.0 Flash API를 직접 연동해 팀 일정을 자동 생성합니다"

**Step 3 — 실시간 채팅 (1분)**
- 브라우저 2개 열기 (또는 팀원 2명 접속)
- 채팅 입력 → 즉시 상대방 화면에 반영
- 포인트: "WebSocket으로 서버 polling 없이 실시간 통신합니다"

**Step 4 — 업무 관리 → Grafana 연동 (1분)**
- 업무 상태를 진행 전 → 진행 중 → 완료로 변경
- Grafana 대시보드로 전환 → task 관련 메트릭 수치 변화 확인
- 포인트: "사용자 행동이 즉시 SRE 메트릭에 반영됩니다"

**Step 5 — 공지사항 + 자료실 (1분)**
- 공지 등록 (리더 공지 핀 고정)
- 자료실 URL 등록 (Google Drive 링크)
- 포인트: 빠르게 기능 존재 확인 수준으로 진행

**Step 6 — Grafana 대시보드 라이브 (1분 30초)**
- Grafana 접속 (EC2:3000 또는 ALB 경유)
- AI 응답시간 히스토그램, WebSocket 접속자 수, HTTP 에러율 확인
- 알림 룰 목록 보여주기 (7개 룰)
- 포인트: "p95 응답시간이 5초 초과 시 자동으로 Slack 알림을 보냅니다"

**Step 7 — CI/CD 파이프라인 (1분)**
- GitHub Actions 탭 → 최근 배포 워크플로 로그 보여주기
- 또는 라이브로 코드 1줄 수정 → push → 자동 배포 진행 보여주기
- ECR에 이미지가 쌓이는 것 확인
- 포인트: "코드 push만 하면 자동으로 EC2에 무중단 배포됩니다"

---

### [13:00 - 15:00] 버퍼 / 마무리 (2분)

- 예상보다 빠르게 끝나면: 아키텍처 다이어그램 한 번 더 보여주며 요약
- 시연 오류 발생 시: 미리 찍어둔 시연 영상 재생
- 질문 준비: 아래 예상 질문 참고

### 예상 질문 & 답변 준비

| 예상 질문 | 답변 포인트 |
|----------|-----------|
| DB가 AWS 외부인데 괜찮나요? | Supabase는 관리형 PostgreSQL로 99.99% SLA 제공. AWS RDS와 동일 엔진, 외부 연결로도 안정적 운영 가능 |
| Lambda/ECS 안 쓴 이유는? | AWS Academy 서비스 제한 + 이미 Docker Compose 운영 중. EC2 + ASG로 동일한 이중화 달성 |
| SLO는 어떻게 정의했나요? | 가용성 99.9%, p99 응답시간 500ms 이하, 에러율 1% 미만 |
| Secrets Manager 어떻게 쓰나요? | EC2 IAM Instance Profile → Secrets Manager 읽기 권한 → 앱 시작 시 자동 주입 |

---

## 6. 역할 분배

| 팀원 | 담당 | 난이도 | 주요 작업 |
|------|------|--------|----------|
| A | 인프라 리더 | 상 | VPC, EC2×2, ASG, ALB, IAM, ACM |
| B | SecOps | 중 | Secrets Manager, WAF, CloudTrail, CORS 수정 |
| C | SRE / 로깅 | 중 | Grafana 대시보드 완성, CloudWatch Alarms, SNS |
| D | 총괄 PM | 하 | ECR 레포 생성, GitHub Actions 완성, 발표 자료, 데모 리허설, **전체 발표** |
| E | 프론트 배포 | 하 | S3 버킷 생성, npm build, CloudFront 연결 |
| F | FinOps | 하 | AWS Budgets 설정, Cost Allocation Tags, Cost Explorer 비용 분석 자료 |
| G | 테스트 | 하 | Dev 환경, 부하 테스트, 데모 시나리오 검증 |

### 2주 타임라인

```
Week 1 (D-14 ~ D-7):
  Day 1-2:  팀원A — VPC, EC2, ASG, ALB 구성
            팀원B — Secrets Manager 이전, CORS 수정
  Day 3-4:  팀원E — S3 배포, CloudFront 연결
            팀원D — ECR 레포 생성 + GitHub Actions 완성
  Day 5-7:  팀원C — CloudWatch Alarms + SNS 연결
            팀원F — AWS Budgets, Cost Tags 설정
            팀원G — 전체 연동 테스트

Week 2 (D-7 ~ D-1):
  Day 8-10: 전체 통합 테스트 (시나리오대로 전체 흐름 리허설)
  Day 11-12: 발표 자료 완성, 아키텍처 다이어그램 업데이트
  Day 13:   최종 리허설 (시간 측정)
  Day 14:   발표 당일 — 오전에 서비스 상태 최종 확인
```
