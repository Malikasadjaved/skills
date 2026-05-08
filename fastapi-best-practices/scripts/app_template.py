#!/usr/bin/env python
"""
Production-ready FastAPI app scaffold.

Usage:
    python app_template.py                  # run on default port 8080
    uvicorn app_template:app --reload       # dev mode with hot reload

Features:
    - Lifespan-based startup/shutdown (no @app.on_event)
    - pydantic-settings BaseSettings from .env
    - Request ID + timing middleware
    - Structured JSON error handlers
    - CORS configured from settings
    - Versioned router with health + example CRUD

Requirements:
    pip install fastapi>=0.111.0 pydantic>=2.0 pydantic-settings uvicorn[standard]
"""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.middleware.base import BaseHTTPMiddleware

# ═══════════════════════════════════════════════════════════════════
# Settings
# ═══════════════════════════════════════════════════════════════════


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "FastAPI App"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8080

    # CORS
    allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"],
    )

    # External service URLs (placeholder — wire up in lifespan)
    qdrant_url: str = "http://localhost:6333"


@lru_cache
def get_settings() -> Settings:
    return Settings()


# ═══════════════════════════════════════════════════════════════════
# Middleware
# ═══════════════════════════════════════════════════════════════════


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.request_id = request.headers.get(
            "X-Request-ID", str(uuid.uuid4())
        )
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Response-Time"] = f"{elapsed_ms:.1f}ms"
        return response


# ═══════════════════════════════════════════════════════════════════
# Custom exceptions
# ═══════════════════════════════════════════════════════════════════


class AppException(Exception):
    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code


class NotFoundError(AppException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail=detail, status_code=404)


# ═══════════════════════════════════════════════════════════════════
# Lifespan
# ═══════════════════════════════════════════════════════════════════


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings

    # ── Startup ──────────────────────────────────────
    # Wire up external clients here (DB pool, Qdrant, Redis, etc.)
    # For now, store settings as a placeholder.
    app.state.started_at = time.time()
    print(f"[lifespan] {settings.app_name} starting on {settings.host}:{settings.port}")

    yield  # ← app handles requests here

    # ── Shutdown ─────────────────────────────────────
    # Close connections, flush buffers, etc.
    print("[lifespan] Shutdown complete")


# ═══════════════════════════════════════════════════════════════════
# App factory
# ═══════════════════════════════════════════════════════════════════

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="Production-ready FastAPI scaffold",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )

    # Custom middleware (applied in reverse — RequestID runs last/outermost)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # ── Exception handlers ──────────────────────────
    from fastapi.exceptions import RequestValidationError

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "error": exc.detail,
                "type": type(exc).__name__,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        errors = [
            {
                "field": " → ".join(str(loc) for loc in e["loc"]),
                "message": e["msg"],
            }
            for e in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={"status": "error", "error": "Validation error", "details": errors},
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception):
        import logging

        logger = logging.getLogger("app")
        logger.exception(f"Unhandled error on {request.method} {request.url.path}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": "Internal server error"},
        )

    # ── Health routes (hidden from OpenAPI docs) ────

    @app.get("/health", include_in_schema=False)
    async def health(request: Request):
        return {
            "status": "ok",
            "uptime_seconds": round(time.time() - request.app.state.started_at, 1),
        }

    @app.get("/readyz", include_in_schema=False)
    async def readyz():
        return {"status": "ok", "ready": True}

    # ── Include routers ─────────────────────────────
    from fastapi import APIRouter

    v1_router = APIRouter(prefix="/api/v1", tags=["v1"])

    # --- Example Pydantic models ---
    class ItemCreate(BaseModel):
        model_config = {"str_strip_whitespace": True, "extra": "forbid"}
        name: str = Field(min_length=1, max_length=200)
        description: str = Field(default="")

    class ItemResponse(BaseModel):
        id: str
        name: str
        description: str

    # In-memory store (replace with real DB in production)
    _items: dict[str, dict] = {}

    @v1_router.get("/items", response_model=list[ItemResponse])
    async def list_items():
        return [
            ItemResponse(id=k, name=v["name"], description=v["description"])
            for k, v in _items.items()
        ]

    @v1_router.post("/items", response_model=ItemResponse, status_code=201)
    async def create_item(body: ItemCreate, request: Request):
        import uuid as _uuid

        item_id = str(_uuid.uuid4())
        _items[item_id] = body.model_dump()
        return ItemResponse(id=item_id, **body.model_dump())

    @v1_router.get("/items/{item_id}", response_model=ItemResponse)
    async def get_item(item_id: str):
        if item_id not in _items:
            raise NotFoundError(detail=f"Item '{item_id}' not found")
        v = _items[item_id]
        return ItemResponse(id=item_id, name=v["name"], description=v["description"])

    app.include_router(v1_router)

    return app


# ═══════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════

app = create_app()

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app_template:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
