---
name: fastapi-best-practices
description: >
  Use when building or reviewing FastAPI applications — async route design, 
  asynccontextmanager lifespan for DB/Qdrant/Redis startup, Pydantic v2 with 
  model_config and model_validator, Annotated+Depends injection, JWT with 
  OAuth2PasswordBearer, structured AppException hierarchy, CORS, background 
  tasks, and OpenAPI config. Python 3.11+, pydantic>=2.0.
triggers:
  - fastapi
  - python api
  - async api
  - pydantic
  - rest api python
  - uvicorn
  - starlette
  - python backend
  - lifespan
  - dependency injection
version: 1.0.0
author: malikasadjaved
---

## Project Structure

```
app/
├── main.py                  # FastAPI() create, lifespan, include routers, middleware
├── core/
│   ├── config.py            # pydantic-settings BaseSettings (reads .env)
│   ├── security.py          # JWT encode/decode, password hashing
│   └── exceptions.py        # Custom AppException hierarchy
├── models/
│   ├── request.py           # Pydantic v2 request schemas (inbound)
│   └── response.py          # Pydantic v2 response schemas (outbound)
├── dependencies/
│   ├── database.py          # get_db (async session yield)
│   ├── auth.py              # get_current_user (JWT decode)
│   └── services.py          # get_qdrant_client, get_redis, get_http_client
├── routers/
│   ├── health.py            # /health, /readyz
│   ├── auth.py              # /auth/login, /auth/refresh
│   └── v1/                  # Versioned API
│       ├── __init__.py
│       └── documents.py
├── services/                # Business logic (no HTTP concerns)
│   ├── document_service.py
│   └── notification_service.py
└── middleware/
    ├── request_id.py        # X-Request-ID injection
    └── timing.py            # X-Response-Time header
```

Keep `routers/` thin (parse request, call service, return response). Put
business logic in `services/`. Never import `Request` or `Response` in
service layer modules.

## Lifespan Pattern

Use `asynccontextmanager` lifespan. Never use the deprecated `@app.on_event("startup")`
or `@app.on_event("shutdown")` — they are removed in FastAPI 0.112+.

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ──────────────────────────────────────────
    # Init resources BEFORE yield — failures here prevent app start
    pool = await create_db_pool(app.state.settings.database_url)
    app.state.db_pool = pool

    qdrant = QdrantClient(url=app.state.settings.qdrant_url)
    app.state.qdrant = qdrant

    print(f"[lifespan] Ready — {app.state.settings.app_name}")

    yield  # ← app runs here

    # ── SHUTDOWN ─────────────────────────────────────────
    # Cleanup AFTER yield — runs on SIGTERM/SIGINT
    await pool.close()
    qdrant.close()
    print("[lifespan] Shutdown complete")


app = FastAPI(lifespan=lifespan)
```

Store shared resources on `request.app.state`:

```python
# In a dependency or route
def get_qdrant(request: Request) -> QdrantClient:
    return request.app.state.qdrant
```

If a startup resource is optional (e.g., Qdrant not running locally),
wrap its init in try/except and store None — then guard in the dependency.

## Pydantic v2 Models

### BaseModel with model_config

```python
from pydantic import BaseModel, Field
from datetime import datetime

class DocumentCreate(BaseModel):
    model_config = {"str_strip_whitespace": True, "extra": "forbid"}

    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    domain: str = Field(pattern=r"^(finance|hr|legal|shared)$")
    tags: list[str] = Field(default_factory=list, max_length=10)


class DocumentResponse(BaseModel):
    model_config = {"from_attributes": True}  # enables ORM → Pydantic

    id: str
    title: str
    domain: str
    created_at: datetime
    snippet: str = Field(exclude=True)  # present in code, excluded from JSON
```

### computed_field

```python
from pydantic import BaseModel, computed_field

class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    first_name: str
    last_name: str

    @computed_field
    def display_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @computed_field
    def initials(self) -> str:
        return f"{self.first_name[0]}{self.last_name[0]}".upper()
```

### field_validator

```python
from pydantic import BaseModel, field_validator

class SearchQuery(BaseModel):
    query: str
    top_k: int = 5

    @field_validator("top_k")
    @classmethod
    def clamp_top_k(cls, v: int) -> int:
        return max(1, min(50, v))

    @field_validator("query")
    @classmethod
    def strip_query(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("query must not be empty")
        return stripped
```

### model_validator (cross-field)

```python
from pydantic import BaseModel, model_validator

class DateRange(BaseModel):
    start_date: str
    end_date: str

    @model_validator(mode="after")
    def check_date_order(self):
        if self.start_date > self.end_date:
            raise ValueError("start_date must be <= end_date")
        return self
```

### Request vs Response separation

Always separate inbound from outbound models — even if they look identical today:

```python
# models/request.py
class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=8)

# models/response.py
class UserPublic(BaseModel):
    id: str
    email: str
    # Never include password, hashed_password, internal flags
```

This prevents accidental password leaks and decouples API contract from internal
schema changes.

## Dependency Injection

Use `Annotated` + `Depends` (Python 3.11+ preferred style):

```python
from typing import Annotated
from fastapi import Depends, Request

# ── DB session (yields for cleanup) ──────────────────────

async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    async with request.app.state.db_pool.session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Current user from JWT ────────────────────────────────

async def get_current_user(
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    try:
        payload = decode_jwt(token, request.app.state.settings.jwt_secret)
        user_id = payload["sub"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await fetch_user(request.app.state.db_pool, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ── Qdrant client ────────────────────────────────────────

def get_qdrant(request: Request) -> QdrantClient:
    client = request.app.state.qdrant
    if client is None:
        raise HTTPException(status_code=503, detail="Qdrant not available")
    return client


# ── Shortcut types ───────────────────────────────────────

CurrentUser = Annotated[User, Depends(get_current_user)]
Database = Annotated[AsyncSession, Depends(get_db)]
Qdrant = Annotated[QdrantClient, Depends(get_qdrant)]


# ── Route usage ──────────────────────────────────────────

@app.get("/api/documents")
async def list_documents(
    db: Database,
    user: CurrentUser,
    qdrant: Qdrant,
):
    ...
```

The `Annotated` shortcut types go in `dependencies/__init__.py` so every router
imports them cleanly.

## Router Organization

```python
# routers/v1/documents.py
from fastapi import APIRouter
from dependencies import Database, CurrentUser, Qdrant

router = APIRouter(
    prefix="/api/v1/documents",
    tags=["v1 — Documents"],
    dependencies=[],  # router-level deps (auth guard etc.)
)


@router.get("", response_model=list[DocumentResponse])
async def list_docs(
    db: Database,
    user: CurrentUser,
    domain: str | None = None,
):
    """List documents, optionally filtered by domain."""
    ...


@router.post("", response_model=DocumentResponse, status_code=201)
async def create_doc(
    body: DocumentCreate,
    db: Database,
    user: CurrentUser,
):
    ...
```

Include in main app:

```python
# main.py
from routers.v1.documents import router as docs_router

app.include_router(docs_router)
```

Use `dependencies=[Depends(get_current_user)]` on the router itself when every
route in that router requires auth — cleaner than repeating it on every endpoint.

## Async Route Patterns

### When async def vs def

- **`async def`**: when your route awaits something (DB query, HTTP call, Redis).
  FastAPI runs these on the event loop — zero overhead.
- **`def`**: when your route is pure CPU work with no await. FastAPI runs it in
  a threadpool so the event loop isn't blocked. Use sparingly — if you need a
  threadpool explicitly, use `run_in_executor` instead.

### Async DB query

```python
@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: str, db: Database) -> DocumentResponse:
    result = await db.execute(
        select(Document).where(Document.id == doc_id)
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse.model_validate(doc)
```

### Async HTTP call with httpx

```python
import httpx

@app.post("/api/chat")
async def proxy_to_whatsapp(body: ChatRequest, request: Request):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{request.app.state.settings.whatsapp_bot_url}/chat",
            json={"message": body.message, "chat_jid": body.chat_jid},
            headers={"Authorization": f"Bearer {request.app.state.settings.chat_secret}"},
            timeout=30.0,
        )
    response.raise_for_status()
    return response.json()
```

### Sync code in threadpool

```python
import asyncio

@app.post("/api/reports")
async def generate_report(body: ReportRequest):
    # generate_pdf() is CPU-heavy and synchronous — run it off the event loop
    loop = asyncio.get_running_loop()
    pdf_bytes = await loop.run_in_executor(None, generate_pdf, body.template, body.data)
    return Response(content=pdf_bytes, media_type="application/pdf")
```

## Global Error Handling

### Custom exception hierarchy

```python
# core/exceptions.py
class AppException(Exception):
    """Base for all application-level exceptions."""
    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code


class NotFoundError(AppException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail=detail, status_code=404)


class ForbiddenError(AppException):
    def __init__(self, detail: str = "Access denied"):
        super().__init__(detail=detail, status_code=403)


class ServiceUnavailableError(AppException):
    def __init__(self, detail: str = "Service unavailable"):
        super().__init__(detail=detail, status_code=503)
```

### Exception handlers

```python
# main.py
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from core.exceptions import AppException

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error": exc.detail,
            "type": type(exc).__name__,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Flatten Pydantic errors into a readable list
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " → ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
        })
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "error": "Validation error",
            "details": errors,
        },
    )


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
    # Log the full traceback but return a sanitized error to the client
    import logging
    logger = logging.getLogger("app")
    logger.exception(f"Unhandled error on {request.method} {request.url.path}")

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": "Internal server error",
        },
    )
```

### Structured error convention

Every error response follows this shape:

```json
{"status": "error", "error": "Human-readable message", "type": "ExceptionClassName"}
```

This is the same convention used by the project's MCP servers (`{"status": "error", "error": str(e)}`).
Consistency across the API and MCP layer simplifies client error handling.

## Background Tasks

Use `BackgroundTasks` for fire-and-forget work that doesn't need to block the
HTTP response:

```python
from fastapi import BackgroundTasks

async def send_whatsapp_notification(jid: str, message: str):
    """Simulate sending a WhatsApp message (fire-and-forget)."""
    import asyncio
    await asyncio.sleep(0.5)  # I/O boundary
    print(f"[notify] Sent to {jid}: {message}")


@app.post("/api/documents", status_code=201)
async def create_document(
    body: DocumentCreate,
    db: Database,
    user: CurrentUser,
    background_tasks: BackgroundTasks,
):
    doc = await document_service.create(db, body)

    # Fire-and-forget: notification won't delay the 201 response
    background_tasks.add_task(
        send_whatsapp_notification,
        jid=user.whatsapp_jid,
        message=f"New document created: {doc.title}",
    )

    return DocumentResponse.model_validate(doc)
```

**When to use BackgroundTasks:**
- Sending push notifications, emails, Slack messages
- Writing to an audit log that's not part of the critical path
- Cache invalidation that can tolerate a few seconds of staleness

**When NOT to use BackgroundTasks:**
- Work that must complete before the response (use `await` directly)
- Long-running jobs (use a task queue: Celery, Redis Queue, or a scheduled DB table)
- Work where failure must be surfaced to the caller (BG tasks swallow exceptions)

## Middleware

### Request ID injection

```python
# middleware/request_id.py
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


# main.py
app.add_middleware(RequestIDMiddleware)
```

### Timing middleware

```python
# middleware/timing.py
import time
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Response-Time"] = f"{elapsed_ms:.1f}ms"
        return response
```

### CORS

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://app.example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
```

Never use `allow_origins=["*"]` in production. List allowed origins explicitly.
If you need wildcard support, use `allow_origin_regex` with a constrained pattern.

## JWT Auth Pattern

### Token creation and verification

```python
# core/security.py
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = {"sub": subject, "exp": expire, "iat": datetime.now(timezone.utc)}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
```

### OAuth2 dependency

```python
# dependencies/auth.py
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

async def get_current_user(
    request: Request,
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> User | None:
    if token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    ...
```

### Role-based access shortcut

```python
from typing import Annotated
from fastapi import Depends

def require_role(*roles: str):
    """Factory: create a dependency that checks for specific roles."""
    async def checker(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail=f"Requires role: {roles}")
        return user
    return Depends(checker)


AdminUser = Annotated[User, Depends(require_role("admin", "superadmin"))]

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str, admin: AdminUser):
    ...
```

## OpenAPI Config

```python
app = FastAPI(
    title="Digital FTE API",
    version="2.0.0",
    description="Multi-vertical AI Employee platform — HTTP API",
    docs_url="/docs",                    # Swagger UI
    redoc_url="/redoc",                  # ReDoc
    openapi_url="/openapi.json",
    servers=[
        {"url": "http://localhost:8080", "description": "Local dev"},
        {"url": "https://api.digitalfte.com", "description": "Production"},
    ],
)
```

### Hide internal routes

```python
@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok"}


@app.get("/internal/metrics", include_in_schema=False)
async def metrics():
    ...
```

Use `include_in_schema=False` for health checks, metrics, debug endpoints, and
internal admin routes — they don't belong in the public API contract.

### Response model by status code

```python
@app.post(
    "/api/documents",
    response_model=DocumentResponse,
    status_code=201,
    responses={
        201: {"description": "Created"},
        409: {"description": "Document already exists"},
        422: {"description": "Validation error"},
    },
)
```

## Environment & Settings

### pydantic-settings BaseSettings

```python
# core/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "Digital FTE API"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8080

    # Database
    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/db"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""

    # Auth
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    allowed_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

`lru_cache` ensures a single `Settings` instance — `.env` is parsed once at
first access, never re-read on every import.

Usage:

```python
settings = get_settings()

# In lifespan:
app.state.settings = settings

# In dependencies/routes:
settings = request.app.state.settings
```

## Common Pitfalls

1. **Blocking calls in async routes.** `time.sleep(2)` or `requests.get(url)`
   block the event loop — all concurrent requests stall. Use `await asyncio.sleep(2)`
   and `httpx.AsyncClient` instead. If you must call sync code, wrap it in
   `await loop.run_in_executor(None, sync_func)`.

2. **Missing `await` on async functions.** Calling an async function without
   `await` returns a coroutine object that never executes — no error, just silent
   failure. Type checkers catch this; if you're not using mypy/pyright, start.

3. **Wrong status codes.** `200` for every success (use `201` for creation),
   `400` for validation (use `422` per RFC 9110 for semantic validation failures).
   `401` for missing/expired auth, `403` for insufficient permissions — don't
   conflate them.

4. **Pydantic v1 → v2 migration traps.** `regex=` is now `pattern=`, `orm_mode`
   is now `from_attributes=True`, `@validator` is now `@field_validator`,
   `schema()` is now `model_json_schema()`, `.dict()` is now `.model_dump()`.

5. **Returning ORM objects without serialization.** FastAPI will try to JSON-encode
   the ORM object directly — SQLAlchemy objects aren't serializable. Always
   `return ResponseModel.model_validate(orm_obj)` or set `response_model=` on
   the route decorator.

6. **Using `@app.on_event`.** These decorators are deprecated and removed in
   FastAPI 0.112+. Use `lifespan` (asynccontextmanager) for all startup/shutdown
   logic.

7. **Creating a new client per request.** `httpx.AsyncClient`, `QdrantClient`,
   and `redis.asyncio.Redis` all manage connection pools. Create them once in
   lifespan, store on `app.state`, and inject via `Depends`. Per-request creation
   adds ~50ms overhead and leaks sockets under load.

8. **No timeout on external calls.** `httpx.get(url)` without `timeout=` hangs
   indefinitely if the downstream service is slow — the event loop stalls, and
   your health check starts failing. Always set an explicit timeout.

## Install

```bash
pip install fastapi>=0.111.0 pydantic>=2.0 pydantic-settings python-jose[cryptography] httpx python-dotenv uvicorn[standard]
```
