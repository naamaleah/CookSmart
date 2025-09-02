# frontend/views/favorites_view.pyy
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea,
    QFrame, QGridLayout
)
from PySide6.QtCore import Qt
from presenters.favorites_presenter import FavoritesPresenter
from views.base_view import BaseView


class FavoritesView(BaseView):
    """
    View for displaying the user's list of favorite recipes.

    Features:
    - Title header ("Your Favorite Recipes").
    - Scrollable grid layout of recipe cards (3 columns).
    - Integrates with FavoritesPresenter to fetch and display data.
    - Supports a 'dirty flag' to mark when the tab needs to refresh
      (e.g., after a recipe is added/removed from favorites).
    """

    def __init__(self, token, main_window):
        """
        Initialize the favorites view.

        Args:
            token (str): Authentication token (JWT).
            main_window (QWidget): Reference to the main window
                                   (used for opening recipe detail views).
        """
        super().__init__()
        self.token = token
        self.main_window = main_window
        self._dirty = False  # Tracks if the tab needs refresh

        self.setWindowTitle("📋 My Favorites")
        self.setMinimumSize(600, 500)

        # === Main layout ===
        self.main_layout = QVBoxLayout()

        # Title
        title = QLabel("❤️ Your Favorite Recipes")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("FavoritesTitle")
        self.main_layout.addWidget(title)

        # Scrollable grid container
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.container = QFrame()
        self.container.setObjectName("clear_frame")
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setContentsMargins(20, 20, 20, 20)

        self.scroll_area.setWidget(self.container)
        self.main_layout.addWidget(self.scroll_area)
        self.setLayout(self.main_layout)

        # Presenter (handles API + rendering)
        self.presenter = FavoritesPresenter(self, token, main_window)

        # Initial load
        self.presenter.load_favorites()

    # --- Public API ---

    def load_favorites(self):
        """Explicitly trigger reload of favorites via the presenter."""
        self.presenter.load_favorites()

    def mark_dirty(self):
        """
        Mark this view as 'dirty' (stale data).
        When shown again, it will refresh automatically.
        """
        self._dirty = True

    # --- Qt Events ---

    def showEvent(self, e):
        """
        If the tab is shown and marked dirty, refresh favorites.
        """
        super().showEvent(e)
        if self._dirty:
            self._dirty = False
            self.presenter.load_favorites()
