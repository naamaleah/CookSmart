# frontend/views/base_view.py
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPixmap, QPalette, QBrush
from PySide6.QtCore import Qt


class BaseView(QWidget):
    """
    Base class for all views in the application.

    Provides a **shared background image** that is loaded once and reused
    across all instances of BaseView (and its subclasses).  
    The background automatically scales with window resize events.
    """

    # Shared cached background image (class-level, loaded once)
    _shared_background = None

    def __init__(self):
        super().__init__()

        # Load background only once (static/shared for all views)
        if BaseView._shared_background is None:
            BaseView._shared_background = QPixmap("frontend/images/final_background.png")

        self._background_pixmap = BaseView._shared_background
        self._apply_background()

    def _apply_background(self):
        """
        Scale and apply the background image to the current widget
        using the widget's size as reference.
        """
        if not self._background_pixmap.isNull():
            scaled_pixmap = self._background_pixmap.scaled(
                self.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation,
            )
            palette = QPalette()
            palette.setBrush(QPalette.Window, QBrush(scaled_pixmap))
            self.setAutoFillBackground(True)
            self.setPalette(palette)

    def resizeEvent(self, event):
        """
        Override resize event to reapply the scaled background
        whenever the widget is resized.
        """
        self._apply_background()
        super().resizeEvent(event)
