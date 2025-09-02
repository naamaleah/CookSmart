# backend/services/favorites_query_service.py
from backend.db.db_config import get_connection

def get_user_favorites(current_user: str):
    """
    Retrieve all favorite recipes for the specified user.
    Returns a list of recipe details including id, name, instructions,
    thumbnail URL, ingredients, category, and area.
    """
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
        SELECT R.recipeid, R.name, R.instructions, R.thumbnail_url, R.ingredients, R.category, R.area
        FROM favorites F
        JOIN recipes R ON F.recipeid = R.recipeid
        JOIN users U ON F.userid = U.userid
        WHERE U.username = ?
        """, (current_user,))

        favorites = cur.fetchall()
        cur.close()
        conn.close()

        return [
            {
                "recipeid": row[0],
                "name": row[1],
                "instructions": row[2],
                "thumbnail_url": row[3],
                "ingredients": row[4].split(", ") if row[4] else [],
                "category": row[5],
                "area": row[6]
            }
            for row in favorites
        ]

    except Exception as e:
        return {"error": str(e)}
