# frontend/utils/ai_chat_button.py
from PySide6.QtWidgets import QPushButton, QWidget
from PySide6.QtCore import QTimer
from views.ai_consult_panel import AIConsultPanel  # Chat panel container


class AIChatButton(QPushButton):
    """
    Floating circular button (🤖) that anchors to the bottom-left corner
    of its parent widget. Toggles visibility of the AIConsultPanel.
    """

    def __init__(self, parent: QWidget, token: str):
        super().__init__("🤖", parent)
        self.token = token

        # Style button (circular, branded color)
        self.setObjectName("AIChatButton")
        self.setFixedSize(50, 50)

        # Create the floating chat panel (initially hidden)
        self.chat_panel = AIConsultPanel(parent, token)
        self.chat_panel.hide()

        # Initial positioning
        self._position_widgets()

        # Toggle panel visibility on click
        self.clicked.connect(self.toggle_panel)

        # Track parent resize (to reposition button & panel)
        QTimer.singleShot(100, self._track_resize)

    # ---------------------------
    # Resize & Positioning
    # ---------------------------
    def _track_resize(self):
        """Hook into parent's resizeEvent to keep button anchored."""
        if self.parent():
            original = getattr(self.parent(), "resizeEvent", None)

            def _on_parent_resize(event):
                self._position_widgets()
                if callable(original):
                    original(event)
                else:
                    event.accept()

            # Override parent's resizeEvent with a chained version
            self.parent().resizeEvent = _on_parent_resize  # type: ignore

    def _position_widgets(self):
        """Anchor button bottom-left and position panel just above it."""
        if not self.parent():
            return

        parent = self.parent()
        margin = 8

        # Button at bottom-left corner
        self.move(margin, parent.height() - self.height() - margin)

        # If panel is visible, keep it above the button
        if self.chat_panel.isVisible():
            panel_x = margin
            panel_y = parent.height() - self.chat_panel.height() - self.height() - margin - 8
            if panel_y < margin:
                panel_y = margin
            self.chat_panel.move(panel_x, panel_y)

    # ---------------------------
    # Toggle panel
    # ---------------------------
    def toggle_panel(self):
        """Show/hide the AIConsultPanel above the button."""
        if self.chat_panel.isVisible():
            self.chat_panel.hide()
        else:
            self.chat_panel.show()
            self.chat_panel.raise_()
            self._position_widgets()
