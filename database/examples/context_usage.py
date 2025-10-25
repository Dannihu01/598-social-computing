# --------------------------------------------------
# File: database/examples/context_usage.py
# Description: Examples of how to use the new database context management
# --------------------------------------------------

from database.db import get_db_connection, get_db_cursor
from database.models import User, Event, Response
import uuid
from datetime import datetime


def example_with_connection_context():
    """
    Example using get_db_connection() context manager.
    Use this when you need full control over the connection and cursor.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Multiple operations in a single transaction
            cur.execute("SELECT COUNT(*) FROM users")
            user_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM events")
            event_count = cur.fetchone()[0]
            
            # All operations are in the same transaction
            conn.commit()
            
            print(f"Users: {user_count}, Events: {event_count}")


def example_with_cursor_context():
    """
    Example using get_db_cursor() context manager.
    Use this for simple single-operation queries.
    """
    with get_db_cursor() as cur:
        cur.execute("SELECT uuid, slack_id FROM users LIMIT 5")
        users = cur.fetchall()
        
        for user_data in users:
            print(f"User: {user_data[0]}, Slack ID: {user_data[1]}")


def example_transaction_rollback():
    """
    Example showing automatic rollback on exception.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # This will fail and automatically rollback
                cur.execute("INSERT INTO non_existent_table VALUES (1)")
                conn.commit()
    except Exception as e:
        print(f"Transaction rolled back automatically: {e}")


def example_create_user_with_context():
    """
    Example of creating a user using the context manager.
    """
    with get_db_cursor() as cur:
        user_uuid = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO users (uuid, slack_id) VALUES (%s, %s) RETURNING uuid, slack_id",
            (user_uuid, "U12345")
        )
        row = cur.fetchone()
        cur.connection.commit()
        
        user = User(uuid=row[0], slack_id=row[1])
        print(f"Created user: {user}")
        return user


def example_create_event_with_context():
    """
    Example of creating an event using the context manager.
    """
    with get_db_cursor() as cur:
        cur.execute(
            "INSERT INTO events (time_start, day_duration) VALUES (%s, %s) RETURNING id, time_start, day_duration",
            (datetime.now(), 1)
        )
        row = cur.fetchone()
        cur.connection.commit()
        
        event = Event(id=row[0], time_start=row[1], day_duration=row[2])
        print(f"Created event: {event}")
        return event


if __name__ == "__main__":
    print("Database Context Management Examples")
    print("=" * 40)
    
    print("\n1. Connection Context Example:")
    example_with_connection_context()
    
    print("\n2. Cursor Context Example:")
    example_with_cursor_context()
    
    print("\n3. Transaction Rollback Example:")
    example_transaction_rollback()
    
    print("\n4. Create User Example:")
    user = example_create_user_with_context()
    
    print("\n5. Create Event Example:")
    event = example_create_event_with_context()
