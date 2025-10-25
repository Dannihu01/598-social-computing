# Database Context Management

This document explains how to use the new database context management system for automatic connection handling.

## Overview

The database module now provides context managers that automatically handle database connections, ensuring proper cleanup and error handling. This eliminates the need to manually manage `get_conn()` and `put_conn()` calls.

## Context Managers

### `get_db_connection()`

Use this when you need full control over the connection and cursor, especially for multi-operation transactions.

```python
from database.db import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        # Multiple operations in a single transaction
        cur.execute("INSERT INTO users (uuid, slack_id) VALUES (%s, %s)", (uuid, slack_id))
        cur.execute("INSERT INTO events (time_start) VALUES (%s)", (datetime.now(),))
        conn.commit()  # Commit the transaction
```

### `get_db_cursor()`

Use this for simple single-operation queries. The connection and cursor are managed automatically.

```python
from database.db import get_db_cursor

with get_db_cursor() as cur:
    cur.execute("SELECT * FROM users WHERE slack_id = %s", (slack_id,))
    result = cur.fetchone()
```

## Key Benefits

1. **Automatic Cleanup**: Connections are automatically returned to the pool
2. **Error Handling**: Automatic rollback on exceptions
3. **Simplified Code**: No more manual `get_conn()`/`put_conn()` calls
4. **Transaction Safety**: Proper transaction management

## Migration from Old Pattern

### Before (Manual Connection Management)
```python
from database.db import get_conn, put_conn

def create_user(slack_id: str):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO users (uuid, slack_id) VALUES (%s, %s)", (uuid, slack_id))
            conn.commit()
    finally:
        put_conn(conn)
```

### After (Context Management)
```python
from database.db import get_db_cursor

def create_user(slack_id: str):
    with get_db_cursor() as cur:
        cur.execute("INSERT INTO users (uuid, slack_id) VALUES (%s, %s)", (uuid, slack_id))
        cur.connection.commit()
```

## Updated Models

The models have been updated to use integer IDs instead of string IDs to match the new SERIAL primary keys:

```python
@dataclass
class Event:
    id: int  # Changed from str to int
    time_start: Optional[datetime]
    day_duration: Optional[int]

@dataclass
class Response:
    id: int  # Changed from str to int
    entry: Optional[str]
    submitted_at: Optional[datetime]
    user_id: UUID
    event_id: int  # Changed from str to int
```

## Repository Functions

All repository functions have been updated to use the new context management:

- `database/repos/users.py` - All functions now use `get_db_cursor()`
- `database/repos/responses.py` - Updated to use context management
- Function signatures updated to use `int` instead of `str` for IDs

## Error Handling

The context managers automatically handle errors:

- **Exceptions**: Any exception triggers an automatic rollback
- **Connection Issues**: Connections are properly returned to the pool even on errors
- **Transaction Safety**: Failed operations don't leave the database in an inconsistent state

## Examples

See `database/examples/context_usage.py` for comprehensive examples of how to use the new context management system.

## Best Practices

1. **Use `get_db_cursor()`** for simple queries
2. **Use `get_db_connection()`** for multi-operation transactions
3. **Always commit** transactions explicitly when needed
4. **Let exceptions propagate** - the context manager handles cleanup
5. **Don't mix old and new patterns** in the same function

## App Integration

The Flask app (`app.py`) has been updated to:
- Initialize the database pool on startup
- Register cleanup functions to close the pool on shutdown
- Ensure proper resource cleanup

This ensures that database connections are properly managed throughout the application lifecycle.
