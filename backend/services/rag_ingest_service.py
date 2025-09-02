# backend/services/rag_ingest_service.py
from __future__ import annotations
import asyncio, json, textwrap
from typing import Optional, Tuple, List
from backend.gateway import Gateway
from backend.db.db_config import get_sqlserver_conn
from .embedding_service import EmbeddingService

_gateway: Optional[Gateway] = None

def set_gateway(gateway: Gateway) -> None:
    """Set the global Gateway instance to be used by the ingestion service."""
    global _gateway
    _gateway = gateway

def _run(coro):
    """Run an async coroutine in a sync context (with proper event loop handling)."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    else:
        return loop.run_until_complete(coro)

def _chunk(paragraphs: str, max_len: int = 1200) -> List[str]:
    """
    Split text into smaller chunks by paragraphs with soft wrapping.
    Ensures no chunk exceeds `max_len` characters.
    """
    parts = [p.strip() for p in paragraphs.split("\n\n") if p.strip()]
    out: List[str] = []
    for p in parts:
        if len(p) <= max_len:
            out.append(p)
            continue
        out.extend(textwrap.wrap(p, width=max_len, break_long_words=False, replace_whitespace=False))
    return out

def embed_text(text: str) -> list[float]:
    """
    Generate an embedding vector for a single text chunk.
    Requires the Gateway to be set beforehand.
    """
    if _gateway is None:
        raise RuntimeError("Gateway not set. Call set_gateway(gateway).")
    svc = EmbeddingService(_gateway)
    return _run(svc.embed_text(text))

def ingest_document(title: str, source: str, full_text: str) -> Tuple[int, int]:
    """
    Ingest a document into the database.
    - Splits text into chunks.
    - Stores document metadata in `documents`.
    - Stores chunks with embeddings in `chunks`.
    Returns the document ID and number of chunks.
    """
    if _gateway is None:
        raise RuntimeError("Gateway not set. Call set_gateway(gateway).")
    chunks = _chunk(full_text)
    if not chunks:
        return (0, 0)

    with get_sqlserver_conn() as conn:
        cur = conn.cursor()
        # Insert document
        cur.execute("""
            INSERT INTO documents (title, source) OUTPUT INSERTED.doc_id VALUES (?, ?)
        """, (title, source))
        doc_id = int(cur.fetchone()[0])

        # Insert chunks with embeddings
        for i, c in enumerate(chunks):
            vec = embed_text(c)
            cur.execute("""
              INSERT INTO chunks (doc_id, content, embedding, ord)
              VALUES (?, ?, ?, ?)
            """, (doc_id, c, json.dumps(vec), i))
        conn.commit()
    return (doc_id, len(chunks))
