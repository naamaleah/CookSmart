# frontend/views/add_recipe_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QComboBox, QFrame, QScrollArea
)
from PySide6.QtCore import Qt
from presenters.add_recipe_presenter import AddRecipePresenter
from views.base_view import BaseView

# External widget for creating ingredient tags
from utils.ingredient_tag import create_ingredient_tag as _create_tag


class AddRecipeView(BaseView):
    """
    View for adding a new recipe.
    Provides a three-column layout:
      - Left: General recipe information (name, category, area, thumbnail URL).
      - Center: Ingredients input and tag list.
      - Right: Instructions text area.
    Connected to `AddRecipePresenter` for business logic.
    """

    def __init__(self, token: str):
        super().__init__()
        self.token = token
        self.setWindowTitle("➕ Add New Recipe")
        self.setMinimumSize(950, 600)

        self.ingredients = []

        # Main container layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 40, 30, 20)
        main_layout.addSpacing(15)

        # === Title ===
        title = QLabel("Add New Recipe")
        title.setObjectName("RecipeTitle")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # === Main container ===
        container = QFrame()
        container.setObjectName("clear_frame")
        container_layout = QVBoxLayout(container)

        # --- Column headers row ---
        header_row = QHBoxLayout()
        header_row.setSpacing(24)
        header_row.addWidget(self._column_label("Recipe Info"), stretch=3)
        header_row.addWidget(self._column_label("Ingredients"), stretch=3)
        header_row.addWidget(self._column_label("Instructions"), stretch=3)
        container_layout.addLayout(header_row)

        # --- Content row ---
        content_row = QHBoxLayout()
        content_row.setSpacing(24)

        # ========== Left column – Recipe Info ==========
        left_col = QVBoxLayout()
        left_col.setSpacing(0)
        left_col.setAlignment(Qt.AlignTop)

        self.name_input = self._add_labeled_input(left_col, "Recipe Name:")
        left_col.addStretch(1)

        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        self.category_input.addItems([
            "Beef", "Breakfast", "Chicken", "Dessert", "Goat", "Lamb", "Miscellaneous",
            "Pasta", "Pork", "Seafood", "Side", "Starter", "Vegan", "Vegetarian",
            "Soup", "Salad", "Drink", "Bakery"
        ])
        self._add_labeled_widget(left_col, "Category:", self.category_input)
        left_col.addStretch(1)

        self.area_input = QComboBox()
        self.area_input.setEditable(True)
        self.area_input.addItems([
            "American", "British", "Canadian", "Chinese", "Croatian", "Dutch", "Egyptian",
            "Filipino", "French", "Greek", "Indian", "Irish", "Italian", "Jamaican",
            "Japan", "Japanese", "Kenyan", "Malaysian", "Mexican", "Middle Eastern",
            "Moroccan", "Polish", "Portuguese", "Russian", "Spanish", "Thai",
            "Tunisian", "Turkish", "Uruguayan", "Vietnamese"
        ])
        self._add_labeled_widget(left_col, "Area:", self.area_input)
        left_col.addStretch(1)

        self.thumbnail_input = self._add_labeled_input(left_col, "Image URL:")
        left_col.addStretch(3)

        content_row.addLayout(left_col, stretch=3)

        # ========== Center column – Ingredients ==========
        center_col = QVBoxLayout()
        center_col.setSpacing(16)

        # Ingredient input row
        input_row = QHBoxLayout()
        self.ingredient_input = QLineEdit()
        self.ingredient_input.setPlaceholderText("Type an ingredient")
        input_row.addWidget(self.ingredient_input)

        self.add_btn = QPushButton("+")
        input_row.addWidget(self.add_btn)
        center_col.addLayout(input_row)

        # Ingredient list area
        self.ingredient_area = QScrollArea()
        self.ingredient_area.setMinimumHeight(220)
        self.ingredient_area.setWidgetResizable(True)

        self.ingredient_widget = QWidget()
        self.ingredient_layout = QVBoxLayout(self.ingredient_widget)
        self.ingredient_layout.setAlignment(Qt.AlignTop)
        self.ingredient_area.setWidget(self.ingredient_widget)
        center_col.addWidget(self.ingredient_area)

        content_row.addLayout(center_col, stretch=3)

        # ========== Right column – Instructions ==========
        right_col = QVBoxLayout()
        right_col.setSpacing(16)

        self.instructions_input = QTextEdit()
        right_col.addWidget(self.instructions_input)
        content_row.addLayout(right_col, stretch=3)

        container_layout.addLayout(content_row)
        main_layout.addWidget(container)

        # --- Submit button ---
        self.submit_btn = QPushButton("Add Recipe")
        main_layout.addWidget(self.submit_btn, alignment=Qt.AlignCenter)

        # --- Connect presenter ---
        self.presenter = AddRecipePresenter(self, token)
        self.add_btn.clicked.connect(self.presenter.add_ingredient)
        self.ingredient_input.returnPressed.connect(self.presenter.add_ingredient)
        self.submit_btn.clicked.connect(self.presenter.submit_recipe)

    # --- Helper wrappers ---
    def _add_labeled_input(self, layout, label_text: str) -> QLineEdit:
        """Add a labeled QLineEdit to the given layout."""
        box = QVBoxLayout()
        label = QLabel(label_text)
        label.setStyleSheet("font-weight: bold; font-size: 13px;")
        field = QLineEdit()
        box.addWidget(label)
        box.addWidget(field)
        container = QFrame()
        container.setObjectName("totaly_clear_frame")
        container.setLayout(box)
        layout.addWidget(container)
        return field

    def _add_labeled_widget(self, layout, label_text: str, widget: QWidget) -> None:
        """Add a labeled widget (e.g., QComboBox) to the given layout."""
        box = QVBoxLayout()
        label = QLabel(label_text)
        label.setStyleSheet("font-weight: bold; font-size: 13px;")
        box.addWidget(label)
        box.addWidget(widget)
        container = QFrame()
        container.setObjectName("totaly_clear_frame")
        container.setLayout(box)
        layout.addWidget(container)

    def _column_label(self, text: str) -> QLabel:
        """Create a bold column header label."""
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-weight: bold; font-size: 16px; padding-bottom: 6px;")
        return label

    # Wrapper to prevent presenter breakage
    def create_ingredient_tag(self, ingredient_name: str, remove_callback) -> QFrame:
        """Delegate ingredient tag creation to the shared widget factory."""
        return _create_tag(ingredient_name, remove_callback)

    # --- Reset form ---
    def reset_form(self) -> None:
        """Clear all inputs and reset the form state."""
        self.name_input.clear()
        self.thumbnail_input.clear()
        self.instructions_input.clear()
        self.category_input.setCurrentIndex(-1)
        self.category_input.setCurrentText("")
        self.area_input.setCurrentIndex(-1)
        self.area_input.setCurrentText("")

        # Clear ingredient tags
        layout = self.ingredient_layout
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.name_input.setFocus()
        self.ingredient_area.verticalScrollBar().setValue(0)
