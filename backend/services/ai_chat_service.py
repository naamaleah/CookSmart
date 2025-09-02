# backend/services/ai_chat_service.py
# -------------------------------------------------
# Multi-turn RAG chat via Ollama (/api/generate),
# with short history, user taste profile (favorites),
# robust retrieval handling, EN-only & brief answers,
# and DB session deletion helpers.

from __future__ import annotations
from typing import Any, Dict, List, Optional
import re
import requests
import uuid
from fastapi import HTTPException

from ..db.db_config import get_sqlserver_conn
from .rag_retrieval_service import retrieve_context

# ---- Model / Server ----
from dotenv import load_dotenv
import os

load_dotenv()
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
GEN_MODEL = os.getenv("OLLAMA_MODEL", "llama3")


# ---- Output constraints ----
MAX_HISTORY_MESSAGES = 8      # keep history short for speed
MAX_WORDS = 50                # enforce concise answers
NUM_PREDICT = 96              # limit generation length
TEMPERATURE = 0.6

# ---- Assistant instructions ----
SYSTEM_PROMPT = (
    "You are CookSmart's culinary assistant.\n"
    "- ENGLISH ONLY.\n"
    "- Be brief: one short paragraph (<= 50 words) OR up to 4 tiny bullet points.\n"
    "- Stay strictly ON TOPIC of the user message.\n"
    "- If an ingredient is mentioned (e.g., tahini), focus on definition, uses, nutrition, related recipes.\n"
    "- Use RAG context and cite [1], [2] when relevant. Prefer the user's taste profile.\n"
    "- If unsure and no context, ask ONE short clarifying question first.\n"
)

# -------------------------
# History & sessions
# -------------------------
def _load_history(session_id: str) -> List[Dict[str, str]]:
    """Load a limited number of chat history messages for the session."""
    try:
        with get_sqlserver_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT role, content
                FROM chat_messages
                WHERE session_id = ?
                ORDER BY created_at ASC, msg_id ASC
                """,
                (str(session_id),),
            )
            msgs = [{"role": r, "content": c} for r, c in cur.fetchall()]
            return msgs[-MAX_HISTORY_MESSAGES:]
    except Exception as e:
        print("load_history error:", e)
        return []

def load_history_for_api(session_id: str, limit: int = 50) -> List[Dict[str, str]]:
    """Retrieve session history for API consumption, limited to `limit` messages."""
    try:
        with get_sqlserver_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT TOP 500 role, content, created_at
                FROM chat_messages
                WHERE session_id = ?
                ORDER BY created_at ASC, msg_id ASC
                """,
                (str(session_id),),
            )
            rows = cur.fetchall()
        out: List[Dict[str, str]] = []
        for role, content, created_at in rows[-limit:]:
            out.append({"role": role, "content": content, "created_at": str(created_at)})
        return out
    except Exception as e:
        print("load_history_for_api error:", e)
        return []

def _save_msg(session_id: str, role: str, content: str) -> None:
    """Persist a message (user or assistant) in the database."""
    with get_sqlserver_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO chat_messages(session_id, role, content) VALUES (?, ?, ?)",
            (str(session_id), role, content),
        )
        conn.commit()

def ensure_session(session_id: Optional[str] = None, user_id: Optional[int] = None) -> str:
    """Ensure a session exists, creating one if necessary."""
    if session_id:
        return session_id
    with get_sqlserver_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO chat_sessions(user_id) OUTPUT INSERTED.session_id VALUES(?)",
            (user_id,),
        )
        return cur.fetchone()[0]

