# frontend/views/ai_consult_panel.py
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QFrame, QSizePolicy, QGraphicsDropShadowEffect
)
from presenters.ai_consult_presenter import AIConsultPresenter
from utils.message_box import MessageBox

class ChatBubble(QWidget):
    """
    A single chat bubble representing either a user or assistant message.
    - User bubbles are right-aligned, styled blue with white text.
    - Assistant bubbles are left-aligned, styled light gray with dark text.
    """
    def __init__(self, text: str, is_user: bool):
        super().__init__()
        outer = QHBoxLayout(self)
        outer.setContentsMargins(6, 0, 6, 0)

        bubble = QFrame()
        bubble.setObjectName("bubble_user" if is_user else "bubble_bot")
        bubble.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        inner = QVBoxLayout(bubble)
        inner.setContentsMargins(14, 10, 14, 10)

        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        inner.addWidget(lbl)

        if is_user:
            outer.addStretch(1)
            outer.addWidget(bubble, 0, Qt.AlignRight)
        else:
            outer.addWidget(bubble, 0, Qt.AlignLeft)
            outer.addStretch(1)

        self.setStyleSheet("""
            QFrame#bubble_user { background: #FFF4E8; color: #0F172A; border-radius:14px; border:1px solid #3A6A37;}
            QFrame#bubble_bot  { background: #FFF4E8; color: #0F172A; border-radius:14px; border:1px solid #E2742D; }
            QLabel { font-size:14px; }
        """)


class TypingIndicator(ChatBubble):
    """
    A special chat bubble that simulates typing activity by the assistant.
    Shows an animated 'Assistant is typing...' with dots cycling every 400ms.
    """
    def __init__(self):
        super().__init__("Assistant is typing", is_user=False)
        self._dots = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(400)

    def _tick(self):
        self._dots = (self._dots + 1) % 4
        self.findChild(QLabel).setText("Assistant is typing" + "." * self._dots)

    def stop(self):
        """Stop the typing animation."""
        self._timer.stop()


class AIConsultPanel(QWidget):
    """
    Floating chat panel that appears when the AI chat button is toggled.
    Contains:
      - A header with title and control buttons.
      - A scrollable area with chat history (user and assistant bubbles).
      - A text input row with a send button.

    Controlled by `AIChatButton` and powered by `AIConsultPresenter`.
    """
    def __init__(self, parent, token: str):
        super().__init__(parent)
        self.token = token
        self.setObjectName("ai_consult_panel")
        self.setFixedSize(380, 520)
        self.setAttribute(Qt.WA_StyledBackground, True)

        # Card container with drop shadow
        card = QFrame(self)
        card.setObjectName("chat_card")
        card.setGeometry(0, 0, self.width(), self.height())
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        card.setGraphicsEffect(shadow)

        root = QVBoxLayout(card)
        root.setContentsMargins(12, 12, 12, 12)

        # --- Header ---
        header = QHBoxLayout()
        header.addWidget(QLabel("AI Assistant"))
        header.addStretch(1)

        self.clear_btn = QPushButton("Clear history")
        self.clear_btn.setObjectName("ChatButton")
        self.clear_btn.setFixedHeight(28)
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        header.addWidget(self.clear_btn)

#

        root.addLayout(header)

        # --- Chat area ---
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self._chat_host = QWidget()
        self._chat_layout = QVBoxLayout(self._chat_host)
        self._chat_layout.setContentsMargins(4, 6, 4, 6)
        self._chat_layout.setSpacing(8)
        self._chat_layout.addStretch(1)

        self.scroll.setWidget(self._chat_host)
        root.addWidget(self.scroll, 1)

        # --- Input row ---
        row = QHBoxLayout()
        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("e.g., What is tahini?")
        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("ChatButton")
        self.send_btn.setFixedHeight(34)
        row.addWidget(self.question_input, 1)
        row.addWidget(self.send_btn)
        root.addLayout(row)

        # --- Presenter ---
        self._typing_widget: TypingIndicator | None = None
        self.presenter = AIConsultPresenter(self, lambda: self.token)
        self.send_btn.clicked.connect(self._on_send_clicked)
        self.presenter.on_open()

        # Styling
        self.setStyleSheet("""
            #chat_card { background: #FFF4E8; border-radius:14px; border:1px solid #3A6A37; }
            QLineEdit { padding:8px 10px; border:1px solid #3A6A37; border-radius:10px; }
            QPushButton { background:#FDBA74; border:none; border-radius:10px; padding:7px 14px; font-weight:600; }
            QPushButton:hover { background:#FB923C; }
        """)

        self.hide()

    # ---- View API (called by presenter) ----
    def append_user(self, text: str):
        """Append a user bubble to the chat history."""
        self._insert_bubble(ChatBubble(text, is_user=True))

    def append_assistant(self, text: str, sources=None):
        """Append an assistant bubble (removing typing indicator if active)."""
        if self._typing_widget:
            self._remove_typing()
        self._insert_bubble(ChatBubble(text, is_user=False))

    def clear_messages(self):
        """Clear all messages from the chat area."""
        while self._chat_layout.count() > 1:  # leave the stretch
            item = self._chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def set_busy(self, busy: bool):
        """Enable/disable input and send button."""
        self.question_input.setDisabled(busy)
        self.send_btn.setDisabled(busy)

    def show_error(self, msg: str):

        MessageBox.show_error(self, msg)

    def show_info(self, msg: str):
        
        MessageBox.show_info(self, msg)

    def show_typing(self, show: bool):
        """Show or hide typing indicator."""
        if show and not self._typing_widget:
            self._typing_widget = TypingIndicator()
            self._insert_bubble(self._typing_widget)
        elif not show:
            self._remove_typing()

    # ---- Actions ----
    def _on_send_clicked(self):
        """Send message from input field via presenter."""
        txt = self.question_input.text().strip()
        if not txt:
            return
        self.question_input.clear()
        self.presenter.send_message(txt)
        self._scroll_to_bottom()

    def _on_clear_clicked(self):
        """Clear chat history (both local and server-side if confirmed)."""
        if MessageBox.ask_confirm(self, "Clear history?", 
                                "Delete the current chat session from the server?"):
            ok, server_msg = self.presenter.clear_history(delete_on_server=True)
            if ok:
                self.clear_messages()
                self.show_info("History cleared.")
            else:
                self.show_error(server_msg or "Failed to clear history.")

    # ---- Helpers ----
    def _insert_bubble(self, widget: QWidget):
        """Insert a chat bubble widget into the chat area."""
        self._chat_layout.insertWidget(self._chat_layout.count()-1, widget, 0, Qt.AlignTop)
        self._scroll_to_bottom()

    def _remove_typing(self):
        """Remove the typing indicator if it exists."""
        if self._typing_widget:
            self._typing_widget.stop()
            self._typing_widget.deleteLater()
            self._typing_widget = None

    def _scroll_to_bottom(self):
        """Scroll to the latest message in the chat area."""
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())
