# Qdrant Cheatsheet

Quick API reference for `qdrant-client` (>= 1.9.0, REST transport).

---

## Client

```python
from qdrant_client import QdrantClient

# Local Docker
client = QdrantClient(url="http://localhost:6333")

# Qdrant Cloud
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

client.close()  # always close when done
```

## Collections

```python
from qdrant_client.models import VectorParams, Distance, HnswConfigDiff

# List
[info.name for info in client.get_collections().collections]

# Get one
client.get_collection(collection_name="docs")

# Create
client.create_collection(
    collection_name="docs",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    hnsw_config=HnswConfigDiff(m=16, ef_construct=200),
)

# Delete
client.delete_collection(collection_name="docs")
```

## Upsert

```python
from qdrant_client.models import PointStruct

# Single
client.upsert(collection_name="docs", points=[
    PointStruct(id=1, vector=[0.1, ...], payload={"key": "val"}),
])

# Batch (100–200 per call)
for i in range(0, len(points), 100):
    client.upsert(collection_name="docs", points=points[i:i+100])
```

## Search

```python
# Semantic (vector)
response = client.query_points(
    collection_name="docs",
    query=query_vector,          # list[float]
    limit=10,
    score_threshold=0.7,         # optional
    with_payload=True,           # include metadata
    with_vectors=False,          # set True to get vectors back
)
for hit in response.points:
    print(hit.id, hit.score, hit.payload)

# With filter
from qdrant_client.models import Filter, FieldCondition, MatchValue

response = client.query_points(
    collection_name="docs",
    query=query_vector,
    query_filter=Filter(
        must=[FieldCondition(key="tenant", match=MatchValue(value="acme"))],
    ),
    limit=10,
    with_payload=True,
)
```

## Filter Operators

```python
from qdrant_client.models import (
    Filter, FieldCondition, MatchValue, MatchAny, MatchExcept, Range, GeoRadius,
)

# Exact match
FieldCondition(key="status", match=MatchValue(value="active"))

# Any of
FieldCondition(key="type", match=MatchAny(any=["invoice", "bill"]))

# Not in
FieldCondition(key="type", match=MatchExcept(**{"except": ["archived"]}))

# Range
FieldCondition(key="year", range=Range(gte=2024, lt=2026))

# Compound
Filter(
    must=[...],       # AND
    should=[...],     # OR (use min_should=1)
    must_not=[...],   # NOT
)

# OR (at least 1 should match)
Filter(
    should=[
        FieldCondition(key="domain", match=MatchValue(value="finance")),
        FieldCondition(key="domain", match=MatchValue(value="hr")),
    ],
    min_should=1,
)
```

## Payload Index

```python
# Create
client.create_payload_index(
    collection_name="docs",
    field_name="tenant_id",
    field_schema="keyword",    # keyword | integer | float | geo | text
)

# List
client.list_payload_indexes(collection_name="docs")
```

## Scroll (payload-only fetch, no vector)

```python
records, next_offset = client.scroll(
    collection_name="docs",
    scroll_filter=Filter(must=[...]),
    limit=100,
    with_payload=True,
)
```

## Count

```python
# Full collection
count = client.count(collection_name="docs").count

# With filter
count = client.count(
    collection_name="docs",
    count_filter=Filter(must=[FieldCondition(key="domain", match=MatchValue(value="finance"))]),
).count
```

## Delete

```python
# By IDs
client.delete(collection_name="docs", points_selector=[1, 2, 3])

# By filter
client.delete(
    collection_name="docs",
    points_selector=Filter(must=[FieldCondition(key="status", match=MatchValue(value="archived"))]),
)
```

## Points

```python
# Get by ID
client.retrieve(collection_name="docs", ids=[1, 2], with_payload=True, with_vectors=True)

# Count
client.count(collection_name="docs")
```

## Distance Reference

| Distance | Range | Good for |
|----------|-------|----------|
| `Distance.COSINE` | 0–2 (0=identical) | Text embeddings (most common) |
| `Distance.DOT` | -∞ to ∞ (higher=more similar) | Learned embeddings, ColBERT |
| `Distance.EUCLID` | 0–∞ (0=identical) | Image embeddings, geometry |

## Collection Info at a Glance

```python
info = client.get_collection(collection_name="docs")
info.points_count          # total points
info.config.params.vectors.size     # vector dimension
info.config.params.vectors.distance  # Distance enum
info.status                # "green" / "yellow" / "red"
```

## Install

```bash
pip install qdrant-client>=1.9.0

# Optional extras
pip install qdrant-client[fastembed]   # on-device embeddings, no API key
```