def get_or_create_latest_session(user_id: int) -> str:
    """Get the latest session for a user or create a new one."""
    sid = get_latest_session_id_only(user_id)
    if sid:
        return sid

    sid = str(uuid.uuid4())
    try:
        with get_sqlserver_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO chat_sessions (session_id, user_id, created_at)
                VALUES (?, ?, GETDATE())
                """,
                (sid, user_id),
            )
            conn.commit()
    except Exception as e:
        print("get_or_create_latest_session insert error:", e)
        # Retry if another session was created meanwhile
        s2 = get_latest_session_id_only(user_id)
        if s2:
            return s2
        raise
    return sid

def get_latest_session_id_only(user_id: int) -> Optional[str]:
    """Return the most recent session_id for a user."""
    try:
        with get_sqlserver_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT TOP 1 session_id
                FROM chat_sessions
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (user_id,),
            )
            row = cur.fetchone()
            return str(row[0]) if row else None
    except Exception as e:
        print("get_latest_session_id_only error:", e)
        return None

def _render_history_as_prompt(history: List[Dict[str, str]]) -> str:
    """Format history messages into a prompt for the assistant."""
    lines = [f"System: {SYSTEM_PROMPT}"]
    for m in history:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role == "assistant":
            lines.append(f"Assistant: {content}")
        elif role == "system":
            lines.append(f"System: {content}")
        else:
            lines.append(f"User: {content}")
    return "\n".join(lines)

# -------------------------
# User taste profile (favorites)
# -------------------------
def _favorites_profile_text(user_id: Optional[int], max_items: int = 10) -> str:
    """Return a short textual profile of the user's favorite recipes."""
    if not user_id:
        return ""
    try:
        with get_sqlserver_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT TOP (?) r.name, r.category, r.area
                FROM favorites f
                JOIN recipes r ON r.recipeid = f.recipeid
                WHERE f.userid = ?
                ORDER BY r.recipeid DESC
                """,
                (max_items, user_id),
            )
            rows = cur.fetchall()

        if not rows:
            return ""

        lines = []
        for name, category, area in rows:
            bits = [name]
            if category:
                bits.append(f"({category})")
            if area:
                bits.append(f"- {area}")
            lines.append(" • " + " ".join(bits))
        return "User favorites (recent first):\n" + "\n".join(lines)

    except Exception as e:
        print("favorites profile error:", e)
        return ""

# -------------------------
# English-only & brevity enforcement
# -------------------------
_HEBREW_RE = re.compile(r"[\u0590-\u05FF]")

def _needs_english_or_shortening(text: str) -> bool:
    """Check if text is too long or contains non-English (Hebrew)."""
    if not text:
        return False
    too_long = len(text.split()) > MAX_WORDS + 5
    has_hebrew = bool(_HEBREW_RE.search(text))
    return too_long or has_hebrew

def _rewrite_english_brief(text: str) -> str:
    """Rewrite assistant output to enforce English-only and brevity."""
    try:
        prompt = (
            "Rewrite the following assistant answer in ENGLISH ONLY. "
            f"Keep it very concise: one short paragraph (<= {MAX_WORDS} words) "
            "OR up to 4 very short bullet points. Remove filler.\n\n"
            f"ANSWER:\n{text}\n\n"
            "Rewritten:"
        )
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": GEN_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": 160, "temperature": 0.2},
            },
            timeout=90,
        )
        r.raise_for_status()
        rewritten = (r.json().get("response") or "").strip()
        if rewritten:
            words = rewritten.split()
            if len(words) > MAX_WORDS:
                rewritten = " ".join(words[:MAX_WORDS]) + "..."
            return rewritten
    except Exception as e:
        print("rewrite_english_brief error:", e)

    words = text.split()
    if len(words) > MAX_WORDS:
        return " ".join(words[:MAX_WORDS]) + "..."
    return text

# -------------------------
# Core chat
# -------------------------
def chat(session_id: str, user_message: str, user_id: Optional[int] = None) -> Dict[str, Any]:
    """Main chat function: saves message, retrieves context, builds prompt, and queries LLM."""
    # 1) Save user message
    try:
        _save_msg(session_id, "user", user_message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB save(user) failed: {e}")

    # 2) RAG context
    context_text, sources = retrieve_context(user_message, top_k=3)
    if not isinstance(context_text, str) or not isinstance(sources, list):
        context_text, sources = "", []

    # 3) User taste profile
    profile_text = _favorites_profile_text(user_id, max_items=10)

    # 4) Build prompt
    history = _load_history(session_id)
    prompt = _render_history_as_prompt(history)
    if profile_text:
        prompt += "\n\nUser taste profile:\n" + profile_text
    if context_text:
        prompt += "\n\nContext:\n" + context_text
    prompt += f"\n\nUser: {user_message}\nAssistant:"

    # 5) Call Ollama
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": GEN_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": NUM_PREDICT,
                    "temperature": TEMPERATURE,
                    "stop": ["\nUser:", "\nSystem:"],
                },
            },
            timeout=180,
        )
        if r.status_code == 404:
            raise HTTPException(
                status_code=502,
                detail="Ollama model not found (try `ollama pull llama3`).",
            )
        r.raise_for_status()
        data = r.json()
        answer = (data.get("response") or "").strip()
        if not answer:
            answer = "No response from the model."
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {e}")

    # 6) Enforce English & brevity
    if _needs_english_or_shortening(answer):
        answer = _rewrite_english_brief(answer)

    # 7) Save assistant reply (best effort)
    try:
        _save_msg(session_id, "assistant", answer)
    except Exception as e:
        print("DB save(assistant) failed:", e)

    return {"answer": answer, "sources": sources, "session_id": str(session_id)}

# -------------------------
# Session deletion (DB)
# -------------------------
def delete_session(session_id: str, user_id: Optional[int]) -> int:
    """
    Delete a session and its messages.
    - Enforce ownership if chat_sessions row exists.
    - If session row is missing but messages exist, delete messages anyway.
    Returns number of deleted messages. Raises 404 only if nothing to delete.
    """
    sid = str(session_id)
    with get_sqlserver_conn() as conn:
        cur = conn.cursor()

        owner_id = None
        try:
            cur.execute(
                "SELECT user_id FROM chat_sessions WHERE session_id = ?", (sid,)
            )
            row = cur.fetchone()
            if row:
                owner_id = int(row[0]) if row[0] is not None else None
        except Exception:
            row = None

        if row and (user_id is not None) and (owner_id is not None) and owner_id != user_id:
            raise HTTPException(status_code=403, detail="Not allowed to delete this session.")

        cur.execute("SELECT COUNT(*) FROM chat_messages WHERE session_id = ?", (sid,))
        msg_count = int(cur.fetchone()[0] or 0)

        if (row is None) and msg_count == 0:
            raise HTTPException(status_code=404, detail="Session not found.")

        cur.execute("DELETE FROM chat_messages WHERE session_id = ?", (sid,))
        try:
            cur.execute("DELETE FROM chat_sessions WHERE session_id = ?", (sid,))
        except Exception:
            pass

        conn.commit()
        return msg_count

# -------------------------
# Resolve user id by username
# -------------------------
def get_user_id_by_username(username: str) -> Optional[int]:
    """Resolve user id from the 'users' table using username."""
    try:
        with get_sqlserver_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT userid FROM users WHERE username = ?", (username,))
            row = cur.fetchone()
            return int(row[0]) if row else None
    except Exception as e:
        print("get_user_id_by_username error:", e)
        return None
