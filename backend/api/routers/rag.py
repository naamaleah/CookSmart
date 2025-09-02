# backend/api/routers/rag.py
from fastapi import APIRouter, Depends, Body, Query, HTTPException

from backend.api.deps import get_gateway
from backend.gateway import Gateway

from ...services import rag_ingest_service, ai_chat_service, rag_retrieval_service
from ...utils.auth_utils import get_current_user  # JWT-based authentication

# Router for RAG (Retrieval-Augmented Generation) endpoints
router = APIRouter(prefix="/rag", tags=["RAG"])

def _resolve_user_id(user) -> int | None:
    """
    Resolve the user identifier from different possible formats (dict, object, or string).
    Returns the user ID as an integer, or None if it cannot be resolved.
    """
    try:
        if isinstance(user, dict):
            return user.get("id") or user.get("user_id")
        if hasattr(user, "id"):
            return getattr(user, "id")
        if isinstance(user, str):
            s = user.strip()
            if s.isdigit():
                return int(s)
            return ai_chat_service.get_user_id_by_username(s)
    except Exception:
        pass
    return None


# -------- Ingest --------
@router.post("/ingest", summary="Ingest a document to RAG")
def ingest_doc(
    title: str = Query(..., description="Title of the document"),
    source: str = Query("recipes", description="Source or category of the document"),
    full_text: str = Body(..., description="Full text of the document to ingest"),
    user=Depends(get_current_user),
    gateway: Gateway = Depends(get_gateway),
):
    """
    Ingest a document into the RAG system.
    Splits the document into chunks and stores them for retrieval.
    """
    rag_ingest_service.set_gateway(gateway)
    doc_id, n_chunks = rag_ingest_service.ingest_document(title, source, full_text)
    return {"doc_id": doc_id, "chunks": n_chunks}


# -------- Chat --------
@router.post("/chat", summary="Multi-turn RAG chat")
def rag_chat(
    message: str = Body(..., embed=True, description="User message for the AI chat"),
    session_id: str | None = Body(None, description="Existing session ID if continuing a chat"),
    user=Depends(get_current_user),
    gateway: Gateway = Depends(get_gateway),
):
    """
    Perform a multi-turn chat with the RAG system.
    Uses embeddings for retrieval and maintains session history.
    """
    rag_retrieval_service.set_gateway(gateway)

    user_id = _resolve_user_id(user)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Cannot resolve current user id.")
    sid = ai_chat_service.ensure_session(session_id, user_id=user_id)
    out = ai_chat_service.chat(sid, message, user_id=user_id)
    return out


# -------- Session/History helpers --------
@router.get("/history", summary="Get messages of a session")
def history(session_id: str, limit: int = 200, user=Depends(get_current_user)):
    """
    Retrieve the message history for a given session.
    """
    return {"messages": ai_chat_service.load_history_for_api(session_id, limit=limit)}


@router.get("/session/current", summary="Get latest session id for current user (no create)")
def get_current_session(user=Depends(get_current_user)):
    """
    Get the most recent session ID for the current user, without creating a new one.
    """
    user_id = _resolve_user_id(user)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Cannot resolve current user id.")
    sid = ai_chat_service.get_latest_session_id_only(user_id)
    if not sid:
        raise HTTPException(status_code=404, detail="No session found for user.")
    return {"session_id": sid}


@router.get("/session/get-or-create", summary="Get latest session id or create a new one")
def get_or_create_session(user=Depends(get_current_user)):
    """
    Retrieve the latest session ID for the current user, or create a new one if none exist.
    """
    user_id = _resolve_user_id(user)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Cannot resolve current user id.")
    sid = ai_chat_service.get_or_create_latest_session(user_id)
    return {"session_id": sid}


@router.delete("/session/{session_id}", summary="Delete a chat session and its messages")
def delete_session(session_id: str, user=Depends(get_current_user)):
    """
    Delete a specific chat session and all of its associated messages.
    """
    user_id = _resolve_user_id(user)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Cannot resolve current user id.")
    deleted = ai_chat_service.delete_session(session_id, user_id=user_id)
    return {"deleted": deleted, "session_id": session_id}


@router.delete("/session/current", summary="Delete user's latest session (if exists)")
def delete_latest_session(user=Depends(get_current_user)):
    """
    Delete the most recent chat session for the current user, if one exists.
    """
    user_id = _resolve_user_id(user)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Cannot resolve current user id.")
    sid = ai_chat_service.get_latest_session_id_only(user_id)
    if not sid:
        return {"deleted": 0, "session_id": None}
    deleted = ai_chat_service.delete_session(sid, user_id=user_id)
    return {"deleted": deleted, "session_id": sid}
