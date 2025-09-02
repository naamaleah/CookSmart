# file: frontend/presenters/favorites_presenter.py
from PySide6.QtWidgets import QLabel, QVBoxLayout, QFrame, QWidget
from PySide6.QtCore import Qt

from services.api import get_favorites
from views.home_view import OutlinedLabel, ACCENT
from utils.images import get_pixmap_or_default, rounded_pixmap_with_border


class FavoritesPresenter:
    def __init__(self, view, token, main_window):
        self.view = view
        self.token = token
        self.main_window = main_window

        self.img_size = 240
        self.radius = 22
        self.stroke = 2

    # ===== API =====
    def load_favorites(self):
        layout = self.view.grid_layout

        # clear old
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        favorites = get_favorites(self.token)
        if not favorites:
            label = QLabel("🧺 You have no favorite recipes yet.\nStart exploring and add some delicious ideas!")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-size: 16px; margin-top: 40px; color: #555;")
            layout.addWidget(label, 0, 0, 1, 3, alignment=Qt.AlignCenter)
            return

        for index, recipe in enumerate(favorites):
            row = index // 3
            col = index % 3
            layout.addWidget(self._create_card(recipe), row, col, alignment=Qt.AlignHCenter)

    # ===== Card =====
    def _create_card(self, recipe: dict) -> QWidget:
        img_box = QFrame()
        img_box.setObjectName("FavoriteItemBox")
        img_box.setFrameShape(QFrame.NoFrame)
        img_box.setStyleSheet("background: transparent; border: none;")
        img_box.setFixedSize(self.img_size, self.img_size)

        # open details on click
        img_box.mousePressEvent = lambda e, r=recipe: self.main_window.open_recipe_detail(r)

        # image
        img_label = QLabel(img_box)
        img_label.setGeometry(0, 0, self.img_size, self.img_size)
        img_label.setAlignment(Qt.AlignCenter)

        pixmap = get_pixmap_or_default(recipe.get("thumbnail_url"),
                                       size=(self.img_size, self.img_size))
        rounded = rounded_pixmap_with_border(
            pixmap, size=self.img_size, radius=self.radius, stroke=self.stroke, color=ACCENT
        )
        img_label.setPixmap(rounded)

        # title overlay
        title = OutlinedLabel(
            recipe.get("name", ""),
            img_box,
            stroke_color=ACCENT,
            text_color=Qt.white,
            stroke_thickness=3,
        )
        title.setObjectName("RecipeOverlay")
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        title.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        title.setStyleSheet("background: transparent; font-weight: 900; font-size: 14px;")
        title.setFixedWidth(self.img_size - 16)
        title.adjustSize()
        title.move((self.img_size - title.width()) // 2, self.img_size - title.height() - 10)

        # wrapper
        wrapper = QFrame()
        wrapper.setFrameShape(QFrame.NoFrame)
        wrapper.setStyleSheet("background: transparent; border: none;")
        lay = QVBoxLayout(wrapper)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(img_box, 0, Qt.AlignHCenter)

        return wrapper
