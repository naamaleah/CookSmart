# backend/services/recipes_command_service.py
from backend.db.db_config import get_connection
from pydantic import BaseModel
from typing import List
from .event_store import append_event


class NewRecipe(BaseModel):
    """Pydantic model representing a new recipe."""
    name: str
    category: str
    area: str
    instructions: str
    thumbnail_url: str
    ingredients: List[str]


def add_recipe(recipe: NewRecipe):
    """
    Add a new recipe to the database.
    Uses event sourcing: projection (insert into recipes) + append event.
    Returns the new recipe ID and confirmation message.
    """
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        ing_str = ", ".join(ing.strip() for ing in recipe.ingredients)

        # Insert recipe and return generated ID
        cur.execute("""
            INSERT INTO recipes (name, category, area, instructions, thumbnail_url, ingredients)
            OUTPUT INSERTED.recipeid
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            recipe.name,
            recipe.category,
            recipe.area,
            recipe.instructions,
            recipe.thumbnail_url,
            ing_str
        ))
        recipe_id = int(cur.fetchone()[0])

        # Append event to event store
        append_event(
            conn,
            aggregate_type="recipe",
            aggregate_id=recipe_id,
            event_type="RECIPE_ADDED",
            payload={
                "name": recipe.name,
                "category": recipe.category,
                "area": recipe.area,
                "thumbnail_url": recipe.thumbnail_url,
                "ingredients": recipe.ingredients,   # Save original list in JSON
                "instructions": recipe.instructions
            },
            user_id=None  # Optionally include user_id if available
        )

        conn.commit()
        return {"message": "Recipe added successfully!", "recipeid": recipe_id}

    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
