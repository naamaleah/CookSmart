# frontend/presenters/add_recipe_presenter.py
from services.api import add_recipe
from utils.ingredients import IngredientManager
from utils.message_box import MessageBox


class AddRecipePresenter:
    def __init__(self, view, token):
        self.view = view
        self.token = token

        # Manage ingredients list and tag rendering via IngredientManager
        self.ingredients_mgr = IngredientManager(
            layout=self.view.ingredient_layout,
            create_tag_fn=self.view.create_ingredient_tag,
            on_remove=self._remove_ingredient,
        )

    # ----- Ingredients Management -----
    def add_ingredient(self):
        """Add an ingredient from the input field to the ingredient manager."""
        text = self.view.ingredient_input.text().strip()
        if self.ingredients_mgr.add(text):
            self.view.ingredient_input.clear()

    def _remove_ingredient(self, ing: str):
        """Remove an ingredient from the ingredient manager."""
        self.ingredients_mgr.remove(ing)

    # ----- Recipe Submission -----
    def submit_recipe(self):
        """
        Collect form data, validate fields, and attempt to add a recipe
        via the API. Provides user feedback through MessageBox.
        """
        name = self.view.name_input.text().strip()
        category = self.view.category_input.currentText().strip()
        area = self.view.area_input.currentText().strip()
        instructions = self.view.instructions_input.toPlainText().strip()
        thumbnail_url = self.view.thumbnail_input.text().strip()
        ingredients = self.ingredients_mgr.items()

        # Validation
        if not all([name, category, area, instructions]) or not ingredients:
            MessageBox.show_info(self.view, "Please fill in all fields and add ingredients.")
            return

        # API call to add recipe
        success, msg = add_recipe(
            token=self.token,
            name=name,
            category=category,
            area=area,
            instructions=instructions,
            thumbnail_url=thumbnail_url,
            ingredients=ingredients,
        )

        # Feedback
        if success:
            MessageBox.show_success(self.view,  "Recipe added successfully!")
            # Reset presenter and view state
            self.ingredients_mgr.clear()
            self.view.reset_form()
        else:
            MessageBox.show_error(self.view, f"Failed to add recipe: {msg}")
