# backend/services/favorites_command_service.py
from fastapi import HTTPException
from backend.db.db_config import get_connection
from .event_store import append_event


def add_favorite(recipeid: int, current_user: str):
    """
    Add a recipe to the user's favorites.
    Uses projection (insert if not exists) + append event.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT userid FROM users WHERE username = ?", (current_user,))
        result = cursor.fetchone()
        if not result:
            return {"error": "User not found"}
        userid = int(result[0])

        # Insert favorite only if it does not already exist
        cursor.execute("""
            IF NOT EXISTS (
                SELECT 1 FROM favorites
                WHERE userid = ? AND recipeid = ?
            )
            INSERT INTO favorites (userid, recipeid) VALUES (?, ?)
        """, (userid, recipeid, userid, recipeid))

        # Append event to event store
        append_event(
            conn,
            aggregate_type="favorite",
            aggregate_id=recipeid,  # could also use (user_id, recipe_id) but kept simple
            event_type="FAVORITE_ADDED",
            payload={"user_id": userid, "recipe_id": recipeid},
            user_id=userid
        )

        conn.commit()
        return {"message": "Favorite added successfully"}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def remove_favorite(recipeid: int, current_user: str):
    """
    Remove a recipe from the user's favorites.
    Uses projection (delete) + append event if a record was actually removed.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT userid FROM users WHERE username = ?", (current_user,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        userid = int(result[0])

        # Delete favorite
        cursor.execute("DELETE FROM favorites WHERE userid = ? AND recipeid = ?", (userid, recipeid))
        deleted = cursor.rowcount or 0

        # Append event only if a record was deleted
        if deleted > 0:
            append_event(
                conn,
                aggregate_type="favorite",
                aggregate_id=recipeid,
                event_type="FAVORITE_REMOVED",
                payload={"user_id": userid, "recipe_id": recipeid},
                user_id=userid
            )

        conn.commit()
        return {"message": "Favorite removed successfully", "deleted": deleted}
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()