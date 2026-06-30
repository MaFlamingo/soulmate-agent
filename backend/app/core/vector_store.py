"""Lightweight vector store using numpy + JSON file storage.

Replaces ChromaDB dependency for zero-compilation installation on Windows.
Uses cosine similarity via numpy/scikit-learn for vector search.
"""

import json
import os
import threading
from pathlib import Path
import numpy as np
from loguru import logger

# Resolve persist dir
_store_dir = Path(__file__).resolve().parent.parent.parent / "data"
_store_dir.mkdir(parents=True, exist_ok=True)
_vectors_file = _store_dir / "vectors.json"

# In-memory store: {doc_id: {"embedding": [...], "metadata": {...}}}
_store: dict[str, dict] = {}
_lock = threading.Lock()


def _load_store():
    """Load vectors from disk."""
    global _store
    if _vectors_file.exists():
        try:
            with open(_vectors_file, "r", encoding="utf-8") as f:
                _store = json.load(f)
            logger.info(f"Loaded {len(_store)} vectors from {_vectors_file}")
        except Exception as e:
            logger.warning(f"Failed to load vectors file: {e}")
            _store = {}


def _save_store():
    """Persist vectors to disk."""
    try:
        with open(_vectors_file, "w", encoding="utf-8") as f:
            json.dump(_store, f)
    except Exception as e:
        logger.error(f"Failed to save vectors: {e}")


# Load on module import
_load_store()


def upsert_profile_embedding(
    user_id: int,
    embedding: list[float],
    metadata: dict | None = None,
) -> str:
    """Insert or update a user's profile embedding."""
    doc_id = f"user_{user_id}"
    with _lock:
        _store[doc_id] = {
            "embedding": embedding,
            "metadata": metadata or {},
        }
        _save_store()
    logger.debug(f"Upserted embedding for user_{user_id}")
    return doc_id


def delete_profile_embedding(user_id: int) -> None:
    """Remove a user's profile embedding."""
    doc_id = f"user_{user_id}"
    with _lock:
        if doc_id in _store:
            del _store[doc_id]
            _save_store()
    logger.debug(f"Deleted embedding for user_{user_id}")


def similarity_search(
    query_embedding: list[float],
    exclude_user_ids: list[int] | None = None,
    top_k: int = 20,
    filter_metadata: dict | None = None,
) -> list[dict]:
    """Search for the most similar user profiles using cosine similarity.

    Args:
        query_embedding: The query vector.
        exclude_user_ids: User IDs to exclude.
        top_k: Number of results.
        filter_metadata: Key-value pairs to filter by metadata.

    Returns:
        List of dicts with: user_id, distance, similarity, metadata.
    """
    exclude = {f"user_{uid}" for uid in (exclude_user_ids or [])}

    query = np.array(query_embedding, dtype=np.float32)

    results = []
    with _lock:
        for doc_id, data in _store.items():
            if doc_id in exclude:
                continue

            # Metadata filter
            if filter_metadata:
                meta = data.get("metadata", {})
                if not all(meta.get(k) == v for k, v in filter_metadata.items()):
                    continue

            vec = np.array(data["embedding"], dtype=np.float32)

            # Cosine similarity
            dot = np.dot(query, vec)
            norm_q = np.linalg.norm(query)
            norm_v = np.linalg.norm(vec)
            if norm_q == 0 or norm_v == 0:
                similarity = 0.0
            else:
                similarity = float(dot / (norm_q * norm_v))
            distance = 1.0 - similarity

            user_id = int(doc_id.replace("user_", ""))
            results.append({
                "user_id": user_id,
                "distance": distance,
                "similarity": max(0.0, min(1.0, similarity)),
                "metadata": data.get("metadata", {}),
            })

    # Sort by similarity (descending) and return top_k
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:top_k]


def get_profile_embedding(user_id: int) -> list[float] | None:
    """Retrieve a specific user's embedding vector."""
    doc_id = f"user_{user_id}"
    with _lock:
        data = _store.get(doc_id)
        return data["embedding"] if data else None


def get_collection_stats() -> dict:
    """Return basic stats about the vector store."""
    with _lock:
        return {
            "count": len(_store),
            "name": "numpy_vector_store",
        }


def reset_collection() -> None:
    """Delete all vectors (for admin rebuild)."""
    global _store
    with _lock:
        _store = {}
        _save_store()
    logger.info("Vector store reset")


def rebuild_all_embeddings(profiles: list[dict]) -> int:
    """Rebuild all profile embeddings. Returns count of embeddings created."""
    count = 0
    for p in profiles:
        uid = p.get("user_id")
        emb = p.get("embedding")
        meta = p.get("metadata", {})
        if uid is not None and emb is not None:
            upsert_profile_embedding(uid, emb, meta)
            count += 1
    logger.info(f"Rebuilt {count} embeddings")
    return count
