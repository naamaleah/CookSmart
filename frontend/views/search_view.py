# file: frontend/views/search_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QHBoxLayout, QScrollArea, QFrame,
    QTableWidget, QHeaderView
)
from PySide6.QtCore import Qt
from presenters.search_presenter import SearchPresenter
from views.base_view import BaseView
from utils.ingredient_tag import create_ingredient_tag  


class SearchView(BaseView):
    def __init__(self, token, parent_tabs=None):
        super().__init__()
        self.token = token
        self.parent_tabs = parent_tabs
        self.setWindowTitle("Recipe Search")
        self.setMinimumSize(800, 500)

        layout = QVBoxLayout(self)

        # ---- Search mode: two exclusive buttons ----
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Search Mode:"))

        self.mode_name_btn = QPushButton("By Name")
        self.mode_ing_btn = QPushButton("By Ingredients")

        for b in (self.mode_name_btn, self.mode_ing_btn):
            b.setCheckable(True)
            b.setObjectName("ModeButton")  # for QSS styling
            mode_layout.addWidget(b)

        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        # Name search input
        self.name_input = QLineEdit(placeholderText="e.g. Shakshuka")
        layout.addWidget(self.name_input)

        # Ingredients area
        inp_layout = QHBoxLayout()
        self.ingredient_input = QLineEdit(placeholderText="Enter an ingredient")
        inp_layout.addWidget(self.ingredient_input)
        self._add_btn = QPushButton("+")
        inp_layout.addWidget(self._add_btn)
        layout.addLayout(inp_layout)

        self.ingredient_area = QScrollArea(maximumHeight=60, widgetResizable=True)
        self.ingredient_container = QWidget()
        self.ingredient_layout = QHBoxLayout(self.ingredient_container)
        self.ingredient_layout.setAlignment(Qt.AlignLeft)
        self.ingredient_area.setWidget(self.ingredient_container)
        layout.addWidget(self.ingredient_area)

        # Search button
        self.search_btn = QPushButton("Search")
        layout.addWidget(self.search_btn)

        # Results table
        self.results_table = QTableWidget(columnCount=5)
        self.results_table.setHorizontalHeaderLabels(
            ["Image", "Name", "Category", "Origin", "Ingredients"]
        )
        self.results_table.setColumnWidth(0, 200)   # Image
        self.results_table.setColumnWidth(2, 150)   # Category
        self.results_table.setColumnWidth(3, 150)   # Origin
        header = self.results_table.horizontalHeader()

        # Prevent text truncation
        header.setTextElideMode(Qt.ElideNone)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Column resizing
        header.setSectionResizeMode(0, QHeaderView.Fixed)    # Image - fixed
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Name - stretch
        header.setSectionResizeMode(2, QHeaderView.Fixed)    # Category - fixed
        header.setSectionResizeMode(3, QHeaderView.Fixed)    # Origin - fixed
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Ingredients - stretch
        header.setStretchLastSection(True)

        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setShowGrid(False)
        layout.addWidget(self.results_table)

        # Presenter
        self.presenter = SearchPresenter(self, token)

        # Connect events
        self.mode_name_btn.clicked.connect(lambda: self.presenter.set_mode("name"))
        self.mode_ing_btn.clicked.connect(lambda: self.presenter.set_mode("ingredients"))
        self.search_btn.clicked.connect(self.presenter.perform_search)
        self.name_input.returnPressed.connect(self.presenter.perform_search)
        self.ingredient_input.returnPressed.connect(self.presenter.add_ingredient)
        self._add_btn.clicked.connect(self.presenter.add_ingredient)
        self.results_table.cellClicked.connect(self.presenter.show_recipe_details)

        # Default mode
        self.presenter.set_mode("name")

    # ----- Update UI according to search mode -----
    def update_search_mode(self, mode: str):
        by_ing = (mode == "ingredients")
        self.mode_ing_btn.setChecked(by_ing)
        self.mode_name_btn.setChecked(not by_ing)
        self.name_input.setVisible(not by_ing)
        self.ingredient_input.setVisible(by_ing)
        self._add_btn.setVisible(by_ing)
        self.ingredient_area.setVisible(by_ing)

    # ----- New: use the shared ingredient tag widget -----
    def create_ingredient_tag(self, ingredient_name: str, remove_callback) -> QFrame:
        return create_ingredient_tag(ingredient_name, remove_callback)
