import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from typing import Generator
_db_pool = None


def init_pool(dsn=None):
    """Call once, after app starts."""
    global _db_pool
    if _db_pool is None:
        _db_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=dsn
        )


def get_conn():
    """Get a connection from the pool."""
    if _db_pool is None:
        raise RuntimeError("DB pool not initialized!")
    return _db_pool.getconn()


def put_conn(conn):
    """Return a connection to the pool."""
    _db_pool.putconn(conn)


@contextmanager
def get_db_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """
    Context manager for database connections.
    Automatically handles connection acquisition and release.
    
    Usage:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users")
                result = cur.fetchall()
    """
    conn = None
    try:
        conn = get_conn()
        yield conn
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            put_conn(conn)


@contextmanager
def get_db_cursor() -> Generator[psycopg2.extensions.cursor, None, None]:
    """
    Context manager for database cursors.
    Automatically handles connection and cursor management.
    
    Usage:
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM users")
            result = cur.fetchall()
    """
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            yield cur
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            put_conn(conn)


def close_pool():
    global _db_pool
    if _db_pool is None:
        return
    try:
        _db_pool.closeall()
    except pool.PoolError:
        # Pool already closed; ignore to prevent noisy shutdown errors
        pass
    finally:
        _db_pool = None
