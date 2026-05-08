# FastAPI Cheatsheet

Quick patterns reference for FastAPI ≥ 0.111.0 with Pydantic v2.

---

## App Factory

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: init DB pool, clients, etc.
    app.state.db = await create_pool()
    yield
    # shutdown: close connections
    await app.state.db.close()

app = FastAPI(
    title="My API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
)
```

## Pydantic v2 Models

```python
from pydantic import BaseModel, Field, computed_field, field_validator

class ItemCreate(BaseModel):
    model_config = {"str_strip_whitespace": True, "extra": "forbid"}
    name: str = Field(min_length=1, max_length=200)
    tags: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be blank")
        return v.strip()

class ItemResponse(BaseModel):
    model_config = {"from_attributes": True}  # was orm_mode in v1
    id: str
    name: str

    @computed_field
    def display_name(self) -> str:
        return self.name.upper()

# v1 → v2 migration:
#   orm_mode=True        → from_attributes=True
#   regex=r"..."         → pattern=r"..."
#   @validator           → @field_validator
#   .dict()              → .model_dump()
#   .json()              → .model_dump_json()
#   .schema()            → .model_json_schema()
```

## Routes & Routers

```python
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/items", tags=["Items"])

@router.get("", response_model=list[ItemResponse])
async def list_items(domain: str | None = None, limit: int = 50):
    ...

@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(item_id: str):
    ...

@router.post("", response_model=ItemResponse, status_code=201)
async def create_item(body: ItemCreate):
    ...

@router.delete("/{item_id}", status_code=204)
async def delete_item(item_id: str):
    ...

# Include in main app
app.include_router(router)
```

## Dependency Injection

```python
from typing import Annotated
from fastapi import Depends, Request

# Yield dependency (cleanup after response)
async def get_db(request: Request) -> AsyncGenerator[DB, None]:
    async with request.app.state.db_pool.session() as s:
        yield s

# Auth dependency
async def get_current_user(
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    payload = jwt.decode(token, request.app.state.settings.jwt_secret)
    return await fetch_user(payload["sub"])

# Shortcut types (put in dependencies/__init__.py)
Database = Annotated[DB, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]

# Route usage
@router.get("/me")
async def me(db: Database, user: CurrentUser):
    return user
```

## Status Codes

```python
from fastapi import status

@app.post("/items", status_code=status.HTTP_201_CREATED)
@app.delete("/items/{id}", status_code=status.HTTP_204_NO_CONTENT)
raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
```

## Background Tasks

```python
from fastapi import BackgroundTasks

@router.post("/items")
async def create(body: ItemCreate, bg: BackgroundTasks):
    item = await save(body)
    bg.add_task(send_notification, item.id)  # fire-and-forget
    return item
```

## Query Parameters

```python
@router.get("/search")
async def search(
    q: str,                              # required
    page: int = 1,                       # default
    limit: int | None = None,            # optional
    domain: str = Query(default="all", min_length=1),
    tags: list[str] = Query(default_factory=list),
):
    ...
```

## CORS

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],  # never ["*"] in prod
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

## Error Responses

```python
# Always return this shape:
{"status": "error", "error": "<message>", "type": "<ExceptionName>"}

# Raise in routes/services:
raise HTTPException(status_code=404, detail="Not found")
raise AppException("Bad request", status_code=400)

# Register handlers:
@app.exception_handler(AppException)
async def handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "error": exc.detail, "type": type(exc).__name__},
    )
```

## Async HTTP Calls (httpx)

```python
import httpx

@router.post("/proxy")
async def proxy(body: dict, request: Request):
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post("https://api.example.com", json=body)
        resp.raise_for_status()
        return resp.json()

# Better: reuse client from app.state (created in lifespan)
@app.post("/proxy")
async def proxy(body: dict, http: Annotated[httpx.AsyncClient, Depends(get_http)]):
    resp = await http.post("https://api.example.com", json=body)
    resp.raise_for_status()
    return resp.json()
```

## JWT Auth

```python
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Encode
token = jwt.encode(
    {"sub": user_id, "exp": expire, "iat": now},
    SECRET,
    algorithm="HS256",
)

# Decode in dependency
try:
    payload = jwt.decode(token, SECRET, algorithms=["HS256"])
except JWTError:
    raise HTTPException(status_code=401)
```

## OpenAPI Tweaks

```python
# Hide from docs
@app.get("/health", include_in_schema=False)

# Tag groups
router = APIRouter(tags=["v1 — Documents"])

# Response descriptions
@router.post("/items", responses={
    201: {"description": "Created"},
    409: {"description": "Already exists"},
})

# Deprecation
@router.get("/old-endpoint", deprecated=True)
```

## Settings (pydantic-settings)

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "My API"
    port: int = 8080

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

## Install

```bash
pip install "fastapi>=0.111.0" "pydantic>=2.0" pydantic-settings uvicorn[standard] python-jose[cryptography] httpx python-dotenv
```
