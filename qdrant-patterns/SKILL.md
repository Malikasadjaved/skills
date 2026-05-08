---
name: qdrant-patterns
description: >
  Use this skill when working with Qdrant vector database — creating
  collections, upserting embeddings, running semantic/hybrid search,
  managing payloads, and integrating Qdrant with FastAPI or async
  Python services. Covers both local Docker and Qdrant Cloud setups.
triggers:
  - qdrant
  - vector database
  - vector search
  - semantic search
  - embeddings
  - RAG
  - pgvector alternative
  - similarity search
version: 1.0.0
author: malikasadjaved
---

## Overview

Qdrant is an open-source vector database purpose-built for similarity
search. It stores high-dimensional vector embeddings alongside their
payload (metadata) and provides filtered search, hybrid search, and
sparse/dense multi-vector support out of the box.

**Use Qdrant when** you need:
- Lightning-fast ANN (approximate nearest neighbour) search at scale
- Payload filtering that doesn't degrade query performance
- Multi-tenancy with per-tenant collection or payload-based isolation
- Named vectors for multi-model embeddings in a single point
- A Rust-native engine with gRPC + REST APIs and a first-class async Python client

**Use pgvector when** you need:
- OLTP + vector in one query (no eventual consistency between DBs)
- Small datasets (< 100K vectors) where operational simplicity beats speed
- A single Postgres instance already running and cost is the main constraint

This project uses Qdrant via Docker at `http://localhost:6333` with the
REST API for upsert, query, and collection management. The `shared/rag/pipeline.py`
module is the canonical reference implementation — this skill captures the
patterns from that module and extends them for general use.

## Setup

### Docker (local dev)

```bash
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v "$(pwd)/data/qdrant:/qdrant/storage" \
  qdrant/qdrant:latest
```

Or via docker-compose (the project standard):

```yaml
qdrant:
  image: qdrant/qdrant:latest
  container_name: digitalfte-qdrant
  restart: unless-stopped
  ports:
    - "6333:6333"
    - "6334:6334"
  volumes:
    - ./data/qdrant:/qdrant/storage
  environment:
    QDRANT__SERVICE__GRPC_PORT: 6334
```

Port 6333 = REST API, port 6334 = gRPC (optional). The project uses REST
exclusively via `QdrantClient(url=...)`.

Health check:

```bash
curl -f http://localhost:6333/readyz
```

### Qdrant Cloud

Set these env vars:

```bash
QDRANT_URL=https://xyz-example.eu-central.aws.cloud.qdrant.io:6333
QDRANT_API_KEY=your-api-key
```

The client init pattern detects cloud vs local automatically (see below).

## Python Client Init

### Local Docker (no auth)

```python
import os
from qdrant_client import QdrantClient

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

client = QdrantClient(url=QDRANT_URL)
```

### Qdrant Cloud (API key auth)

```python
import os
from qdrant_client import QdrantClient

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
```

### Unified init (works for both)

```python
import os
from qdrant_client import QdrantClient

def get_qdrant_client() -> QdrantClient:
    url = os.getenv("QDRANT_URL", "http://localhost:6333")
    api_key = os.getenv("QDRANT_API_KEY")
    return QdrantClient(url=url, api_key=api_key or None)
```

### Lazy singleton (project pattern)

```python
_qdrant_client = None

def get_qdrant_client() -> QdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        url = os.getenv("QDRANT_URL", "http://localhost:6333")
        api_key = os.getenv("QDRANT_API_KEY")
        _qdrant_client = QdrantClient(url=url, api_key=api_key or None)
    return _qdrant_client
```

Reuse the client across requests — it manages connection pools internally.

## Creating a Collection

### Standard text-embedding collection (COSINE)

```python
from qdrant_client.models import VectorParams, Distance

COLLECTION_NAME = "my_docs"
VECTOR_DIM = 1536  # text-embedding-3-small

client.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(
        size=VECTOR_DIM,
        distance=Distance.COSINE,
    ),
)
```

### Idempotent create (project pattern)

```python
def ensure_collection(name: str, dim: int) -> bool:
    existing = {c.name for c in client.get_collections().collections}
    if name not in existing:
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
        return True
    return False
```

### Named vectors (multi-model on one point)

