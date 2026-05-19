# TeamTeam Backend

> 26-1 클라우드 컴퓨팅 수업 프로젝트 백엔드 레포입니다.

## 기술스택

- **Framework**: Python 3.12 / FastAPI
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Simple ID-based Auth (데모용)
- **AI**: Gemini API (gemini-2.5-flash) — 일정 추천 & 채팅 요약
- **Monitoring**: Prometheus + 구조화 JSON 로깅
- **Deployment**: Docker + Docker Compose → AWS EC2

## 프로젝트 구조

```
app/
├── main.py              # FastAPI 앱, 미들웨어, CORS 설정
├── dependencies.py      # 인증 dependency (get_current_user)
├── core/
│   ├── config.py        # 환경변수 설정 (pydantic-settings)
│   ├── supabase.py      # Supabase 클라이언트 싱글턴
│   ├── security.py      # ID 기반 단순 인증 유틸
│   └── logging.py       # 구조화 JSON 로깅 미들웨어
├── routers/
│   ├── auth.py          # POST /api/auth/signup, /api/auth/login
│   ├── users.py         # GET/PATCH /api/users/me
│   ├── teams.py         # 팀 생성/참여/목록/대시보드/상태변경
│   ├── notices.py       # 공지사항 CRUD
│   ├── tasks.py         # 업무 관리
│   ├── ai_schedule.py   # AI 일정 추천 세션
│   ├── references.py    # 자료실
│   ├── chat.py          # 채팅방 & 메시지 & AI 프롬프트
│   └── evaluations.py   # 상호평가
└── schemas/             # Pydantic 요청/응답 모델
```

## 로컬 실행

```bash
# 가상환경 생성 & 활성화
python3 -m venv .venv
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행 (개발 모드)
uvicorn app.main:app --reload --port 8000
```

## Docker 실행

```bash
docker compose up --build
```

## 환경변수 (.env)

| 변수명 | 설명 | 필수 |
|--------|------|------|
| `SUPABASE_URL` | Supabase 프로젝트 URL | ✅ |
| `SUPABASE_KEY` | Supabase anon key | ✅ |
| `JWT_SECRET_KEY` | JWT 시크릿 키 | ✅ |
| `GEMINI_API_KEY` | Gemini API 키 (AI 기능용) | ❌ |
| `CORS_ORIGINS` | 허용 오리진 (쉼표 구분) | ❌ |

## API 엔드포인트

### 인증 (Auth)
| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | `/api/auth/signup` | 회원가입 |
| POST | `/api/auth/login` | 로그인 |

### 사용자 (Users)
| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/api/users/me` | 마이페이지 (평가 통계 포함) |
| PATCH | `/api/users/me` | 내 정보 수정 |

### 팀 (Teams)
| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | `/api/teams` | 팀 생성 |
| POST | `/api/teams/join` | 초대 코드로 팀 참여 |
| GET | `/api/teams` | 내 팀 목록 |
| GET | `/api/teams/{teamId}` | 팀 대시보드 |
| PATCH | `/api/teams/{teamId}/status` | 상태 변경 (팀장) |

### 공지사항 (Notices)
| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/api/teams/{teamId}/notices` | 공지 목록 |
| POST | `/api/teams/{teamId}/notices` | 공지 작성 |
| GET | `/api/notices/{noticeId}` | 공지 상세 |

### 업무 (Tasks)
| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/api/teams/{teamId}/tasks` | 업무 목록 (?mine_only=true) |
| POST | `/api/teams/{teamId}/tasks` | 업무 추가 |
| PATCH | `/api/tasks/{taskId}` | 업무 수정 |

### AI 스케줄링
| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | `/api/teams/{teamId}/ai-sessions` | AI 추천 요청 (팀장) |
| GET | `/api/ai-sessions/{sessionId}` | 추천 일정 확인 |
| POST | `/api/ai-sessions/{sessionId}/confirm` | 일정 확정 |

### 자료실 (References)
| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/api/teams/{teamId}/references` | 자료 목록 |
| POST | `/api/teams/{teamId}/references` | 자료 업로드 |
| DELETE | `/api/references/{refId}` | 자료 삭제 |

### 채팅 (Chat)
| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | `/api/teams/{teamId}/chat-rooms` | 채팅방 생성 |
| GET | `/api/teams/{teamId}/chat-rooms` | 채팅방 목록 |
| GET | `/api/chat-rooms/{roomId}/messages` | 메시지 조회 |
| POST | `/api/chat-rooms/{roomId}/messages` | 메시지 전송 |
| POST | `/api/chat-rooms/{roomId}/ai-prompt` | AI 요약 생성 |

### 상호평가 (Evaluations)
| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | `/api/teams/{teamId}/evaluations` | 평가 제출 |
| GET | `/api/teams/{teamId}/members/eval-status` | 평가 현황 |

### 기타
| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/` | 헬스 체크 |
| GET | `/health` | 헬스 체크 |
| GET | `/metrics` | Prometheus 메트릭 |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc |
