#!/usr/bin/env python
"""
Reusable FastAPI dependency injection patterns.

Covers:
    - Async DB session with yield (cleanup on response)
    - JWT auth dependency with OAuth2PasswordBearer
    - Role-based access guard factory
    - Qdrant client from app.state
    - httpx.AsyncClient for outbound HTTP
    - Redis client from app.state

All dependencies read shared state from request.app.state, which is
populated during lifespan startup — no globals, no module-level singletons.

Usage:
    from dependencies import Database, CurrentUser, AdminUser, Qdrant
"""

from __future__ import annotations

from typing import Annotated, AsyncGenerator

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

# ═══════════════════════════════════════════════════════════════════
# Type stubs (replace with your actual models)
# ═══════════════════════════════════════════════════════════════════


class User:
    """Placeholder — replace with your actual User model / dataclass."""
    def __init__(self, id: str, email: str, role: str = "user"):
        self.id = id
        self.email = email
        self.role = role


# ═══════════════════════════════════════════════════════════════════
# Database dependency (async session with yield)
# ═══════════════════════════════════════════════════════════════════

# Replace AsyncSession with your ORM's session type.
# Example with SQLAlchemy:
#   from sqlalchemy.ext.asyncio import AsyncSession

AsyncSession = object  # placeholder — replace with actual type


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Yield an async DB session. Commits on success, rollback on error."""
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    async with pool.session() as session:  # type: ignore[attr-defined]
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


Database = Annotated[AsyncSession, Depends(get_db)]


# ═══════════════════════════════════════════════════════════════════
# OAuth2 scheme
# ═══════════════════════════════════════════════════════════════════

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    auto_error=False,
)


# ═══════════════════════════════════════════════════════════════════
# JWT auth dependency
# ═══════════════════════════════════════════════════════════════════


def decode_token(token: str, secret: str, algorithm: str = "HS256") -> dict:
    """Decode and validate a JWT. Raises JWTError on failure."""
    return jwt.decode(token, secret, algorithms=[algorithm])


async def get_current_user(
    request: Request,
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> User:
    """Extract and validate the current user from the Authorization header."""
    if token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    settings = request.app.state.settings
    try:
        payload = decode_token(
            token,
            settings.jwt_secret,
            settings.jwt_algorithm if hasattr(settings, "jwt_algorithm") else "HS256",
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # Replace this with an actual DB lookup:
    #   user = await fetch_user_by_id(request.app.state.db_pool, user_id)
    user = User(id=user_id, email=f"{user_id}@example.com", role=payload.get("role", "user"))

    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def get_optional_user(
    request: Request,
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> User | None:
    """Like get_current_user, but returns None instead of 401 for unauthenticated requests."""
    if token is None:
        return None
    try:
        settings = request.app.state.settings
        payload = decode_token(token, settings.jwt_secret)
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return User(id=user_id, email=f"{user_id}@example.com", role=payload.get("role", "user"))
    except JWTError:
        return None


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]


# ═══════════════════════════════════════════════════════════════════
# Role-based access guard (factory pattern)
# ═══════════════════════════════════════════════════════════════════


def require_role(*roles: str):
    """Factory: return a dependency that enforces the caller has one of `roles`."""

    async def role_checker(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied — requires role: {' or '.join(roles)}",
            )
        return user

    return Depends(role_checker)


AdminUser = Annotated[User, Depends(require_role("admin", "superadmin"))]
EditorUser = Annotated[User, Depends(require_role("admin", "editor"))]


# ═══════════════════════════════════════════════════════════════════
# Qdrant client dependency
# ═══════════════════════════════════════════════════════════════════

# Replace with: from qdrant_client import QdrantClient
QdrantClient = object  # placeholder


def get_qdrant(request: Request) -> QdrantClient:
    """Return the QdrantClient stored on app.state (created in lifespan)."""
    client = getattr(request.app.state, "qdrant", None)
    if client is None:
        raise HTTPException(status_code=503, detail="Qdrant not available")
    return client


Qdrant = Annotated[QdrantClient, Depends(get_qdrant)]


# ═══════════════════════════════════════════════════════════════════
# Redis client dependency
# ═══════════════════════════════════════════════════════════════════

# Replace with: from redis.asyncio import Redis
Redis = object  # placeholder


def get_redis(request: Request) -> Redis:
    """Return the Redis client stored on app.state (created in lifespan)."""
    client = getattr(request.app.state, "redis", None)
    if client is None:
        raise HTTPException(status_code=503, detail="Redis not available")
    return client


RedisClient = Annotated[Redis, Depends(get_redis)]


# ═══════════════════════════════════════════════════════════════════
# httpx async client dependency
# ═══════════════════════════════════════════════════════════════════

import httpx  # noqa: E402


def get_http_client(request: Request) -> httpx.AsyncClient:
    """Return a shared httpx.AsyncClient from app.state (created in lifespan)."""
    client = getattr(request.app.state, "http_client", None)
    if client is None:
        raise HTTPException(status_code=503, detail="HTTP client not available")
    return client


HttpClient = Annotated[httpx.AsyncClient, Depends(get_http_client)]


# ═══════════════════════════════════════════════════════════════════
# Example: lifespan section that wires up these dependencies
# ═══════════════════════════════════════════════════════════════════

"""
Add this to your app's lifespan:

@asynccontextmanager
async def lifespan(app: FastAPI):
    import httpx
    from qdrant_client import QdrantClient
    from redis.asyncio import Redis

    settings = get_settings()
    app.state.settings = settings

    # Qdrant
    try:
        app.state.qdrant = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
        )
    except Exception:
        app.state.qdrant = None  # optional — guarded in dependency

    # Redis
    try:
        app.state.redis = Redis.from_url(settings.redis_url)
    except Exception:
        app.state.redis = None

    # httpx (shared connection pool)
    app.state.http_client = httpx.AsyncClient(timeout=30.0)

    yield

    # Cleanup
    if app.state.qdrant:
        app.state.qdrant.close()
    if app.state.redis:
        await app.state.redis.close()
    await app.state.http_client.aclose()
"""