```python
from qdrant_client.models import VectorParams, Distance, NamedVector

client.create_collection(
    collection_name="multi_docs",
    vectors_config={
        "dense": VectorParams(size=1536, distance=Distance.COSINE),
        "sparse": VectorParams(size=768, distance=Distance.DOT),
        "late-interaction": VectorParams(
            size=1024,
            distance=Distance.COSINE,
            hnsw_config=HnswConfigDiff(m=16, ef_construct=200),
        ),
    },
)
```

### HNSW tuning

```python
from qdrant_client.models import HnswConfigDiff

client.create_collection(
    collection_name="large_docs",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    hnsw_config=HnswConfigDiff(
        m=16,               # edges per node (default 16, range 4-64)
        ef_construct=200,   # build-time search depth (default 100, higher = more accurate but slower build)
        full_scan_threshold=10000,  # skip HNSW for small result sets
    ),
    optimizers_config=OptimizersConfigDiff(
        default_segment_number=2,  # balance index freshness vs disk
    ),
)
```

- **m**: Higher = more recall, more RAM. 16 is good for 1M+ points.
- **ef_construct**: Higher = better index quality, slower upserts. 100-200 is typical.
- **full_scan_threshold**: Below this many points, Qdrant does exact search (no HNSW). Keep low for production.

## Upserting Points

### Single point

```python
from qdrant_client.models import PointStruct

point = PointStruct(
    id=1,
    vector=[0.1, 0.2, ...],  # 1536-dim list[float]
    payload={"title": "Document", "domain": "finance", "chunk_index": 0},
)
client.upsert(collection_name="my_docs", points=[point])
```

### Batch upsert (project pattern — 100 points per batch)

```python
from qdrant_client.models import PointStruct

points: list[PointStruct] = []

for doc in documents:
    embedding = embed(doc["text"])
    points.append(PointStruct(
        id=doc["id"],
        vector=embedding,
        payload={
            "title": doc["title"],
            "domain": doc["domain"],
            "doc_type": doc.get("type", "unknown"),
            "source_file": doc["file"],
            "chunk_index": doc["chunk"],
            "chunk_text": doc["text"],
        },
    ))

batch_size = 100
for i in range(0, len(points), batch_size):
    batch = points[i : i + batch_size]
    client.upsert(collection_name="my_docs", points=batch)
```

### Payload schema conventions

Keep payloads flat — no nested dicts deeper than 1 level (payload index
requires string, integer, or keyword values at the top level):

```python
# Good: flat, indexable
{"tenant_id": "acme-corp", "type": "invoice", "year": 2025}

# Bad: nested beyond index reach
{"tenant": {"id": "acme-corp"}, "meta": {"type": "invoice"}}
```

### ID strategies

**UUID5 deterministic (project standard):**

```python
import uuid

point_id = int(
    uuid.uuid5(uuid.NAMESPACE_DNS, f"{domain}:{file_name}:{chunk_idx}").int
    % (2**63)
)
```

Advantage: re-running the same ingest produces the same IDs — upsert becomes
idempotent (no duplicates, no manual dedup).

**UUID4 random:**

```python
import uuid

point_id = str(uuid.uuid4())
```

Advantage: no collision risk, no max-int wrapping. Use when you never re-ingest
the same source.

**Integer auto-increment:**

```python
# Only safe when you maintain an external counter
point_id = next_counter()
```

Qdrant requires unsigned 64-bit integers or UUID strings. The project uses
64-bit integers from UUID5 hashing to avoid string IDs (slightly faster
serialization).

## Semantic Search

### Basic query

```python
response = client.query_points(
    collection_name="my_docs",
    query=query_embedding,  # list[float] — same dimension as collection
    limit=10,
    with_payload=True,
)

for hit in response.points:
    print(f"Score: {hit.score:.4f} | {hit.payload['title']}")
```

`response.points` is a list of `ScoredPoint` objects — each has `.id`, `.score`,
`.vector` (if `with_vector=True`), and `.payload` (if `with_payload=True`).

### With score threshold

```python
response = client.query_points(
    collection_name="my_docs",
    query=query_embedding,
    limit=10,
    score_threshold=0.7,  # only return points with cosine >= 0.7
    with_payload=True,
)
```

### With vector (for re-ranking)

