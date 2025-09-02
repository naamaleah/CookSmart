# frontend/presenters/ai_consult_presenter.py
from __future__ import annotations
from typing import Callable, Optional, Dict, Any, List
from PySide6.QtCore import QRunnable, QObject, Signal, Slot, QThreadPool, QSettings

from services.api import (
    rag_chat, rag_ingest,
    rag_get_or_create_session, rag_get_history,
    rag_delete_session, rag_delete_latest_session,
)

# ---------- Workers ----------
class _ChatWorkerSignals(QObject):
    finished = Signal(dict)
    error = Signal(str)

class _ChatWorker(QRunnable):
    """
    Background worker for sending a chat message to the RAG service.
    """
    def __init__(self, message: str, session_id: Optional[str], token: str, timeout_sec: int = 240):
        super().__init__()
        self.message, self.session_id, self.token, self.timeout_sec = message, session_id, token, timeout_sec
        self.signals = _ChatWorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            resp = rag_chat(self.message, self.session_id, self.token, timeout_sec=self.timeout_sec)
            self.signals.finished.emit(resp)
        except Exception as e:
            self.signals.error.emit(str(e))

class _InitWorkerSignals(QObject):
    finished = Signal(dict)
    error = Signal(str)

class _InitWorker(QRunnable):
    """
    Background worker for initializing a chat session and loading history.
    """
    def __init__(self, token: str, session_id_hint: Optional[str], limit: int = 200):
        super().__init__()
        self.token, self.session_id_hint, self.limit = token, session_id_hint, limit
        self.signals = _InitWorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            sid = self.session_id_hint or rag_get_or_create_session(self.token).get("session_id")
            hist = rag_get_history(sid, self.token, limit=self.limit)
            self.signals.finished.emit({"session_id": sid, "messages": hist.get("messages", [])})
        except Exception as e:
            self.signals.error.emit(str(e))

# ---------- Presenter ----------
class AIConsultPresenter:
    """
    Presenter for managing AI consultation chat sessions:
    - Initializes and restores sessions.
    - Sends and receives messages asynchronously.
    - Handles document ingestion for RAG context.
    - Persists session state using QSettings.
    """
    def __init__(self, view, token_provider: Callable[[], str]):
        self.view = view
        self._token_provider = token_provider
        self._session_id: Optional[str] = None
        self._pool = QThreadPool.globalInstance()
        self._workers: List[QRunnable] = []
        self._timeout_sec = 240
        self._settings = QSettings("CookSmart", "Client")

    # --- Helpers ---
    def _require_token(self) -> str:
        """Ensure a valid token exists, otherwise raise an error."""
        token = self._token_provider() if self._token_provider else ""
        if not token:
            raise RuntimeError("No token (JWT) found. Please sign in again.")
        return token

    def _safe_call(self, method: str, *args, **kwargs):
        """Call a method on the view if it exists, ignoring missing methods."""
        if hasattr(self.view, method):
            getattr(self.view, method)(*args, **kwargs)

    # --- Init & History ---
    def on_open(self) -> None:
        """Initialize presenter: restore session or create new one, then load history."""
        self._safe_call("set_busy", True)
        try:
            token = self._require_token()
            sid_local = self._settings.value("chat/last_session_id", type=str)
            worker = _InitWorker(token, sid_local, limit=200)
            worker.signals.finished.connect(self._on_init_ok)
            worker.signals.error.connect(self._on_init_err)
            self._workers.append(worker)
            self._pool.start(worker)
        except Exception as ex:
            self._safe_call("show_error", str(ex))
            self._safe_call("set_busy", False)

    def _on_init_ok(self, payload: Dict[str, Any]) -> None:
        """Handle successful session initialization and render chat history."""
        self._session_id = payload.get("session_id", self._session_id)
        if self._session_id:
            self._settings.setValue("chat/last_session_id", self._session_id)

        msgs = payload.get("messages", [])
        self._safe_call("clear_messages")
        for m in msgs:
            role, content = (m.get("role") or "").lower(), m.get("content") or ""
            if role == "user":
                self._safe_call("append_user", content)
            else:
                self._safe_call("append_assistant", content, [])
        self._safe_call("set_busy", False)

    def _on_init_err(self, msg: str) -> None:
        """Handle initialization errors."""
        self._safe_call("show_error", msg)
        self._safe_call("set_busy", False)

    # --- Send ---
    def send_message(self, text: str) -> None:
        """Send a new message to the assistant asynchronously."""
        text = (text or "").strip()
        if not text: 
            return
        self._safe_call("append_user", text)
        self._safe_call("show_typing", True)
        self._safe_call("set_busy", True)

        try:
            token = self._require_token()
            worker = _ChatWorker(text, self._session_id, token, timeout_sec=self._timeout_sec)
            worker.signals.finished.connect(self._on_chat_ok)
            worker.signals.error.connect(self._on_chat_err)
            self._workers.append(worker)
            self._pool.start(worker)
        except Exception as ex:
            self._safe_call("show_typing", False)
            self._safe_call("show_error", str(ex))
            self._safe_call("set_busy", False)

    def _on_chat_ok(self, resp: Dict[str, Any]) -> None:
        """Handle a successful chat response from the assistant."""
        self._safe_call("show_typing", False)
        self._session_id = resp.get("session_id", self._session_id)
        if self._session_id:
            self._settings.setValue("chat/last_session_id", self._session_id)

        answer, sources = (resp.get("answer") or "").strip(), resp.get("sources", [])
        self._safe_call("append_assistant", answer, sources)
        self._safe_call("set_busy", False)

    def _on_chat_err(self, msg: str) -> None:
        """Handle errors that occur while sending a chat message."""
        self._safe_call("show_typing", False)
        self._safe_call("show_error", msg)
        self._safe_call("set_busy", False)

    # --- Clear / Delete ---
    def clear_history(self, delete_on_server: bool = True) -> tuple[bool, str]:
        """Clear local and optionally server-side chat history."""
        try:
            token = self._require_token()
            if delete_on_server:
                if self._session_id:
                    rag_delete_session(self._session_id, token)
                else:
                    rag_delete_latest_session(token)
        except Exception as e:
            return False, str(e)

        self.reset_session()
        return True, "cleared"

    def reset_session(self) -> None:
        """Reset current session and clear local history."""
        self._session_id = None
        self._safe_call("clear_messages")
        self._settings.remove("chat/last_session_id")

    def continue_session(self, session_id: str) -> None:
        """Resume a session by explicitly setting the session ID."""
        self._session_id = (session_id or "").strip() or None
        if self._session_id:
            self._settings.setValue("chat/last_session_id", self._session_id)

    @property
    def session_id(self) -> Optional[str]:
        return self._session_id

    # --- Ingestion ---
    def ingest_document(self, title: str, source: str, full_text: str) -> None:
        """Ingest a document into the RAG system for later retrieval context."""
        title, source, full_text = title.strip(), (source or "recipes").strip(), full_text.strip()
        if not title or not full_text:
            self._safe_call("show_error", "Title or text is empty — ingestion skipped.")
            return

        self._safe_call("set_busy", True)
        try:
            token = self._require_token()
            result = rag_ingest(title=title, source=source, full_text=full_text, token=token)
            self._safe_call("show_info",
                            f"Ingestion completed: doc_id={result.get('doc_id')}, chunks={result.get('chunks')}")
        except Exception as ex:
            self._safe_call("show_error", str(ex))
        finally:
            self._safe_call("set_busy", False)
