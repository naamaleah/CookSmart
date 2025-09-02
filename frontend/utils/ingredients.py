# frontend/utils/ingredients.py
from __future__ import annotations
from typing import Callable, List, Optional
from PySide6.QtWidgets import QLayout


def clear_layout(layout: QLayout) -> None:
    """
    Remove and safely delete all widgets from a given Qt layout.

    Args:
        layout: The QLayout whose child widgets should be removed.
    """
    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        if w:
            w.deleteLater()


class IngredientManager:
    """
    Helper class to manage a unique list of ingredients and render them as tags in a layout.

    This class abstracts away the logic for:
    - Keeping an internal list of unique ingredient strings.
    - Rendering ingredient tags inside a given QLayout.
    - Handling add/remove/clear operations consistently.

    The actual tag widget creation is delegated to `create_tag_fn`,
    which must accept `(ingredient_name, remove_callback)` and return a QWidget-like object.
    """

    def __init__(
        self,
        layout: QLayout,
        create_tag_fn: Callable[[str, Callable[..., None]], object],
        on_remove: Callable[[str], None],
    ) -> None:
        """
        Args:
            layout: The target layout where ingredient tags will be rendered.
            create_tag_fn: Function to create a tag widget for a given ingredient.
                           Signature: (ingredient_name: str, remove_callback: Callable) -> QWidget
            on_remove: Callback to be called when a tag is removed.
        """
        self._ingredients: List[str] = []
        self._layout = layout
        self._create_tag = create_tag_fn
        self._on_remove = on_remove

    # ---- Data API ----
    def items(self) -> List[str]:
        """Return a copy of the current list of ingredients."""
        return list(self._ingredients)

    def add(self, text: Optional[str]) -> bool:
        """
        Add a new ingredient if it is non-empty and not already present.

        Args:
            text: The ingredient string to add.

        Returns:
            True if the ingredient was added, False otherwise.
        """
        t = (text or "").strip()
        if not t or t in self._ingredients:
            return False
        self._ingredients.append(t)
        self.refresh()
        return True

    def remove(self, ing: str) -> bool:
        """
        Remove an ingredient by name.

        Args:
            ing: Ingredient string to remove.

        Returns:
            True if the ingredient was removed, False if not found.
        """
        if ing in self._ingredients:
            self._ingredients.remove(ing)
            self.refresh()
            return True
        return False

    def clear(self) -> None:
        """Clear all ingredients and remove all tag widgets from the layout."""
        self._ingredients.clear()
        clear_layout(self._layout)

    # ---- UI ----
    def refresh(self) -> None:
        """
        Rebuild the tag widgets inside the managed layout.
        This clears the layout first, then re-adds tags for each ingredient.
        """
        clear_layout(self._layout)
        for ing in self._ingredients:
            # Use a lambda with default argument to bind the correct ingredient for removal
            tag = self._create_tag(ing, lambda _=None, i=ing: self._on_remove(i))
            self._layout.addWidget(tag)
