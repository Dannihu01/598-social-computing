from database.db import get_db_cursor
from database.models import SlackEnterprise
from typing import Optional, List

def create_enterprise(enterprise_name: str, description: Optional[str] = None) -> SlackEnterprise:
    with get_db_cursor() as cur:
        cur.execute(
            "INSERT INTO slack_enterprises (enterprise_name, description) VALUES (%s, %s) RETURNING id, enterprise_name, description, created_at, updated_at",
            (enterprise_name, description)
        )
        row = cur.fetchone()
        cur.connection.commit()
        return SlackEnterprise(
            id=row[0],
            enterprise_name=row[1],
            description=row[2],
            created_at=row[3],
            updated_at=row[4]
        )

def get_enterprise_by_id(enterprise_id: int) -> Optional[SlackEnterprise]:
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT id, enterprise_name, description, created_at, updated_at FROM slack_enterprises WHERE id = %s",
            (enterprise_id,)
        )
        row = cur.fetchone()
        if row:
            return SlackEnterprise(
                id=row[0],
                enterprise_name=row[1],
                description=row[2],
                created_at=row[3],
                updated_at=row[4]
            )
        return None
        
def get_enterprise_by_name(enterprise_name: str) -> Optional[SlackEnterprise]:
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT id, enterprise_name, description, created_at, updated_at FROM slack_enterprises WHERE enterprise_name = %s",
            (enterprise_name,)
        )
        row = cur.fetchone()
        if row:
            return SlackEnterprise(
                id=row[0],
                enterprise_name=row[1],
                description=row[2],
                created_at=row[3],
                updated_at=row[4]
            )
        return None

def get_all_enterprises() -> List[SlackEnterprise]:
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT id, enterprise_name, description, created_at, updated_at FROM slack_enterprises ORDER BY enterprise_name"
        )
        rows = cur.fetchall()
        return [
            SlackEnterprise(
                id=row[0],
                enterprise_name=row[1],
                description=row[2],
                created_at=row[3],
                updated_at=row[4]
            )
            for row in rows
        ]

def update_enterprise(enterprise_name: str, description: Optional[str] = None) -> Optional[SlackEnterprise]:
    with get_db_cursor() as cur:
        # Build dynamic update query
        updates = []
        params = []
        
        if description is not None:
            updates.append("description = %s")
            params.append(description)
        
        if not updates:
            return get_enterprise_by_name(enterprise_name)
        
        updates.append("updated_at = NOW()")
        params.append(enterprise_name)
        
        cur.execute(
            f"UPDATE slack_enterprises SET {', '.join(updates)} WHERE enterprise_name = %s RETURNING id, enterprise_name, description, created_at, updated_at",
            params
        )
        row = cur.fetchone()
        cur.connection.commit()
        
        if row:
            return SlackEnterprise(
                id=row[0],
                enterprise_name=row[1],
                description=row[2],
                created_at=row[3],
                updated_at=row[4]
            )
        return None