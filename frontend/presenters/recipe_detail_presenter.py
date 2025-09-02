# frontend/presenters/recipe_detail_presenter.py
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from typing import Callable, Optional

from services.api import add_to_favorites, remove_from_favorites, get_favorites
from utils.images import get_pixmap_or_default


class RecipeDetailPresenter:
    """
    Presenter for the recipe detail screen.
    Responsible for:
    - Populating recipe information into the view.
    - Managing favorite state and synchronization with the server.
    """
    def __init__(self, view, recipe, token: str,
                 on_favorites_changed: Optional[Callable[[], None]] = None):
        self.view = view
        self.recipe = recipe
        self.token = token
        self.on_favorites_changed = on_favorites_changed
        self.recipe_id = int(recipe.get("recipeid") or recipe.get("id") or 0)

        # Initial favorite state (may be overridden after server check)
        self.is_favorite = bool(recipe.get("is_favorite", False))

    # ----- Populate View -----
    def populate(self):
        """Fill the view with recipe data and update favorite state."""
        self.set_image()
        self.set_ingredients()
        self.set_title_and_info()
        self.set_instructions()

        # If favorite state is not provided, validate with server
        if "is_favorite" not in self.recipe and self.recipe_id:
            self._refresh_favorite_from_server()
        else:
            self.view.set_favorite_state(self.is_favorite)

    def _refresh_favorite_from_server(self):
        """Check with the server whether this recipe is currently a favorite."""
        try:
            favs = get_favorites(self.token) or []
            ids = {int(x.get("recipeid", -1)) for x in favs}
            self.is_favorite = self.recipe_id in ids
            self.view.set_favorite_state(self.is_favorite)
        except Exception:
            # Fallback to last known state
            self.view.set_favorite_state(self.is_favorite)

    def set_image(self):
        """Set the recipe thumbnail image."""
        pixmap = get_pixmap_or_default(self.recipe.get("thumbnail_url"), size=(250, 250))
        self.view.image_label.setPixmap(pixmap)

    def set_ingredients(self):
        """Populate the ingredients list in the view."""
        ingredients = self.recipe.get("ingredients", [])
        self.view.ingredients_text.setPlainText("\n".join(ingredients))

    def set_title_and_info(self):
        """Set the recipe title, category, and area."""
        self.view.set_title_text(self.recipe.get("name", ""))
        category = self.recipe.get("category", "N/A")
        area = self.recipe.get("area", "N/A")
        self.view.category_label.setText(f"<b>Category:</b> {category}")
        self.view.area_label.setText(f"<b>Area:</b> {area}")

    def set_instructions(self):
        """Populate the recipe instructions in the view."""
        instructions = self.recipe.get("instructions") or ""
        self.view.instructions_text.setPlainText(instructions)

    # ----- Favorites -----
    def on_favorite_toggled(self, checked: bool):
        """
        Handle toggle of the favorite button.
        Calls the API to add/remove favorites and updates the view state.
        """
        if not self.recipe_id:
            self.view.set_favorite_state(self.is_favorite)
            self.view.alert_error("Favorites", "Missing recipe id.")
            return

        self.view.favorite_btn.setEnabled(False)
        try:
            if checked:
                ok, msg = add_to_favorites(self.token, self.recipe_id)
                if ok:
                    self.is_favorite = True
                    self.view.set_favorite_state(True)
                    if self.on_favorites_changed:
                        self.on_favorites_changed()
                else:
                    self.view.set_favorite_state(self.is_favorite)
                    self.view.alert_error("Favorites", msg or "Failed to add to favorites")
            else:
                ok, msg = remove_from_favorites(self.token, self.recipe_id)
                if ok:
                    self.is_favorite = False
                    self.view.set_favorite_state(False)
                    if self.on_favorites_changed:
                        self.on_favorites_changed()
                else:
                    self.view.set_favorite_state(self.is_favorite)
                    self.view.alert_error("Favorites", msg or "Failed to remove from favorites")
        except Exception as e:
            self.view.set_favorite_state(self.is_favorite)
            self.view.alert_error("Favorites", f"Failed to update favorites: {e}")
        finally:
            self.view.favorite_btn.setEnabled(True)
