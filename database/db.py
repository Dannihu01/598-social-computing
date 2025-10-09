import psycopg2
from psycopg2 import pool
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


def close_pool():
    if _db_pool is not None:
        _db_pool.closeall()
