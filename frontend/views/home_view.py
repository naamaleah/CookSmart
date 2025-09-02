# frontend/views/home_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame,
    QSizePolicy, QSpacerItem
)
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QPen
from PySide6.QtCore import Qt
from views.base_view import BaseView

# Accent color for borders/overlays
ACCENT = QColor("#E2742D")


# ===============================================================
# Label subclass that draws outlined text (stroke + fill)
# ===============================================================
class OutlinedLabel(QLabel):
    def __init__(self, *args, stroke_color=ACCENT,
                 text_color=QColor(255, 255, 255), stroke_thickness=3, **kwargs):
        super().__init__(*args, **kwargs)
        self._stroke = stroke_color
        self._fill = text_color
        self._thick = stroke_thickness
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, e):
        """Draw text with a colored stroke around it."""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.TextAntialiasing, True)
        text = self.text()
        rect = self.rect()
        flags = self.alignment()
        if self.wordWrap():
            flags |= Qt.TextWordWrap

        # Stroke pass
        p.setPen(self._stroke)
        for dx in (-self._thick, 0, self._thick):
            for dy in (-self._thick, 0, self._thick):
                if dx == 0 and dy == 0:
                    continue
                p.drawText(rect.adjusted(dx, dy, dx, dy), flags, text)

        # Fill pass
        p.setPen(self._fill)
        p.drawText(rect, flags, text)


