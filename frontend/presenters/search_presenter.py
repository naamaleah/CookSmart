# frontend/presenters/search_presenter.py
from PySide6.QtWidgets import QLabel, QTableWidgetItem
from PySide6.QtCore import Qt


from services.api import search_recipes, search_by_ingredients
from views.recipe_detail_view import RecipeDetailView
from utils.ingredients import IngredientManager
from utils.images import get_pixmap_or_default
from utils.message_box import MessageBox


class SearchPresenter:
    """
    Presenter for the search screen.
    Responsible for:
    - Managing search mode (by name or ingredients).
    - Handling user input and performing search queries.
    - Rendering search results into a table.
    - Opening detailed recipe views.
    """
    def __init__(self, view, token):
        self.view = view
        self.token = token
        self.current_recipes = []
        self.mode = "name"  # default search mode

        # Manage ingredients list and tag rendering
        self.ingredients_mgr = IngredientManager(
            layout=self.view.ingredient_layout,
            create_tag_fn=self.view.create_ingredient_tag,
            on_remove=self._remove_ingredient,
        )

    # ----- Mode -----
    def set_mode(self, mode: str):
        """Switch between search modes: 'name' or 'ingredients'."""
        if mode not in ("name", "ingredients"):
            return
        self.mode = mode
        self.view.update_search_mode(mode)

    # ----- Ingredients -----
    def add_ingredient(self):
        """Add an ingredient to the search criteria (ingredients mode only)."""
        if self.mode != "ingredients":
            return
        text = self.view.ingredient_input.text().strip()
        if self.ingredients_mgr.add(text):
            self.view.ingredient_input.clear()

    def _remove_ingredient(self, ing: str):
        """Remove an ingredient from the search criteria."""
        self.ingredients_mgr.remove(ing)

    # ----- Search -----
    def perform_search(self):
        """Perform a search by name or ingredients and display results."""
        self.view.results_table.setRowCount(0)

        if self.mode == "ingredients":
            ingredients = self.ingredients_mgr.items()
            if not ingredients:
                MessageBox.show_info(self.view, "Please add at least one ingredient.")
                return
            recipes = search_by_ingredients(ingredients)
        else:  # search by name
            query = self.view.name_input.text().strip()
            if not query:
                MessageBox.show_info(self.view,"Please enter a recipe name.")
                return
            recipes = search_recipes(query)

        if not recipes:
            MessageBox.show_info(self.view, "No recipes found.")
            return

        self.current_recipes = recipes
        table = self.view.results_table
        table.setRowCount(len(recipes))

        for row, r in enumerate(recipes):
            # Thumbnail image
            img_lbl = QLabel()
            img_lbl.setFixedSize(70, 70)
            img_lbl.setStyleSheet("border-radius:8px;border:1px solid #d6a28e;background:#f0eae5;")
            pix = get_pixmap_or_default(r.get("thumbnail_url"), size=(70, 70))
            img_lbl.setPixmap(pix)
            table.setCellWidget(row, 0, img_lbl)

            # Recipe details columns
            table.setItem(row, 1, QTableWidgetItem(r.get("name", "Unknown")))
            table.setItem(row, 2, QTableWidgetItem(r.get("category", "Unknown")))
            table.setItem(row, 3, QTableWidgetItem(r.get("area", "Unknown")))
            ingredients_txt = ", ".join(r.get("ingredients", []))
            table.setItem(row, 4, QTableWidgetItem(ingredients_txt))
            table.setRowHeight(row, 120)

    # ----- Details -----
    def show_recipe_details(self, row, _column):
        """Open the recipe detail view for the selected row."""
        name_item = self.view.results_table.item(row, 1)
        if not name_item:
            return
        recipe_name = name_item.text()
        recipe = next((r for r in self.current_recipes if r.get("name") == recipe_name), None)
        if recipe:
            if self.view.parent_tabs:
                title = recipe["name"]
                # Prevent duplicate tabs
                for i in range(self.view.parent_tabs.count()):
                    if self.view.parent_tabs.tabText(i) == title:
                        self.view.parent_tabs.setCurrentIndex(i)
                        return
                detail_view = RecipeDetailView(recipe, self.token)
                self.view.parent_tabs.addTab(detail_view, title)
                self.view.parent_tabs.setCurrentWidget(detail_view)
            else:
                detail = RecipeDetailView(recipe, self.token)
                detail.show()
