import os
from database.db import get_db_cursor
from database.models import User
from pathlib import Path
from typing import Optional, List
import uuid

SQL_PATH = os.path.join(
    Path(__file__).resolve().parents[1], "DML", "get_event_responses.sql")


def get_event_responses(event_id: int) -> List[str]:
    with get_db_cursor() as cur:
        with open(SQL_PATH, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        cur.execute(sql_script, (event_id,))
        rows = cur.fetchall()
        return rows
