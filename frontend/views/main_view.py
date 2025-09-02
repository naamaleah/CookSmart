# File: frontend/views/main_view.py
from PySide6.QtWidgets import (
    QWidget, QTabBar, QTabWidget, QPushButton, QVBoxLayout, QMainWindow
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

from views.home_view import HomeView
from presenters.home_presenter import HomePresenter
from views.search_view import SearchView
from views.favorites_view import FavoritesView
from views.add_recipe_view import AddRecipeView
from views.recipe_detail_view import RecipeDetailView
from utils.ai_chat_button import AIChatButton


class MainWindow(QMainWindow):
    """
    Main application window.
    - Contains fixed tabs: Home, Search, Favorites, Add.
    - Allows dynamic tabs for recipe details.
    - Provides floating action buttons: Logout & AI Assistant.
    """

    FIXED_TABS_COUNT = 4

    def __init__(self, token, logout_callback, userid: int = 1, username: str = "User"):
        super().__init__()
        self.token = token
        self.logout_callback = logout_callback
        self.userid = userid
        self.username = username

        # --- Window setup ---
        self.setWindowTitle("CookSmart")
        self.setMinimumSize(900, 600)

        # Central widget + layout
        central_widget = QWidget()  # could also use BaseView() for background
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Tabs ---
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)

        tab_bar = self.tabs.tabBar()
        tab_bar.setElideMode(Qt.ElideRight)
        tab_bar.setMovable(False)

        # Home tab
        self.home_view = HomeView(self.username, self.go_to_ingredient_search)
        self.home_presenter = HomePresenter(
            self.home_view, self.token, self.userid, self.open_recipe_detail
        )
        self.home_presenter.init_ui()
        self.tabs.addTab(self.home_view, "Home")

        # Search tab
        self.search_tab = SearchView(self.token, self.tabs)
        self.tabs.addTab(self.search_tab, "Search")

        # Favorites tab
        self.favorites_tab = FavoritesView(self.token, self)
        self.tabs.addTab(self.favorites_tab, "Favorites")

        # Add Recipe tab
        self.tabs.addTab(AddRecipeView(self.token), "Add")

        # Prevent closing fixed tabs
        for i in range(self.FIXED_TABS_COUNT):
            tab_bar.setTabButton(i, QTabBar.RightSide, None)

        self.tabs.currentChanged.connect(self.on_tab_changed)
        main_layout.addWidget(self.tabs)

        # --- Floating buttons ---
        self._setup_logout_button()
        self.ai_button_widget = AIChatButton(self, self.token)
        self.ai_button_widget.move(20, self.height() - 80)
        self.ai_button_widget.show()

    # ================== UI Helpers ==================
    def _setup_logout_button(self):
        """Create and style the floating logout button."""
        self.logout_floating_btn = QPushButton(self)
        self.logout_floating_btn.setIcon(QIcon.fromTheme("application-exit"))
        self.logout_floating_btn.setToolTip("Logout")
        self.logout_floating_btn.setCursor(Qt.PointingHandCursor)
        self.logout_floating_btn.setFixedSize(48, 48)
        self.logout_floating_btn.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 24px;
                background-color: #f44336;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        self.logout_floating_btn.clicked.connect(self.logout)
        self.update_logout_button_position()
        self.resizeEvent = self.on_resize

    def update_logout_button_position(self):
        margin = 20
        x = self.width() - self.logout_floating_btn.width() - margin
        y = self.height() - self.logout_floating_btn.height() - margin
        self.logout_floating_btn.move(x, y)

    def on_resize(self, event):
        self.update_logout_button_position()
        return super().resizeEvent(event)

    # ================== Actions ==================
    def logout(self):
        self.close()
        self.logout_callback()

    def close_tab(self, index):
        """Close only dynamic tabs (not fixed tabs)."""
        if index < self.FIXED_TABS_COUNT:
            return
        self.tabs.removeTab(index)

    def _on_favorites_changed(self):
        """Mark favorites as dirty and refresh if active tab."""
        if hasattr(self.favorites_tab, "mark_dirty"):
            self.favorites_tab.mark_dirty()

        idx = self.tabs.currentIndex()
        widget = self.tabs.widget(idx)
        if widget is self.favorites_tab and hasattr(self.favorites_tab, "load_favorites"):
            self.favorites_tab.load_favorites()

    def open_recipe_detail(self, recipe: dict):
        """Open a recipe detail tab (re-use if already open)."""
        title = recipe["name"]
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == title:
                self.tabs.setCurrentIndex(i)
                return

        view = RecipeDetailView(recipe, self.token, on_favorites_changed=self._on_favorites_changed)
        self.tabs.addTab(view, title)
        self.tabs.setCurrentWidget(view)

    def go_to_ingredient_search(self):
        """Switch to the search tab and focus ingredient input if exists."""
        self.tabs.setCurrentIndex(1)
        if hasattr(self.search_tab, "ing_input"):
            self.search_tab.ing_input.setFocus()

    def on_tab_changed(self, index):
        """Auto-refresh Favorites when its tab is selected."""
        if self.tabs.tabText(index) == "Favorites":
            if hasattr(self.favorites_tab, "load_favorites"):
                self.favorites_tab.load_favorites()
