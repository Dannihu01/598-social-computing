from database.db import get_db_connection, get_db_cursor
from database.models import User, Event, Response
import uuid
from datetime import datetime

def example_create_event():
    with get_db_cursor as cur:
        cur.execute(
            "INSERT I"
        )