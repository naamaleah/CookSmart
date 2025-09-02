# backend/services/rag_retrieval_service.py
from __future__ import annotations
import asyncio, json, math
from typing import List, Optional, Tuple
from backend.gateway import Gateway
from backend.db.db_config import get_sqlserver_conn
from .embedding_service import EmbeddingService, EmbeddingUnavailable

_gateway: Optional[Gateway] = None

def set_gateway(gateway: Gateway) -> None:
    """Set the global Gateway instance to be used by the retrieval service."""
    global _gateway
    _gateway = gateway

def _run(coro):
    """Run an async coroutine in a sync context (handles event loop safely)."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    else:
        return loop.run_until_complete(coro)

def embed_text(text: str) -> List[float]:
    """
    Generate an embedding vector for a given text.
    Requires the Gateway to be set beforehand.
    """
    if _gateway is None:
        raise RuntimeError("Gateway not set. Call set_gateway(gateway).")
    svc = EmbeddingService(_gateway)
    return _run(svc.embed_text(text))

def _cosine(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not a or not b or len(a) != len(b):
        return -1.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return -1.0
    return dot / (na * nb)

def retrieve_context(query: str, top_k: int = 5) -> Tuple[str, list]:
    """
    Retrieve the most relevant context for a query using vector similarity.
    - Embed the query.
    - Compare with recent chunks from the database.
    - Return top_k results with content and metadata.
    """
    try:
        qv = embed_text(query)
    except EmbeddingUnavailable:
        # Fallback: embeddings unavailable
        return "", []

    rows = []
    try:
        with get_sqlserver_conn() as conn:
            cur = conn.cursor()
            # Retrieve recent chunks and their embeddings
            cur.execute("""
                SELECT TOP 500 c.content, c.embedding, d.title, d.source
                FROM chunks c
                JOIN documents d ON d.doc_id = c.doc_id
                ORDER BY c.chunk_id DESC
            """)
            rows = cur.fetchall()
    except Exception:
        return "", []

    scored = []
    for content, emb_json, title, source in rows:
        try:
            vec = json.loads(emb_json) if emb_json else []
            sim = _cosine(qv, vec)
            if sim > 0:
                scored.append((sim, content, title, source))
        except Exception:
            continue

    scored.sort(key=lambda t: t[0], reverse=True)
    top = scored[:max(1, top_k)]
    context = "\n\n".join(item[1] for item in top)
    sources = [{"title": item[2], "source": item[3], "score": round(item[0], 3)} for item in top]
    return context, sources
