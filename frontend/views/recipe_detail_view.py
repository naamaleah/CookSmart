# frontend/views/recipe_detail_view.py
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QTextEdit,
    QFrame, QSizePolicy, QPushButton
)
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QFont, QFontMetrics
from presenters.recipe_detail_presenter import RecipeDetailPresenter
from views.base_view import BaseView
import math

class RecipeDetailView(BaseView):
    def __init__(self, recipe, token, on_favorites_changed=None):
        super().__init__()
        self.setWindowTitle(recipe['name'])
        self.setMinimumSize(900, 650)
        self.token = token
        self.on_favorites_changed = on_favorites_changed

        # UI elements populated by the presenter
        self.image_label = QLabel()
        self.ingredients_text = QTextEdit()
        self.title_label = QLabel()
        self._full_title = ""
        self.category_label = QLabel()
        self.area_label = QLabel()
        self.instructions_text = QTextEdit()

        # Favorite button (heart)
        self.favorite_btn = QPushButton("♡")
        self.favorite_btn.setCheckable(True)
        self.favorite_btn.setObjectName("FavoriteButton")
        self.favorite_btn.setToolTip("Add to favorites")
        self.favorite_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.favorite_btn.setStyleSheet("""
            QPushButton#FavoriteButton {
                border: none;
                background: transparent;
                font-size: 40px;
                padding: 0 10px;
                color: #5C3A1B;
            }
            QPushButton#FavoriteButton:checked {
                color: #E53935;
            }
        """)

        # --- Main layout ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(16)

        outer_row = QHBoxLayout()
        outer_row.setContentsMargins(0, 0, 0, 0)
        outer_row.setSpacing(0)

        container = QFrame()
        container.setObjectName("RecipeContainer")
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(24, 18, 24, 18)
        container_layout.setSpacing(16)

        outer_row.addWidget(container, stretch=2)
        outer_row.addStretch(1)
        main_layout.addLayout(outer_row)

        # Left column – image + ingredients
        left_col = QVBoxLayout()
        left_col.setSpacing(12)

        self.image_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.image_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        left_col.addWidget(self.image_label)

        ingredients_box = QFrame()
        ingredients_box.setObjectName("TextBox")
        ingredients_layout = QVBoxLayout(ingredients_box)
        ingredients_layout.setContentsMargins(18, 14, 18, 14)
        ingredients_layout.setSpacing(10)
        ing_label = QLabel("Ingredients")
        ing_label.setObjectName("SectionTitle")
        ingredients_layout.addWidget(ing_label)
        self.ingredients_text.setReadOnly(True)
        self.ingredients_text.setObjectName("TextBoxContent")
        self.ingredients_text.setMinimumHeight(120)
        ingredients_layout.addWidget(self.ingredients_text)
        left_col.addWidget(ingredients_box)

        container_layout.addLayout(left_col, stretch=1)

        # Right column – title, metadata, instructions
        right_col = QVBoxLayout()
        right_col.setSpacing(12)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)

        self.title_label.setObjectName("RecipeTitle")
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        f = QFont(self.title_label.font())
        f.setPointSize(28)
        f.setBold(True)
        self.title_label.setFont(f)
        self.title_label.setWordWrap(True)
        fm0 = QFontMetrics(self.title_label.font())
        self._title_two_lines_h = fm0.lineSpacing() * 2 + 6
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.title_label.setMaximumHeight(self._title_two_lines_h)

        title_row.addWidget(self.title_label, stretch=1)
        title_row.addSpacing(6)
        title_row.addWidget(self.favorite_btn, 0, Qt.AlignRight | Qt.AlignVCenter)
        right_col.addLayout(title_row)

        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 0, 0, 0)
        meta_row.setSpacing(8)
        self.category_label.setObjectName("RecipeMeta")
        self.area_label.setObjectName("RecipeMeta")
        meta_row.addWidget(self.category_label, 0, Qt.AlignLeft)
        meta_row.addStretch(1)
        meta_row.addWidget(self.area_label, 0, Qt.AlignRight)
        right_col.addLayout(meta_row)

        self.instructions_box = QFrame()
        self.instructions_box.setObjectName("TextBox")
        instructions_layout = QVBoxLayout(self.instructions_box)
        instructions_layout.setContentsMargins(10, 8, 10, 8)
        instructions_layout.setSpacing(6)
        instructions_label = QLabel("Preparation")
        instructions_label.setObjectName("SectionTitle")
        instructions_layout.addWidget(instructions_label)

        self.instructions_text.setReadOnly(True)
        self.instructions_text.setObjectName("TextBoxContent")
        self.instructions_text.setMinimumHeight(160)
        self.instructions_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        instructions_layout.addWidget(self.instructions_text)
        right_col.addWidget(self.instructions_box)

        container_layout.addLayout(right_col, stretch=4)

        # Presenter and bindings
        self.presenter = RecipeDetailPresenter(self, recipe, self.token, on_favorites_changed=self.on_favorites_changed)
        self.favorite_btn.toggled.connect(self.presenter.on_favorite_toggled)
        self.presenter.populate()

    # --- Interface for presenter (MVP pattern) ---
    def set_favorite_state(self, checked: bool):
        if self.favorite_btn.isChecked() != checked:
            self.favorite_btn.blockSignals(True)
            self.favorite_btn.setChecked(checked)
            self.favorite_btn.blockSignals(False)
        self.favorite_btn.setText("♥" if checked else "♡")
        self.favorite_btn.setToolTip("Remove from favorites" if checked else "Add to favorites")

    def set_title_text(self, text: str):
        self._full_title = text or ""
        self._fit_title()

    def _available_title_width(self) -> int:
        row_w = max(self.width() * 2 // 3, self.title_label.width(), 300)
        heart_w = self.favorite_btn.sizeHint().width()
        spacing = 16
        side_padding = 24
        return max(120, int(row_w - heart_w - spacing - side_padding))

    def _fit_title(self):
        if not self._full_title:
            self.title_label.setText("")
            return

        max_lines = 2
        max_pt = 28
        min_pt = 18
        avail = self._available_title_width()
        font = QFont(self.title_label.font())

        for pt in range(max_pt, min_pt - 1, -1):
            font.setPointSize(pt)
            fm = QFontMetrics(font)
            rect = fm.boundingRect(QRect(0, 0, avail, 10**6), Qt.TextWordWrap, self._full_title)
            lines = math.ceil(rect.height() / fm.lineSpacing())
            if lines <= max_lines and rect.height() <= self._title_two_lines_h:
                self.title_label.setFont(font)
                self.title_label.setText(self._full_title)
                self.title_label.setMaximumHeight(self._title_two_lines_h)
                return

        font.setPointSize(min_pt)
        self.title_label.setFont(font)
        self.title_label.setText(self._full_title)
        self.title_label.setMaximumHeight(self._title_two_lines_h)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._fit_title()