```python
response = client.query_points(
    collection_name="my_docs",
    query=query_embedding,
    limit=50,
    with_payload=True,
    with_vectors=True,  # .vector populated on each ScoredPoint
)
```

### Full project retrieval pattern

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue

def search_docs(query_embedding: list[float], domain: str | None, top_k: int = 5):
    query_filter = None
    if domain:
        query_filter = Filter(
            must=[FieldCondition(key="domain", match=MatchValue(value=domain))]
        )

    response = client.query_points(
        collection_name="my_docs",
        query=query_embedding,
        query_filter=query_filter,
        limit=top_k,
        with_payload=True,
    )

    return [
        {
            "title": hit.payload["title"],
            "text": hit.payload["chunk_text"],
            "score": round(hit.score, 4),
            "domain": hit.payload.get("domain"),
        }
        for hit in response.points
    ]
```

## Filtered Search

### Tenant isolation (multi-tenant SaaS)

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Only search points belonging to tenant "acme-corp"
tenant_filter = Filter(
    must=[
        FieldCondition(key="tenant_id", match=MatchValue(value="acme-corp")),
    ]
)

response = client.query_points(
    collection_name="my_docs",
    query=query_embedding,
    query_filter=tenant_filter,
    limit=10,
    with_payload=True,
)
```

### Compound filters (AND + OR)

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny, Range

complex_filter = Filter(
    must=[
        FieldCondition(key="tenant_id", match=MatchValue(value="acme-corp")),
        FieldCondition(key="doc_type", match=MatchAny(any=["invoice", "receipt"])),
        FieldCondition(key="year", range=Range(gte=2024)),
    ],
    must_not=[
        FieldCondition(key="status", match=MatchValue(value="archived")),
    ],
)

response = client.query_points(
    collection_name="my_docs",
    query=query_embedding,
    query_filter=complex_filter,
    limit=10,
    with_payload=True,
)
```

### Filter without vector (payload-only query)

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Scroll through all points matching a filter — no vector involved
records, next_offset = client.scroll(
    collection_name="my_docs",
    scroll_filter=Filter(
        must=[FieldCondition(key="tenant_id", match=MatchValue(value="acme-corp"))],
    ),
    limit=50,
    with_payload=True,
)
```

Use `scroll` for admin operations, exports, and data migrations. Do NOT use
`scroll` in hot request paths — it's linear, not ANN.

### Count with filter

```python
result = client.count(
    collection_name="my_docs",
    count_filter=Filter(
        must=[FieldCondition(key="domain", match=MatchValue(value="finance"))],
    ),
)
print(f"Finance docs: {result.count}")
```

## Payload Indexing

Without a payload index, filtered search does a full scan of all payloads
matched by the HNSW pre-filter — fast for small collections, slow past ~10K points.

```python
# Create an index on the filter field
client.create_payload_index(
    collection_name="my_docs",
    field_name="tenant_id",
    field_schema="keyword",  # or "integer" / "float" / "geo" / "text"
)

# Create index for type-based filters
client.create_payload_index(
    collection_name="my_docs",
    field_name="doc_type",
    field_schema="keyword",
)

# Create index for numeric range filters
client.create_payload_index(
    collection_name="my_docs",
    field_name="year",
    field_schema="integer",
)
```

**When to index:**
- Index any field you filter on in production query paths
- Index `tenant_id` in multi-tenant apps (it's on every query)
- Don't index `chunk_text` (full text) — it's not a filter field
- Don't index fields only used in scroll/admin paths

**When the index is worth it:**
- Cardinally < 10,000 distinct values → keyword index is excellent
- Cardinally > 1M distinct values → index overhead may outweigh benefit; benchmark

## FastAPI Integration Pattern

### Async lifespan with dependency injection

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
import os

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "documents")

_qdrant: QdrantClient | None = None


