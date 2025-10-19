import os
from database.db import get_conn, put_conn
from database.models import User
from pathlib import Path
from typing import Optional, List
import uuid

SQL_PATH = os.path.join(
    Path(__file__).resolve().parents[1], "DML", "get_event_responses.sql")


def get_event_responses(event_id: str) -> List[str]:
    conn = get_conn()
    try:
        with open(SQL_PATH, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        with conn.cursor() as cur:
            cur.execute(sql_script, (event_id,))
            rows = cur.fetchall()
            return rows
    finally:
        put_conn(conn)
