#!/usr/bin/env python
"""
Embed documents with OpenAI text-embedding-3-small and upsert into Qdrant.

Reads .md and .txt files from a directory, chunks them, embeds each chunk,
and upserts into the target Qdrant collection with domain-tagged payloads.

Usage:
    python upsert_vectors.py --source ./docs --collection my_docs --domain finance
    python upsert_vectors.py --source ./docs --collection my_docs --domain hr --batch-size 200

Requirements:
    pip install qdrant-client>=1.9.0 openai python-dotenv
"""

import os
import sys
import uuid
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

CHUNK_SIZE = 512   # tokens (approximate)
CHUNK_OVERLAP = 64  # tokens (approximate)

VALID_DOMAINS = {"finance", "hr", "legal", "shared"}


# ---------------------------------------------------------------------------
# Qdrant client
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


def ensure_collection(client, name: str, dim: int):
    from qdrant_client.models import VectorParams, Distance

    existing = {c.name for c in client.get_collections().collections}
    if name not in existing:
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
        print(f"[OK] Created collection '{name}' ({dim}-dim COSINE)")
    else:
        info = client.get_collection(collection_name=name)
        cfg_dim = info.config.params.vectors.size
        if cfg_dim != dim:
            print(
                f"[FATAL] Collection '{name}' has dimension {cfg_dim}, but embeddings are {dim}-dim. "
                f"Drop the collection (--drop) and re-run.",
                file=sys.stderr,
            )
            sys.exit(1)


# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------

def get_embed_client():
    from openai import OpenAI

    if not OPENAI_API_KEY:
        print("[FATAL] OPENAI_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)
    return OpenAI(api_key=OPENAI_API_KEY)


def embed_texts(texts: list[str], client) -> list[list[float]]:
    """Batch-embed a list of strings via text-embedding-3-small."""
    if not texts:
        return []

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )
    return [d.embedding for d in response.data]


# ---------------------------------------------------------------------------
# Chunking (pure-Python: no external dep beyond stdlib)
# ---------------------------------------------------------------------------

def chunk_text(text: str, chunk_size: int = 512, chunk_overlap: int = 64) -> list[str]:
    """Split text into overlapping word-based chunks."""
    if not text or not text.strip():
        return []

    words = text.split()
    if not words:
        return []

    # Approximate word count from token target (4 chars / word ~= 0.75 token/word)
    word_chunk = max(30, int(chunk_size * 0.75))
    word_overlap = max(10, int(chunk_overlap * 0.75))
    step = max(1, word_chunk - word_overlap)

    chunks = []
    for start in range(0, len(words), step):
        chunk = " ".join(words[start : start + word_chunk])
        if chunk.strip():
            chunks.append(chunk)
        if start + word_chunk >= len(words):
            break

    return chunks if chunks else [text]


# ---------------------------------------------------------------------------
# Upsert
# ---------------------------------------------------------------------------

def upsert_documents(
    source_dir: Path,
    collection: str,
    domain: str,
    batch_size: int = 100,
):
    from qdrant_client.models import PointStruct

    if domain not in VALID_DOMAINS:
        print(
            f"[FATAL] Invalid domain '{domain}'. Must be one of: {sorted(VALID_DOMAINS)}",
            file=sys.stderr,
        )
        sys.exit(1)

    client = get_qdrant_client()
    ensure_collection(client, collection, dim=1536)
    embed_client = get_embed_client()

    files = list(source_dir.glob("*.md")) + list(source_dir.glob("*.txt"))
    if not files:
        print(f"[INFO] No .md or .txt files found in {source_dir}")
        return

    all_points: list[PointStruct] = []
    total_chunks = 0

    for file_path in sorted(files):
        try:
            text = file_path.read_text(encoding="utf-8")
            chunks = chunk_text(text, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
            if not chunks:
                continue

            title = file_path.stem.replace("-", " ").replace("_", " ").title()
            embeddings = embed_texts(chunks, embed_client)

            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                point_id = int(
                    uuid.uuid5(uuid.NAMESPACE_DNS, f"{domain}:{file_path.name}:{i}").int
                    % (2**63)
                )
                all_points.append(
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "domain": domain,
                            "doc_type": "document",
                            "title": title,
                            "source_file": file_path.name,
                            "chunk_index": i,
                            "chunk_text": chunk,
                        },
                    )
                )
                total_chunks += 1

            print(f"  [{domain}] {file_path.name} → {len(chunks)} chunks")
        except Exception as e:
            print(f"  [ERROR] {file_path.name}: {e}", file=sys.stderr)

    if all_points:
        for batch_start in range(0, len(all_points), batch_size):
            batch = all_points[batch_start : batch_start + batch_size]
            client.upsert(collection_name=collection, points=batch)

    print(
        f"\n[DONE] Upserted {len(all_points)} points across {len(files)} files "
        f"→ collection '{collection}' (domain={domain})"
    )

    client.close()
    embed_client.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Embed documents and upsert into a Qdrant collection"
    )
    parser.add_argument("--source", required=True, help="Directory containing .md / .txt files")
    parser.add_argument("--collection", default="documents", help="Qdrant collection name")
    parser.add_argument(
        "--domain",
        required=True,
        choices=sorted(VALID_DOMAINS),
        help="Domain tag for payload isolation",
    )
    parser.add_argument("--batch-size", type=int, default=100, help="Points per upsert batch")
    args = parser.parse_args()

    source = Path(args.source)
    if not source.is_dir():
        print(f"[FATAL] Source directory not found: {source}", file=sys.stderr)
        sys.exit(1)

    upsert_documents(
        source_dir=source,
        collection=args.collection,
        domain=args.domain,
        batch_size=args.batch_size,
    )


if __name__ == "__main__":
    main()
