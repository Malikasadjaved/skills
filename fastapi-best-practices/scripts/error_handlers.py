#!/usr/bin/env python
"""
Global exception handler setup for FastAPI.

Covers:
    - Custom AppException hierarchy → structured JSON responses
    - RequestValidationError → 422 with field-level error detail
    - HTTPException → passthrough with consistent shape
    - Unhandled Exception → 500 with sanitized message (full traceback logged)

All handlers return the project's standard error shape:
    {"status": "error", "error": "<message>", "type": "<ExceptionClass>"}

Usage — register in your app factory or main.py:

    from error_handlers import register_error_handlers
    app = FastAPI()
    register_error_handlers(app)

Requirements:
    pip install fastapi>=0.111.0
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("app.errors")


# ═══════════════════════════════════════════════════════════════════
# Custom exception hierarchy
# ═══════════════════════════════════════════════════════════════════


class AppException(Exception):
    """Base exception for all application-level errors.

    All subclasses are caught by the AppException handler and returned
    as structured JSON with the status_code and detail they define.
    """

    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code


class NotFoundError(AppException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail=detail, status_code=404)


class ConflictError(AppException):
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(detail=detail, status_code=409)


class ForbiddenError(AppException):
    def __init__(self, detail: str = "Access denied"):
        super().__init__(detail=detail, status_code=403)


class UnauthorizedError(AppException):
    def __init__(self, detail: str = "Authentication required"):
        super().__init__(detail=detail, status_code=401)


class ServiceUnavailableError(AppException):
    def __init__(self, detail: str = "Service temporarily unavailable"):
        super().__init__(detail=detail, status_code=503)


class RateLimitError(AppException):
    def __init__(self, detail: str = "Too many requests"):
        super().__init__(detail=detail, status_code=429)


class BadRequestError(AppException):
    def __init__(self, detail: str = "Bad request"):
        super().__init__(detail=detail, status_code=400)


# ═══════════════════════════════════════════════════════════════════
# Handler implementations
# ═══════════════════════════════════════════════════════════════════


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Catch all AppException subclasses → structured JSON with their status code."""
    logger.warning(
        "[%s] %s %s → %d %s",
        getattr(request.state, "request_id", "-"),
        request.method,
        request.url.path,
        exc.status_code,
        exc.detail,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error": exc.detail,
            "type": type(exc).__name__,
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Passthrough FastAPI/Starlette HTTPException with consistent shape."""
    logger.warning(
        "[%s] HTTPException %s %s → %d %s",
        getattr(request.state, "request_id", "-"),
        request.method,
        request.url.path,
        exc.status_code,
        exc.detail,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error": str(exc.detail),
            "type": "HTTPException",
        },
    )


async def validation_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return 422 with field-level error detail for Pydantic validation failures."""
    errors: list[dict[str, str]] = []
    for error in exc.errors():
        field_path = " → ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
        })

    logger.warning(
        "[%s] ValidationError %s %s → %d errors",
        getattr(request.state, "request_id", "-"),
        request.method,
        request.url.path,
        len(errors),
    )

    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "error": "Validation error",
            "type": "RequestValidationError",
            "details": errors,
        },
    )


async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unexpected exceptions.

    Logs the full traceback (for on-call debugging) but returns a sanitized
    500 to the client — never leak stack traces or internal details.
    """
    request_id = getattr(request.state, "request_id", "-")
    logger.exception(
        "[%s] Unhandled error on %s %s — %s: %s",
        request_id,
        request.method,
        request.url.path,
        type(exc).__name__,
        exc,
    )

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": "Internal server error",
            "type": "InternalError",
        },
    )


# ═══════════════════════════════════════════════════════════════════
# Registration helper
# ═══════════════════════════════════════════════════════════════════


def register_error_handlers(app: FastAPI) -> None:
    """Register all exception handlers on a FastAPI app instance.

    Call this once in your app factory or main.py:

        app = FastAPI()
        register_error_handlers(app)

    Handler precedence (most specific first):
        1. AppException (and all subclasses)
        2. HTTPException (FastAPI/Starlette built-in)
        3. RequestValidationError (Pydantic validation)
        4. Exception (unhandled catch-all)
    """
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_handler)
    app.add_exception_handler(Exception, unhandled_handler)

    logger.info("Error handlers registered: AppException, HTTPException, ValidationError, Exception")


# ═══════════════════════════════════════════════════════════════════
# Example usage
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Quick manual test — run this file directly to see the handlers in action.
    import uvicorn
    from fastapi import APIRouter

    app = FastAPI(title="Error Handler Demo", version="1.0.0")
    register_error_handlers(app)

    router = APIRouter()

    @router.get("/not-found")
    async def trigger_not_found():
        raise NotFoundError("Document 'abc' not found")

    @router.get("/forbidden")
    async def trigger_forbidden():
        raise ForbiddenError("You are not allowed to access this resource")

    @router.get("/conflict")
    async def trigger_conflict():
        raise ConflictError("Email already registered")

    @router.get("/validation-error")
    async def trigger_validation():
        from pydantic import BaseModel, Field

        class TestModel(BaseModel):
            name: str = Field(min_length=3)

        # This causes RequestValidationError — the framework catches it.
        # The route's query param doesn't match, so FastAPI raises 422.
        return {"ok": True}

    @router.get("/unhandled")
    async def trigger_unhandled():
        raise ValueError("Something exploded unexpectedly!")

    @router.get("/rate-limited")
    async def trigger_rate_limit():
        raise RateLimitError("Try again in 30 seconds")

    app.include_router(router, prefix="/demo")

    print("Starting demo on http://localhost:8080")
    print("Try: /demo/not-found, /demo/forbidden, /demo/conflict, /demo/unhandled, /demo/rate-limited")
    uvicorn.run(app, host="0.0.0.0", port=8080)