# ===============================================================
# HomeView
# ===============================================================
class HomeView(BaseView):
    """
    Home tab view.

    Layout:
    - Left column: greeting header + recommended recipes (cards).
    - Right column: "Tip of the Day" (AI cooking tip).
    """

    def __init__(self, username, go_to_search_callback):
        super().__init__()
        self.setObjectName("HomeTab")

        self.username = username
        self.go_to_search_callback = go_to_search_callback

        # === Root layout ===
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(60, 40, 80, 40)
        main_layout.setSpacing(24)

        content_row = QHBoxLayout()
        content_row.setSpacing(30)

        # -----------------------------------------------------------
        # Left column: Greeting + Recommendations
        # -----------------------------------------------------------
        left_col = QVBoxLayout()
        left_col.setSpacing(16)

        # Greeting box (click → go to search)
        greeting_box = QFrame()
        greeting_box.setObjectName("GreetingBox")
        greeting_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        greeting_box.setFixedHeight(180)
        greeting_box.setCursor(Qt.PointingHandCursor)
        greeting_box.mousePressEvent = lambda e: self.go_to_search_callback()

        greeting_layout = QVBoxLayout(greeting_box)
        greeting_layout.setContentsMargins(15, 15, 15, 15)
        greeting_layout.setSpacing(10)
        greeting_layout.setAlignment(Qt.AlignCenter)

        hello_label = QLabel(f"Hello, {self.username}!")
        hello_label.setObjectName("GreetingTitle")
        hello_label.setAlignment(Qt.AlignCenter)
        hello_label.setStyleSheet("font-size: 38px; font-weight: 900;")

        subtitle = QLabel("Click here to search for recipes by ingredients you already have")
        subtitle.setWordWrap(True)
        subtitle.setObjectName("GreetingSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 24px; font-weight: 700;")

        greeting_layout.addWidget(hello_label)
        greeting_layout.addWidget(subtitle)
        left_col.addWidget(greeting_box)

        # Container for recommended recipe cards
        self._recent_frame = QFrame()
        self._recent_frame.setObjectName("RecentRecipesBox")
        self._recent_frame.setStyleSheet("background: transparent; border: none;")
        self._recent_layout = QHBoxLayout(self._recent_frame)
        self._recent_layout.setSpacing(22)
        self._recent_layout.setContentsMargins(24, 0, 24, 0)
        self._recent_layout.setAlignment(Qt.AlignHCenter)
        left_col.addWidget(self._recent_frame, 1)

        # -----------------------------------------------------------
        # Right column: AI Tip box
        # -----------------------------------------------------------
        right_col = QVBoxLayout()
        right_col.setSpacing(8)
        right_col.setContentsMargins(0, 0, 0, 0)

        # Spacer to align top of tip box with greeting height
        spacer_top_h = greeting_box.sizeHint().height() + left_col.spacing()
        right_col.addSpacerItem(QSpacerItem(0, spacer_top_h, QSizePolicy.Minimum, QSizePolicy.Fixed))

        tip_box = QFrame()
        tip_box.setObjectName("AITipBox")
        tip_box.setMaximumWidth(340)
        tip_box.setMinimumWidth(280)
        tip_box.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        tip_box.setStyleSheet("padding: 6px;")

        tip_layout = QVBoxLayout(tip_box)
        tip_layout.setContentsMargins(8, 8, 8, 8)
        tip_layout.setSpacing(6)

        tip_title = QLabel("🌿 Tip of the Day")
        tip_title.setObjectName("AITipTitle")
        tip_title.setStyleSheet("font-size: 24px; font-weight: 900; margin: 0;")

        self.tip_label = QLabel("Loading tip...")
        self.tip_label.setObjectName("AITipText")
        self.tip_label.setWordWrap(True)
        self.tip_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.tip_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tip_label.setStyleSheet("font-size: 18px; line-height: 1.3; margin: 0;")

        tip_layout.addWidget(tip_title, 0, Qt.AlignTop)
        tip_layout.addWidget(self.tip_label, 1)
        right_col.addWidget(tip_box, 1)

        # Add columns to row
        content_row.addLayout(left_col, 6)
        content_row.addLayout(right_col, 1)

        main_layout.addLayout(content_row)

    # ===============================================================
    # Public API
    # ===============================================================
    def clear_recommendations(self):
        """Clear all recommendation cards."""
        while (item := self._recent_layout.takeAt(0)) is not None:
            w = item.widget()
            if w:
                w.deleteLater()

    def add_error_label(self, text: str):
        """Show an error message in place of recipe cards."""
        lbl = QLabel(text)
        self._recent_layout.addWidget(lbl, 0, Qt.AlignHCenter)

    def add_recommendation_card(self, recipe: dict, pixmap: QPixmap | None, on_click):
        """
        Add a clickable recommendation card with rounded image + overlay label.
        """
        img_size = 240
        radius   = 22
        stroke   = 2

        img_box = QFrame()
        img_box.setObjectName("RecipeItemBox")
        img_box.setFrameShape(QFrame.NoFrame)
        img_box.setStyleSheet("background: transparent; border: none;")
        img_box.setFixedSize(img_size, img_size)
        img_box.setCursor(Qt.PointingHandCursor)
        img_box.mousePressEvent = lambda e, r=recipe: on_click(r)

        img_label = QLabel(img_box)
        img_label.setGeometry(0, 0, img_size, img_size)
        img_label.setAlignment(Qt.AlignCenter)

        if pixmap is not None and not pixmap.isNull():
            rounded = self._rounded_pixmap_with_border(pixmap, size=img_size, radius=radius, stroke=stroke)
            img_label.setPixmap(rounded)
        else:
            img_label.setText("Img\nError")
            img_label.setAlignment(Qt.AlignCenter)

        overlay = OutlinedLabel(
            recipe.get("name", ""),
            img_box,
            stroke_color=ACCENT,
            text_color=QColor(255, 255, 255),
            stroke_thickness=3,
        )
        overlay.setObjectName("RecipeOverlay")
        overlay.setAlignment(Qt.AlignCenter)
        overlay.setWordWrap(True)
        overlay.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        overlay.setStyleSheet("background: transparent; font-weight: 900; font-size: 14px;")
        overlay.setFixedWidth(img_size - 16)
        overlay.adjustSize()
        overlay.move((img_size - overlay.width()) // 2, img_size - overlay.height() - 10)

        self._recent_layout.addWidget(img_box, 0, Qt.AlignHCenter)

    # ===============================================================
    # Helpers
    # ===============================================================
    def _rounded_pixmap_with_border(self, pixmap: QPixmap, size=240, radius=22, stroke=2) -> QPixmap:
        """Return pixmap cropped to rounded rect with accent border."""
        result = QPixmap(size, size)
        result.fill(Qt.transparent)

        p = QPainter(result)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        path = QPainterPath()
        path.addRoundedRect(0, 0, size, size, radius, radius)
        p.setClipPath(path)

        scaled = pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        p.drawPixmap(0, 0, scaled)

        p.setClipping(False)
        pen = QPen(ACCENT)
        pen.setWidth(stroke)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        inset = stroke / 2.0
        p.drawRoundedRect(inset, inset, size - stroke, size - stroke, radius, radius)

        p.end()
        return result
