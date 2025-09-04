# frontend/presenters/add_recipe_presenter.py
from services.api import add_recipe, upload_image
from utils.ingredients import IngredientManager
from utils.message_box import MessageBox

class AddRecipePresenter:
    def __init__(self, view, token):
        self.view = view
        self.token = token
        self.ingredients_mgr = IngredientManager(
            layout=self.view.ingredient_layout,
            create_tag_fn=self.view.create_ingredient_tag,
            on_remove=self._remove_ingredient,
        )

    def add_ingredient(self):
        text = self.view.ingredient_input.text().strip()
        if self.ingredients_mgr.add(text):
            self.view.ingredient_input.clear()

    def _remove_ingredient(self, ing: str):
        self.ingredients_mgr.remove(ing)

    def submit_recipe(self):
        name = self.view.name_input.text().strip()
        category = self.view.category_input.currentText().strip()
        area = self.view.area_input.currentText().strip()
        instructions = self.view.instructions_input.toPlainText().strip()
        thumbnail_url = self.view.thumbnail_input.text().strip()
        ingredients = self.ingredients_mgr.items()
        image_path = self.view.image_path

        if not all([name, category, area, instructions]) or not ingredients:
            MessageBox.show_info(self.view, "Please fill in all fields and add ingredients.")
            return

        # If user selected a file, upload it first
        if image_path:
            success, url_or_err = upload_image(self.token, image_path)
            if not success:
                MessageBox.show_error(self.view, f"Image upload failed: {url_or_err}")
                return
            thumbnail_url = url_or_err

        success, msg = add_recipe(
            token=self.token,
            name=name,
            category=category,
            area=area,
            instructions=instructions,
            thumbnail_url=thumbnail_url,
            ingredients=ingredients,
        )

        if success:
            MessageBox.show_success(self.view, "Recipe added successfully!")
            self.ingredients_mgr.clear()
            self.view.reset_form()
        else:
            MessageBox.show_error(self.view, f"Failed to add recipe: {msg}")
