"""Custom Prometheus metrics for TeamTeam business-critical endpoints."""

from prometheus_client import Counter, Histogram

# ── 1. AI 채팅 요약 (POST /api/chat-rooms/{room_id}/ai-prompt) ──────────────
ai_chat_summary_latency = Histogram(
    "ai_chat_summary_latency_seconds",
    "End-to-end latency for AI chat summary endpoint",
    buckets=[0.5, 1, 2, 3, 5, 10, 30],
)
ai_chat_external_latency = Histogram(
    "ai_chat_external_api_latency_seconds",
    "Pure external AI API call latency (isolated from server overhead)",
    buckets=[0.5, 1, 2, 3, 5, 10, 30],
)
ai_chat_disconnect_total = Counter(
    "ai_chat_client_disconnect_total",
    "Client disconnects detected during AI chat summary generation",
)

# ── 2. AI 일정 추천 (POST /api/teams/{team_id}/ai-sessions) ──────────────────
ai_schedule_latency = Histogram(
    "ai_schedule_latency_seconds",
    "End-to-end latency for AI schedule recommendation endpoint",
    buckets=[0.5, 1, 2, 3, 5, 10, 30],
)
ai_schedule_failure_total = Counter(
    "ai_schedule_failure_total",
    "AI schedule external API failures by error type",
    ["error_type"],
)

# ── 3. AI 추천 수용/기각/수정률 ───────────────────────────────────────────────
ai_schedule_accept_total = Counter(
    "ai_schedule_accept_total",
    "AI schedule sessions confirmed (accepted by team leader)",
)
ai_schedule_reject_total = Counter(
    "ai_schedule_reject_total",
    "AI schedule sessions explicitly rejected by team leader",
)
ai_schedule_task_modify_total = Counter(
    "ai_schedule_task_modify_total",
    "Number of AI recommended tasks manually modified before confirm",
)

# ── 5. 개인 투두 조회 (GET /api/teams/{team_id}/tasks?mine_only=true) ─────────
task_list_mine_latency = Histogram(
    "task_list_mine_latency_seconds",
    "DB query + API latency for personal task list (mine_only=true)",
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
)
task_list_mine_total = Counter(
    "task_list_mine_requests_total",
    "Total personal task list requests — proxy for Daily Active Users",
)

# ── 6. 동료 평가 제출 (POST /api/teams/{team_id}/evaluations) ────────────────
evaluation_submit_total = Counter(
    "evaluation_submit_total",
    "Evaluation submission outcomes with error classification",
    ["status", "error_type"],
)

# ── 7. 글로벌 에러 카운터 (미들웨어 통합) ─────────────────────────────────────
http_errors_total = Counter(
    "http_requests_errors_total",
    "HTTP errors by endpoint, status code, and error type",
    ["endpoint", "status_code", "error_type"],
)

# ── 8. 웹소켓 채팅 메트릭 ──────────────────────────────────────────────────────
from prometheus_client import Gauge  # noqa: E402

ws_active_connections = Gauge(
    "ws_chat_active_connections",
    "Currently active WebSocket connections per chat room",
    ["room_id"],
)
ws_connections_total = Counter(
    "ws_chat_connections_total",
    "Total WebSocket connections accepted (per room)",
    ["room_id"],
)
ws_messages_received_total = Counter(
    "ws_chat_messages_received_total",
    "Total messages received over WebSocket (per room)",
    ["room_id"],
)
