from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.actions import router as actions_router
from backend.api.events import router as events_router
from backend.api.scan import router as scan_router
from backend.api.stats import router as stats_router
from backend.database.database import create_db_and_tables
from backend.services.security_service import SecurityService


create_db_and_tables()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    create_db_and_tables()
    app.state.security_service = SecurityService()
    app.state.app_version = "1.0.0"
    yield


app = FastAPI(
    title="SentinelAI Security API",
    description="ML-powered prompt injection detection and policy-based AI agent security.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict:
    return {"message": "SentinelAI Security API is running.", "version": "1.0.0"}


@app.get("/health")
def health() -> dict:
    db_ok = True
    security_ok = True
    model_ok = True

    try:
        create_db_and_tables()
    except Exception:
        db_ok = False

    try:
        service = getattr(app.state, "security_service", None)
        if service is None:
            service = SecurityService()
            app.state.security_service = service
        if not hasattr(service, "prompt_detector"):
            security_ok = False
    except Exception:
        security_ok = False

    try:
        service = getattr(app.state, "security_service", None) or SecurityService()
        if service is not None:
            service.prompt_detector.detect("Please summarize the quarterly sales report.")
    except Exception:
        model_ok = False

    version = getattr(app.state, "app_version", "1.0.0")
    return {
        "status": "ok" if db_ok and security_ok and model_ok else "degraded",
        "database": "connected" if db_ok else "error",
        "security_engine": "initialized" if security_ok else "unavailable",
        "ml_model": "loaded" if model_ok else "unavailable",
        "app_version": version,
    }


@app.exception_handler(Exception)
async def handle_unexpected_exception(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "An internal server error occurred.", "message": "Please check the request and try again."},
    )


app.include_router(scan_router)
app.include_router(actions_router)
app.include_router(events_router)
app.include_router(stats_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)
