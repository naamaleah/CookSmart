# backend/db/db_config.py
import pyodbc
from contextlib import contextmanager
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
CONN_STR = os.getenv("SQLSERVER_CONN_STR")

def get_connection():
    """
    Create and return a new connection to the SQL Server database
    using the connection string from environment variables.
    """
    return pyodbc.connect(CONN_STR)

@contextmanager
def get_sqlserver_conn():
    """
    Context manager for establishing a SQL Server connection.
    Usage: with get_sqlserver_conn() as conn: ...
    Ensures the connection is closed properly after use.
    """
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
