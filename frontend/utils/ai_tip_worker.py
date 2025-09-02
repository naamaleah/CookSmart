# frontend/utils/ai_tip_worker.py
from PySide6.QtCore import QObject, Signal, QRunnable, Slot
from services.api import ask_ai_agent


class AITipWorkerSignals(QObject):
    """
    Signal container for AITipWorker.
    Emits the retrieved cooking tip as a string.
    """
    finished = Signal(str)


class AITipWorker(QRunnable):
    """
    Background worker that fetches a short cooking tip from the AI agent.
    Runs in a thread pool to avoid blocking the UI.
    """

    def __init__(self):
        super().__init__()
        self.signals = AITipWorkerSignals()

    @Slot()
    def run(self):
        """Perform the AI request and emit the result."""
        tip = ask_ai_agent("Give one short, punchy cooking tip (max 80 chars).")
        self.signals.finished.emit(tip.strip())
