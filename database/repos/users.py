from database.db import get_db_cursor
from database.models import User
from typing import Optional, List


def create_user(slack_id: Optional[str]) -> User:
    with get_db_cursor() as cur:
        user_id = str(id.id4())
        cur.execute(
            "INSERT INTO users (id, slack_id) VALUES (%s, %s) RETURNING id, slack_id",
            (user_id, slack_id)
        )
        row = cur.fetchone()
        cur.connection.commit()
        return User(id=row[0], slack_id=row[1])


def get_user_by_id(user_id: str) -> Optional[User]:
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT id, slack_id FROM users WHERE id = %s",
            (user_id,)
        )
        row = cur.fetchone()
        if row:
            return User(id=row[0], slack_id=row[1])
        return None


def get_user_by_slack_id(slack_id: str) -> Optional[User]:
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT id, slack_id FROM users WHERE slack_id = %s",
            (slack_id,)
        )
        row = cur.fetchone()
        if row:
            print(row)
            return User(id=row[0], slack_id=row[1])
        return None


def update_user_slack_id(user_id: str, new_slack_id: str) -> Optional[User]:
    with get_db_cursor() as cur:
        cur.execute(
            "UPDATE users SET slack_id = %s WHERE id = %s RETURNING id, slack_id",
            (new_slack_id, user_id)
        )
        row = cur.fetchone()
        cur.connection.commit()
        if row:
            return User(id=row[0], slack_id=row[1])
        return None


def delete_user(user_id: str) -> bool:
    with get_db_cursor() as cur:
        cur.execute(
            "DELETE FROM users WHERE id = %s",
            (user_id,)
        )
        cur.connection.commit()
        return cur.rowcount > 0


def list_users(limit: int = 100) -> List[User]:
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT id, slack_id FROM users ORDER BY id LIMIT %s",
            (limit,)
        )
        rows = cur.fetchall()
        return [User(id=row[0], slack_id=row[1]) for row in rows]


# example usage
# user = create_user("U12345")
# found = get_user_by_id(str(user.id))
# updated = update_user_slack_id(str(user.id), "U67890")
# deleted = delete_user(str(user.id))
# users = list_users()
