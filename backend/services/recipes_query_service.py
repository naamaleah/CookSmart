# backend/services/recipes_query_service.py
from fastapi import HTTPException
from backend.db.db_config import get_connection

def search_recipes(name=None, category=None, area=None):
    """
    Search recipes with optional filters: name (LIKE), category, and area.
    Returns a list of recipe details.
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT RecipeID, Name, Category, Area, Instructions, Thumbnail_URL, Ingredients FROM recipes WHERE 1=1"
    params = []

    if name:
        query += " AND Name LIKE ?"
        params.append(f"%{name}%")
    if category:
        query += " AND Category = ?"
        params.append(category)
    if area:
        query += " AND Area = ?"
        params.append(area)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return [
        {
            "recipeid": row[0],
            "name": row[1],
            "category": row[2],
            "area": row[3],
            "thumbnail_url": row[5],
            "ingredients": row[6].split(", ") if row[6] else [],
            "instructions": row[4] if row[4] else ""
        }
        for row in rows
    ]

def search_by_ingredients(ingredients):
    """
    Search recipes based on a list of ingredients.
    Returns detailed recipe info including match_count for sorting relevance.
    Case-insensitive matching.
    """
    try:
        # Normalize ingredient list
        norm_ings = [ing.strip().lower() for ing in (ingredients or []) if ing and ing.strip()]
        if not norm_ings:
            return []

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT recipeid, name, category, area, thumbnail_url, ingredients, instructions
            FROM recipes
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        results = []
        for row in rows:
            recipeid, name, category, area, thumbnail_url, ing_str, instructions = row
            ing_text = (ing_str or "").lower()

            # Count ingredient matches
            match_count = sum(1 for ing in norm_ings if ing in ing_text)
            if match_count > 0:
                results.append({
                    "recipeid": recipeid,
                    "name": name,
                    "category": category,
                    "area": area,
                    "thumbnail_url": thumbnail_url,
                    "ingredients": ing_str.split(", ") if ing_str else [],
                    "instructions": instructions or "",
                    "match_count": match_count,
                })

        # Sort by relevance (number of matches)
        results.sort(key=lambda x: x["match_count"], reverse=True)
        return results

    except Exception as e:
        return {"error": str(e)}


def get_recipe_details(recipeid):
    """
    Retrieve detailed information about a specific recipe by its ID.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT RecipeID, Name, Category, Area, Instructions, Thumbnail_URL, Ingredients
        FROM recipes
        WHERE RecipeID = ?
    """, (recipeid,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Recipe not found")

    return {
        "recipeid": row[0],
        "name": row[1],
        "category": row[2],
        "area": row[3],
        "instructions": row[4],
        "thumbnail_url": row[5],
        "ingredients": row[6].split(", ") if row[6] else []
    }

def recommend_recipes(userid):
    """
    Recommend up to 3 random recipes not already in the user's favorites.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT TOP 3 recipeid, name, category, area, thumbnail_url, ingredients, instructions
            FROM recipes
            WHERE recipeid NOT IN (
                SELECT recipeid FROM favorites WHERE userid = ?
            )
            ORDER BY NEWID();
        """, (userid,))

        rows = cursor.fetchall()
        return [
            {
                "recipeid": r[0],
                "name": r[1],
                "category": r[2],
                "area": r[3],
                "thumbnail_url": r[4],
                "ingredients": r[5].split(", ") if r[5] else [],
                "instructions": r[6] if r[6] else ""
            }
            for r in rows
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get random recommendations")

    finally:
        cursor.close()
        conn.close()