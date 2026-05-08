#!/usr/bin/env python
"""
Semantic search against a Qdrant collection.

Embeds the query via OpenAI text-embedding-3-small, runs query_points,
and pretty-prints results with scores, metadata, and snippet previews.

Usage:
    python search_vectors.py "How do I reconcile a bank statement?" --collection my_docs
    python search_vectors.py "SOX audit requirements" --domain finance --top 10
    python search_vectors.py "DSAR response timeline" --domain legal --threshold 0.6

Requirements:
    pip install qdrant-client>=1.9.0 openai python-dotenv
"""

import os
import sys
import argparse
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------

def get_qdrant_client():
    from qdrant_client import QdrantClient

    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)
    try:
        client.get_collections()
    except Exception as e:
        print(f"[FATAL] Cannot reach Qdrant at {QDRANT_URL}: {e}", file=sys.stderr)
        sys.exit(1)
    return client


def get_embed_client():
    from openai import OpenAI

    if not OPENAI_API_KEY:
        print("[FATAL] OPENAI_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)
    return OpenAI(api_key=OPENAI_API_KEY)


def embed_query(text: str, client) -> list[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=[text],
    )
    return response.data[0].embedding


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def search(
    query: str,
    collection: str,
    domain: str | None = None,
    top_k: int = 5,
    score_threshold: float | None = None,
):
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    qdrant = get_qdrant_client()
    embed_client = get_embed_client()

    print(f"Embedding query: \"{query}\"")
    embedding = embed_query(query, embed_client)

    query_filter = None
    if domain:
        query_filter = Filter(
            must=[FieldCondition(key="domain", match=MatchValue(value=domain))]
        )
        print(f"Filter: domain = {domain}")

    kwargs = {
        "collection_name": collection,
        "query": embedding,
        "limit": top_k,
        "with_payload": True,
    }
    if query_filter is not None:
        kwargs["query_filter"] = query_filter
    if score_threshold is not None:
        kwargs["score_threshold"] = score_threshold

    response = qdrant.query_points(**kwargs)
    hits = response.points

    print(f"\n{'─' * 64}")
    print(f"Results: {len(hits)} hits from collection '{collection}'\n")

    for rank, hit in enumerate(hits, 1):
        payload = hit.payload or {}
        title = payload.get("title", "Untitled")
        source = payload.get("source_file", "?")
        domain_val = payload.get("domain", "?")
        text = payload.get("chunk_text", "")

        # Truncate text for preview
        snippet = text[:200].replace("\n", " ") + ("…" if len(text) > 200 else "")

        print(f"  #{rank}  [{hit.score:.4f}]  {title}")
        print(f"       domain={domain_val}  source={source}")
        print(f"       {snippet}")
        print()

    print(f"{'─' * 64}")

    qdrant.close()
    embed_client.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Semantic search against a Qdrant collection"
    )
    parser.add_argument("query", help="Natural language search query")
    parser.add_argument("--collection", default="documents", help="Qdrant collection name")
    parser.add_argument(
        "--domain",
        choices=["finance", "hr", "legal", "shared"],
        help="Optional domain filter for payload isolation",
    )
    parser.add_argument("--top", type=int, default=5, help="Number of results (1–20)")
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Minimum cosine similarity score (0.0–1.0)",
    )
    args = parser.parse_args()

    top_k = max(1, min(20, args.top))

    search(
        query=args.query,
        collection=args.collection,
        domain=args.domain,
        top_k=top_k,
        score_threshold=args.threshold,
    )


if __name__ == "__main__":
    main()
