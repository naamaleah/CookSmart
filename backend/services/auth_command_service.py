# backend/services/auth_command_service.py
from fastapi import HTTPException
from backend.db.db_config import get_connection
from backend.utils.auth_utils import create_access_token, hash_password
from .event_store import append_event


def login_user(username: str, password: str):
    """
    Authenticate a user by verifying username and password.
    Returns a JWT access token if credentials are valid.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        password_hashed = hash_password(password)
        cur.execute(
            "SELECT userid FROM users WHERE username = ? AND password_hash = ?",
            (username, password_hashed)
        )
        result = cur.fetchone()

        if result:
            user_id = int(result[0])

            # Optional: log login event
            # append_event(conn, "user", user_id, "USER_LOGGED_IN", {"username": username}, user_id)

            access_token = create_access_token(data={"sub": username})
            return {"access_token": access_token, "token_type": "bearer"}

        raise HTTPException(status_code=401, detail="Invalid username or password")
    finally:
        cur.close()
        conn.close()


def register_user(username: str, password: str, email: str, phone: str):
    """
    Register a new user with username, password, email, and phone.
    Uses event sourcing: projection (insert into users) + append event.
    Returns the new user ID and confirmation message.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT userid FROM users WHERE username = ?", (username,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Username already exists")

        password_hashed = hash_password(password)

        # Insert user and return generated ID
        cur.execute("""
            INSERT INTO users (username, password_hash, email, phone)
            OUTPUT INSERTED.userid
            VALUES (?, ?, ?, ?)
        """, (username, password_hashed, email, phone))
        userid = int(cur.fetchone()[0])

        # Append event to event store
        append_event(
            conn,
            aggregate_type="user",
            aggregate_id=userid,
            event_type="USER_REGISTERED",
            payload={"username": username, "email": email, "phone": phone},
            user_id=userid
        )

        conn.commit()
        return {"userid": userid, "message": "User registered"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
