#!/usr/bin/env python
"""
Create / configure a Qdrant collection.

Usage:
    python setup_collection.py [--collection my_docs] [--dim 1536] [--drop]

Drops and recreates when --drop is passed (useful for schema changes).
Otherwise creates idempotently — no-op if the collection already exists.

Requirements:
    pip install qdrant-client>=1.9.0 python-dotenv
"""

import os
import sys
import argparse
from dotenv import load_dotenv

load_dotenv()

from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    HnswConfigDiff,
    OptimizersConfigDiff,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")


def get_client() -> QdrantClient:
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)
    try:
        client.get_collections()
    except Exception as e:
        print(f"[FATAL] Cannot reach Qdrant at {QDRANT_URL}: {e}", file=sys.stderr)
        sys.exit(1)
    return client


def collection_exists(client: QdrantClient, name: str) -> bool:
    return name in {c.name for c in client.get_collections().collections}


def create_collection(
    client: QdrantClient,
    name: str,
    dim: int,
    distance: Distance = Distance.COSINE,
    on_disk: bool = True,
):
    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(
            size=dim,
            distance=distance,
            on_disk=on_disk,
        ),
        hnsw_config=HnswConfigDiff(
            m=16,
            ef_construct=200,
        ),
        optimizers_config=OptimizersConfigDiff(
            default_segment_number=2,
        ),
    )
    print(f"[OK] Created collection '{name}' ({dim}-dim {distance.name}, on_disk={on_disk})")


def create_payload_indexes(client: QdrantClient, name: str, fields: list[str]):
    for field in fields:
        client.create_payload_index(
            collection_name=name,
            field_name=field,
            field_schema="keyword",
        )
        print(f"[OK] Payload index created: '{name}'.{field}")


def main():
    parser = argparse.ArgumentParser(description="Create / configure a Qdrant collection")
    parser.add_argument("--collection", default="documents", help="Collection name")
    parser.add_argument("--dim", type=int, default=1536, help="Vector dimension")
    parser.add_argument("--drop", action="store_true", help="Drop and recreate")
    parser.add_argument(
        "--index-fields",
        nargs="*",
        default=["domain", "doc_type"],
        help="Payload fields to index (keyword)",
    )
    args = parser.parse_args()

    client = get_client()

    if args.drop:
        if collection_exists(client, args.collection):
            client.delete_collection(collection_name=args.collection)
            print(f"[OK] Dropped existing collection '{args.collection}'")
        else:
            print(f"[INFO] Collection '{args.collection}' does not exist — nothing to drop")

    if collection_exists(client, args.collection):
        print(f"[INFO] Collection '{args.collection}' already exists — nothing to create")
    else:
        create_collection(client, args.collection, args.dim)

    if args.index_fields:
        create_payload_indexes(client, args.collection, args.index_fields)

    # Show summary
    info = client.get_collection(collection_name=args.collection)
    cfg = info.config.params.vectors
    indexed = {f.field_name for f in info.config.params.sparse_vectors or []} if False else {}
    print(
        f"\n[SUMMARY] {args.collection}: {info.points_count} points, "
        f"{cfg.size}-dim {info.config.params.vectors.distance.name}"
    )

    client.close()


if __name__ == "__main__":
    main()
