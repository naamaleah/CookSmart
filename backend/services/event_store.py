# backend/services/event_store.py
from __future__ import annotations
from typing import Optional, Dict, Any
import json

def _next_version(cur, aggregate_type: str, aggregate_id: Optional[int]) -> int:
    """
    Determine the next event version for a given aggregate.
    If no prior events exist, version starts at 1.
    """
    if aggregate_id is None:
        return 1
    cur.execute("""
        SELECT ISNULL(MAX(event_version), 0) + 1
        FROM events
        WHERE aggregate_type = ? AND aggregate_id = ?
    """, (aggregate_type, aggregate_id))
    row = cur.fetchone()
    return int(row[0] or 1)

def append_event(conn, aggregate_type: str, aggregate_id: Optional[int],
                 event_type: str, payload: Dict[str, Any], user_id: Optional[int] = None) -> int:
    """
    Append a new event to the event store (append-only).
    Should be called within the same transaction as the CRUD operation (projection).
    Returns the assigned event_version.
    """
    cur = conn.cursor()
    ver = _next_version(cur, aggregate_type, aggregate_id)
    cur.execute("""
        INSERT INTO events(aggregate_type, aggregate_id, event_type, event_version, payload, user_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (aggregate_type, aggregate_id, event_type, ver, json.dumps(payload, ensure_ascii=False), user_id))
    return ver
