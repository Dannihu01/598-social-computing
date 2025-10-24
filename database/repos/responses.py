import os
from database.db import get_db_cursor
from database.repos import events
from database.repos import users
from pathlib import Path
from typing import Optional, List, Literal


SQL_PATH = os.path.join(
    Path(__file__).resolve().parents[1], "DML", "get_event_responses.sql")


def get_event_responses(event_id: int) -> List[str]:
    with get_db_cursor() as cur:
        with open(SQL_PATH, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        cur.execute(sql_script, (event_id,))
        rows = cur.fetchall()
        return rows


def add_response(user_slack_id: str, response: str) -> Literal["success", "event_over", "database_error", "no_active_event"]:
    print(f"FROM DB FUNC: {user_slack_id}")
    print(f"FROM DB FUNC: {response}")
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
