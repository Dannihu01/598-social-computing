from database.db import get_db_cursor
from database.models import User
from typing import Optional, List
import uuid


def create_user(slack_id: Optional[str]) -> User:
    with get_db_cursor() as cur:
        user_uuid = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO users (uuid, slack_id) VALUES (%s, %s) RETURNING uuid, slack_id",
            (user_uuid, slack_id)
        )
        row = cur.fetchone()
        cur.connection.commit()
        return User(uuid=row[0], slack_id=row[1])


def get_user_by_uuid(user_uuid: str) -> Optional[User]:
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT uuid, slack_id FROM users WHERE uuid = %s",
            (user_uuid,)
        )
        row = cur.fetchone()
        if row:
            return User(uuid=row[0], slack_id=row[1])
        return None


def get_user_by_slack_id(slack_id: str) -> Optional[User]:
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT uuid, slack_id FROM users WHERE slack_id = %s",
            (slack_id,)
        )
        row = cur.fetchone()
        if row:
            return User(uuid=row[0], slack_id=row[1])
        return None


def update_user_slack_id(user_uuid: str, new_slack_id: str) -> Optional[User]:
    with get_db_cursor() as cur:
        cur.execute(
            "UPDATE users SET slack_id = %s WHERE uuid = %s RETURNING uuid, slack_id",
            (new_slack_id, user_uuid)
        )
        row = cur.fetchone()
        cur.connection.commit()
        if row:
            return User(uuid=row[0], slack_id=row[1])
        return None


def delete_user(user_uuid: str) -> bool:
    with get_db_cursor() as cur:
        cur.execute(
            "DELETE FROM users WHERE uuid = %s",
            (user_uuid,)
        )
        cur.connection.commit()
        return cur.rowcount > 0


def list_users(limit: int = 100) -> List[User]:
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT uuid, slack_id FROM users ORDER BY uuid LIMIT %s",
            (limit,)
        )
        rows = cur.fetchall()
        return [User(uuid=row[0], slack_id=row[1]) for row in rows]

# example usage
# user = create_user("U12345")
# found = get_user_by_uuid(str(user.uuid))
# updated = update_user_slack_id(str(user.uuid), "U67890")
# deleted = delete_user(str(user.uuid))
# users = list_users()