def get_qdrant() -> QdrantClient:
    """FastAPI dependency — inject QdrantClient into route handlers."""
    if _qdrant is None:
        raise RuntimeError("Qdrant client not initialised — app lifespan failed?")
    return _qdrant


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: connect Qdrant + ensure collection. Shutdown: close client."""
    global _qdrant

    _qdrant = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY or None,
    )

    existing = {c.name for c in _qdrant.get_collections().collections}
    if COLLECTION_NAME not in existing:
        _qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )
        print(f"[qdrant] Created collection '{COLLECTION_NAME}'")

    print(f"[qdrant] Connected — {QDRANT_URL}")
    yield

    _qdrant.close()
    print("[qdrant] Closed")


app = FastAPI(lifespan=lifespan)


@app.get("/search")
async def search(q: str, client: QdrantClient = Depends(get_qdrant)):
    embedding = await embed_query(q)
    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=embedding,
        limit=5,
        with_payload=True,
    )
    return {"results": [h.payload for h in response.points]}
```

Do NOT create a new `QdrantClient` per request — the client manages a connection
pool and creating/destroying it per request adds latency and TCP overhead.

## Error Handling

### Collection not found guard

```python
from qdrant_client.http.exceptions import UnexpectedResponse

def ensure_collection(name: str, dim: int):
    try:
        client.get_collection(collection_name=name)
    except UnexpectedResponse as e:
        if e.status_code == 404:
            client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )
            return
        raise
```

### Connection retry with backoff

```python
import time

def get_client_with_retry(max_retries: int = 3) -> QdrantClient:
    url = os.getenv("QDRANT_URL", "http://localhost:6333")
    api_key = os.getenv("QDRANT_API_KEY")

    for attempt in range(max_retries):
        try:
            client = QdrantClient(url=url, api_key=api_key or None)
            client.get_collections()  # probe
            return client
        except Exception as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"Qdrant unreachable after {max_retries} attempts: {e}")
            wait = 2 ** attempt
            print(f"[qdrant] Connection failed (attempt {attempt + 1}), retrying in {wait}s...")
            time.sleep(wait)
```

### Tool-call try/except (project pattern)

```python
def search(query: str, domain: str) -> dict:
    try:
        results = _do_search(query, domain)
        return {"status": "success", "results": results}
    except UnexpectedResponse as e:
        return {"status": "error", "error": f"Qdrant error ({e.status_code}): {e}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

Always return `{"status": "error", ...}` dicts from MCP tools and API handlers
— never let Qdrant exceptions propagate to callers.

## Environment Variables Convention

```bash
# Required
QDRANT_URL=http://localhost:6333          # REST API endpoint

# Optional
QDRANT_API_KEY=                           # Cloud API key (omit for local Docker)
COLLECTION_NAME=digital_fte_documents     # Default collection name
EMBEDDING_DIM=1536                        # Vector dimension (text-embedding-3-small = 1536)
```

Load them once at module level:

```python
import os
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "documents")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))
```

## Common Pitfalls

1. **Forgetting payload index on filter fields.** Filtering by `tenant_id` on
   100K+ points without an index forces a full payload scan. Always index
   tenant/shard keys and any field used in `query_filter`.

2. **Wrong vector dimension mismatch.** If `VectorParams(size=768)` but your
   embedding model produces 1536-dim vectors, Qdrant rejects the upsert with
   a dimension error. Keep `EMBEDDING_DIM` in sync with the collection config.

3. **Not using batch upsert.** Upserting 1,000 points one at a time makes 1,000
   HTTP round-trips (~3-10 seconds). Batch them in groups of 100–200 for
   near-linear throughput (< 500ms for 1,000 points).

4. **Creating a new client per request.** `QdrantClient` owns a connection pool.
   Create it once (lifespan/singleton) and reuse. Per-request creation leaks
   sockets and adds ~50ms overhead per call.

5. **Using `client.search()` (removed in qdrant-client 1.17+).** The old API
   is gone. Always use `client.query_points()` — the response object changed
   from returning a flat list to `QueryResponse` with `.points`.

6. **UUID string IDs vs integer IDs.** Integer IDs are slightly faster but
   collision-prone without deterministic hashing. UUID5 (namespace + name) is
   the project standard — idempotent re-ingestion with no collisions.

7. **Cosine distance range assumption.** Cosine similarity runs from -1 to 1,
   but Qdrant represents it as distance (0 to 2). A `score_threshold` of 0.7
   in `query_points` matches cosine >= 0.7 — the client handles the conversion
   internally.

8. **Logging to stdout in MCP servers.** MCP communicates over stdin/stdout.
   Any `print()` or `logging.StreamHandler()` on stdout corrupts the JSON-RPC
   stream. Always route logs to stderr or files.

## Install

```bash
pip install qdrant-client>=1.9.0
```
