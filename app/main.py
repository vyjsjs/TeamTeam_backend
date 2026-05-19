"""TeamTeam Backend — FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import get_settings
from app.core.logging import RequestLoggingMiddleware
from app.routers import auth, users, teams, notices, tasks, ai_schedule, references, chat, evaluations

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="팀 프로젝트 협업 플랫폼 백엔드 API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ──────────────────────────────────────────────
# Middleware
# ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

# ──────────────────────────────────────────────
# Prometheus metrics
# ──────────────────────────────────────────────
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# ──────────────────────────────────────────────
# Routers
# ──────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(teams.router)
app.include_router(notices.router)
app.include_router(tasks.router)
app.include_router(ai_schedule.router)
app.include_router(references.router)
app.include_router(chat.router)
app.include_router(evaluations.router)


# ──────────────────────────────────────────────
# Health check
# ──────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
