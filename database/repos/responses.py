import os
from database.db import get_db_cursor
from database.repos import events
from database.repos import users
from pathlib import Path
from typing import Optional, List, Literal, Tuple


SQL_PATH = os.path.join(
    Path(__file__).resolve().parents[1], "DML", "get_event_responses.sql")

SQL_PATH_WITH_USERS = os.path.join(
    Path(__file__).resolve().parents[1], "DML", "get_responses_with_users.sql")


def get_event_responses(event_id: int) -> List[str]:
    with get_db_cursor() as cur:
        with open(SQL_PATH, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        cur.execute(sql_script, (event_id,))
        rows = cur.fetchall()
        return rows
    
def get_event_user_ids(event_id: int) -> List[int]:
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT user_id FROM responses WHERE event_id = %s;",
            (event_id,)
        )
        rows = cur.fetchall()
        return [row[0] for row in rows]

def get_responses_with_users(event_id: int) -> List[Tuple[str, str]]:
    """
    Get all responses for an event with user slack_ids.
    
    Args:
        event_id: The event ID
        
    Returns:
        List of tuples: [(slack_id, response_text), ...]
    """
    with get_db_cursor() as cur:
        with open(SQL_PATH_WITH_USERS, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        cur.execute(sql_script, (event_id,))
        rows = cur.fetchall()
        return rows


def add_response(user_slack_id: str, response: str) -> Literal["success", "event_over", "database_error", "no_active_event"]:
    try:
        with get_db_cursor() as cur:
            active_event = events.get_active_event()
            if not active_event:
                return "no_active_event"
            event_id = active_event.id
            user_id = users.get_user_by_slack_id(user_slack_id).id
            cur.execute(
                "SELECT id from responses WHERE user_id=%s AND event_id=%s",
                (user_id, event_id,)
            )
            if cur.fetchone():
                cur.execute(
                    "UPDATE responses SET entry=%s WHERE user_id=%s AND event_id=%s",
                    (response, user_id, event_id)
                )
            else:
                cur.execute(
                    "INSERT INTO responses (entry, user_id, event_id, submitted_at) VALUES (%s, %s, %s, NOW())",
                    (response, user_id, event_id)
                )
            cur.connection.commit()
            return "success"
    except Exception as e:
        # Log the error (you might want to use proper logging)
        print(f"Database error in add_response: {e}")
        return "database_error"
