import os
from database.db import get_db_cursor
from database.models import Event
from pathlib import Path
from typing import Optional, List, Literal
import uuid
from datetime import datetime, timedelta

SQL_PATH = os.path.join(
    Path(__file__).resolve().parents[1], "DML", "get_event_responses.sql")


def get_event_responses(event_id: int) -> List[str]:
    with get_db_cursor() as cur:
        with open(SQL_PATH, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        cur.execute(sql_script, (event_id,))
        rows = cur.fetchall()
        return rows


def is_event_over(event_id: int) -> bool:
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT time_start, duration_days FROM events WHERE id = %s",
            (event_id,)
        )
        row = cur.fetchone()
        if not row:
            return False  # Event doesn't exist

        time_start, duration_days = row
        if not time_start or not duration_days:
            return False  # Event doesn't have start time or duration

        # Calculate end time: start time + duration in days (the stored value is treated as days)
        end_time = time_start + timedelta(days=duration_days)
        current_time = datetime.now(
            time_start.tzinfo) if time_start.tzinfo else datetime.now()

        return current_time > end_time


def create_event(time_start: Optional[datetime] = None, duration_days: int = 3) -> Literal["success", "database_error", "event_already_active"]:
    """
    Create a new event in the database.

    Args:
        time_start: When the event starts (defaults to now if None)
        duration_days: How many days the event lasts (defaults to 3)

    Returns:
        "success" if event was created successfully
        "database_error" if there was a database error
    """
    try:
        with get_db_cursor() as cur:
            # Use current time if no start time provided
            if time_start is None:
                time_start = datetime.now()
            # Check if an event is already active
            if get_active_event():
                return "event_already_active"
            # Store the provided number of days in the existing `duration_days` column
            cur.execute(
                "INSERT INTO events (time_start, duration_days) VALUES (%s, %s) RETURNING id",
                (time_start, duration_days)
            )
            event_id = cur.fetchone()[0]
            cur.connection.commit()

            print(f"Event created successfully with ID: {event_id}")
            print(f"Start time: {time_start}")
            print(f"Duration: {duration_days} days")
            print(f"End time: {time_start + timedelta(days=duration_days)}")

            return "success"
    except Exception as e:
        print(f"Database error in create_event: {e}")
        return "database_error"




def delete_event(event_id: int) -> Literal["success", "event_not_found", "database_error"]:
    """
    Delete an event from the database.

    Args:
        event_id: The ID of the event to delete

    Returns:
        "success" if event was deleted successfully
        "event_not_found" if the event doesn't exist
        "database_error" if there was a database error
    """
    try:
        with get_db_cursor() as cur:
            # First check if the event exists
            cur.execute("SELECT id FROM events WHERE id = %s", (event_id,))

            
            if not cur.fetchone():
                return "event_not_found"

            # Delete the event (cascade will handle related records)
            cur.execute(
                "DELETE FROM events WHERE id = %s CASCADE", (event_id,))
            rows_deleted = cur.rowcount
            cur.connection.commit()

            if rows_deleted > 0:
                print(f"Event {event_id} deleted successfully")
                return "success"
            else:
                return "event_not_found"

    except Exception as e:
        print(f"Database error in delete_event: {e}")
        return "database_error"


def get_active_event() -> Optional[Event]:
    with get_db_cursor() as cur:
        cur.execute("""
            WITH non_finalized_events AS(
                SELECT * FROM events WHERE is_finalized = 0
            )

            SELECT 
                id, time_start, duration_days, is_finalized FROM non_finalized_events 
            WHERE 
                time_start + INTERVAL '1 day' * duration_days >= NOW() 
            ORDER BY time_start 
            ASC LIMIT 1
        """)
        row = cur.fetchone()
        if row:
            return Event(id=row[0], time_start=row[1], duration_days=row[2], is_finalized=row[3])
        return None


def get_unfinalized_ended_events() -> List[Event]:
    """
    Get all events that have ended but haven't been finalized yet.
    This is used by the scheduler to find events ready for auto-finalization.
    
    Returns:
        List of Event objects that are ended but not finalized
    """
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT id, time_start, duration_days, is_finalized 
            FROM events 
            WHERE is_finalized = 0
            AND time_start + INTERVAL '1 day' * duration_days < NOW()
            ORDER BY time_start ASC
        """)
        rows = cur.fetchall()
        return [Event(id=row[0], time_start=row[1], duration_days=row[2], is_finalized=row[3]) for row in rows]


def mark_event_finalized(event_id: int) -> Literal["success", "event_not_found", "database_error"]:
    """
    Mark an event as finalized after auto-finalization completes.
    
    Args:
        event_id: The ID of the event to mark as finalized
        
    Returns:
        "success" if event was marked successfully
        "event_not_found" if the event doesn't exist
        "database_error" if there was a database error
    """
    try:
        with get_db_cursor() as cur:
            cur.execute(
                "UPDATE events SET is_finalized = 1 WHERE id = %s",
                (event_id,)
            )
            rows_updated = cur.rowcount
            cur.connection.commit()
            
            if rows_updated > 0:
                print(f"Event {event_id} marked as finalized")
                return "success"
            else:
                return "event_not_found"
                
    except Exception as e:
        print(f"Database error in mark_event_finalized: {e}")
        return "database_error"


def delete_all_events():
    with get_db_cursor() as cur:
        # remove event messaging first to avoid FK issues, then events
        cur.execute("DELETE FROM event_messaging")
        cur.execute("DELETE FROM events")
        cur.connection.commit()
    return "success"
 

def add_message_to_event(event_id: int, sys_message_id: int):
    # minimal implementation: associate a system message with an event
    with get_db_cursor() as cur:
        cur.execute(
            "INSERT INTO event_messaging (event_id, sys_message_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (event_id, sys_message_id),
        )
        cur.connection.commit()
    return "success"