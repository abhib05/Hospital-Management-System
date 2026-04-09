"""
main.py – FastAPI application entry point.

Startup sequence:
  1. Load settings from .env
  2. Initialise MySQL connection pool
  3. Load faster-whisper model (CPU / int8) — singleton
  4. Register all routers
  5. Mount static frontend files

Run:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import get_settings
from backend.database import get_pool
from backend.services.transcription_service import get_whisper_model
from backend.middleware.audit_middleware import AuditMiddleware

# Controllers
from backend.controllers.auth_controller import router as auth_router
from backend.controllers.doctor_controller import router as doctor_router
from backend.controllers.pharmacist_controller import router as pharmacist_router
from backend.controllers.patient_controller import router as patient_router
from backend.controllers.admin_controller import router as admin_router
from backend.controllers.transcription_controller import router as transcription_router

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ───────────────────────────────────────────────────────────────
    logger.info("Starting HMS backend (env=%s)", settings.app_env)

    # 1. Warm up DB pool
    try:
        get_pool()
        logger.info("Database connection pool ready.")
    except Exception as exc:
        logger.error("Failed to connect to MySQL: %s", exc)

    # 2. Load Whisper model once (Singleton)
    try:
        os.makedirs(settings.audio_upload_dir, exist_ok=True)
        model = get_whisper_model()
        if model:
            logger.info("faster-whisper model is ready.")
        else:
            logger.warning("faster-whisper model could not be loaded. Transcription will be unavailable.")
    except Exception as exc:
        logger.error("Whisper init error: %s", exc)

    yield

    # ── SHUTDOWN ──────────────────────────────────────────────────────────────
    logger.info("HMS backend shutting down.")


# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Hospital Management System API",
    description="Full-featured HMS with AI transcription, RBAC, and billing.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Audit middleware (logs every API hit) ─────────────────────────────────────
app.add_middleware(AuditMiddleware)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(doctor_router)
app.include_router(pharmacist_router)
app.include_router(patient_router)
app.include_router(admin_router)
app.include_router(transcription_router)


# ── Serve frontend static files ───────────────────────────────────────────────
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["Health"])
async def health():
    return {"status": "ok", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=(settings.app_env == "development"),
    )
