from database.db import get_db_cursor
from database.models import SysMessage, SysMessageType
from typing import Optional, List

def create_private_message(content: str) -> SysMessage:
    """Create a new private message (potential prompt) for starting events."""
    with get_db_cursor() as cur:
        cur.execute(
            "INSERT INTO sys_messages (type, content) VALUES (%s, %s) RETURNING id, type, content",
            (SysMessageType.private, content)
        )
        row = cur.fetchone()
        cur.connection.commit()
        return SysMessage(
            id=row[0],
            type=SysMessageType(row[1]),
            content=row[2]
        )

def get_private_message_by_id(message_id: int) -> Optional[SysMessage]:
    """Get a specific private message by ID."""
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT id, type, content FROM sys_messages WHERE id = %s AND type = %s",
            (message_id, SysMessageType.private)
        )
        row = cur.fetchone()
        if row:
            return SysMessage(
                id=row[0],
                type=SysMessageType(row[1]),
                content=row[2]
            )
        return None

def get_all_private_messages(limit: Optional[int] = None) -> List[SysMessage]:
    """Get all private messages (potential prompts) for starting events."""
    with get_db_cursor() as cur:
        query = "SELECT id, type, content FROM sys_messages WHERE type = %s ORDER BY id DESC"
        params = [SysMessageType.private]
        
        if limit:
            query += " LIMIT %s"
            params.append(limit)
        
        cur.execute(query, params)
        rows = cur.fetchall()
        return [
            SysMessage(
                id=row[0],
                type=SysMessageType(row[1]),
                content=row[2]
            )
            for row in rows
        ]

def get_random_private_message() -> Optional[SysMessage]:
    """Get a random private message for use in starting an event."""
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT id, type, content FROM sys_messages WHERE type = %s ORDER BY RANDOM() LIMIT 1",
            (SysMessageType.private,)
        )
        row = cur.fetchone()
        if row:
            return SysMessage(
                id=row[0],
                type=SysMessageType(row[1]),
                content=row[2]
            )
        return None

def update_private_message(message_id: int, content: str) -> Optional[SysMessage]:
    """Update an existing private message."""
    with get_db_cursor() as cur:
        cur.execute(
            "UPDATE sys_messages SET content = %s WHERE id = %s AND type = %s RETURNING id, type, content",
            (content, message_id, SysMessageType.private)
        )
        row = cur.fetchone()
        cur.connection.commit()
        
        if row:
            return SysMessage(
                id=row[0],
                type=SysMessageType(row[1]),
                content=row[2]
            )
        return None

def delete_private_message(message_id: int) -> bool:
    """Delete a private message."""
    with get_db_cursor() as cur:
        cur.execute(
            "DELETE FROM sys_messages WHERE id = %s AND type = %s",
            (message_id, SysMessageType.private)
        )
        cur.connection.commit()
        return cur.rowcount > 0

def search_private_messages(search_term: str) -> List[SysMessage]:
    """Search private messages by content."""
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT id, type, content FROM sys_messages WHERE type = %s AND content ILIKE %s ORDER BY id DESC",
            (SysMessageType.private, f"%{search_term}%")
        )
        rows = cur.fetchall()
        return [
            SysMessage(
                id=row[0],
                type=SysMessageType(row[1]),
                content=row[2]
            )
            for row in rows
        ]

def get_private_message_count() -> int:
    """Get the total count of private messages."""
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM sys_messages WHERE type = %s",
            (SysMessageType.private,)
        )
        row = cur.fetchone()
        return row[0] if row else 0

def create_aggregated_message(content: str) -> SysMessage:
    """Create a new aggregated message (for completed events)."""
    with get_db_cursor() as cur:
        cur.execute(
            "INSERT INTO sys_messages (type, content) VALUES (%s, %s) RETURNING id, type, content",
            (SysMessageType.aggregated, content)
        )
        row = cur.fetchone()
        cur.connection.commit()
        return SysMessage(
            id=row[0],
            type=SysMessageType(row[1]),
            content=row[2]
        )

def get_aggregated_message_by_id(message_id: int) -> Optional[SysMessage]:
    """Get a specific aggregated message by ID."""
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT id, type, content FROM sys_messages WHERE id = %s AND type = %s",
            (message_id, SysMessageType.aggregated)
        )
        row = cur.fetchone()
        if row:
            return SysMessage(
                id=row[0],
                type=SysMessageType(row[1]),
                content=row[2]
            )
        return None

def get_all_aggregated_messages(limit: Optional[int] = None) -> List[SysMessage]:
    """Get all aggregated messages (completed events)."""
    with get_db_cursor() as cur:
        query = "SELECT id, type, content FROM sys_messages WHERE type = %s ORDER BY id DESC"
        params = [SysMessageType.aggregated]
        
        if limit:
            query += " LIMIT %s"
            params.append(limit)
        
        cur.execute(query, params)
        rows = cur.fetchall()
        return [
            SysMessage(
                id=row[0],
                type=SysMessageType(row[1]),
                content=row[2]
            )
            for row in rows
        ]

def get_all_sys_messages(limit: Optional[int] = None) -> List[SysMessage]:
    """Get all system messages (both private and aggregated)."""
    with get_db_cursor() as cur:
        query = "SELECT id, type, content FROM sys_messages ORDER BY id DESC"
        params = []
        
        if limit:
            query += " LIMIT %s"
            params.append(limit)
        
        cur.execute(query, params)
        rows = cur.fetchall()
        return [
            SysMessage(
                id=row[0],
                type=SysMessageType(row[1]),
                content=row[2]
            )
            for row in rows
        ]

def get_sys_message_by_id(message_id: int) -> Optional[SysMessage]:
    """Get any system message by ID (regardless of type)."""
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT id, type, content FROM sys_messages WHERE id = %s",
            (message_id,)
        )
        row = cur.fetchone()
        if row:
            return SysMessage(
                id=row[0],
                type=SysMessageType(row[1]),
                content=row[2]
            )
        return None

def update_sys_message(message_id: int, content: str) -> Optional[SysMessage]:
    """Update any system message by ID."""
    with get_db_cursor() as cur:
        cur.execute(
            "UPDATE sys_messages SET content = %s WHERE id = %s RETURNING id, type, content",
            (content, message_id)
        )
        row = cur.fetchone()
        cur.connection.commit()
        
        if row:
            return SysMessage(
                id=row[0],
                type=SysMessageType(row[1]),
                content=row[2]
            )
        return None

def delete_sys_message(message_id: int) -> bool:
    """Delete any system message by ID."""
    with get_db_cursor() as cur:
        cur.execute("DELETE FROM sys_messages WHERE id = %s", (message_id,))
        cur.connection.commit()
        return cur.rowcount > 0

def get_orphaned_private_messages() -> List[SysMessage]:
    """Get private messages that are not associated with any event."""
    with get_db_cursor() as cur:
        cur.execute(
            """SELECT sm.id, sm.type, sm.content 
               FROM sys_messages sm 
               LEFT JOIN event_messaging em ON sm.id = em.sys_message_id 
               WHERE sm.type = %s AND em.sys_message_id IS NULL 
               ORDER BY sm.id DESC""",
            (SysMessageType.private,)
        )
        rows = cur.fetchall()
        return [
            SysMessage(
                id=row[0],
                type=SysMessageType(row[1]),
                content=row[2]
            )
            for row in rows
        ]

def get_unused_private_messages() -> List[SysMessage]:
    """
    Get private messages that haven't been used in any unfinalized events.
    This allows reuse of prompts from finalized events while preventing 
    duplicate prompts in active/pending events.
    """
    with get_db_cursor() as cur:
        cur.execute(
            """SELECT sm.id, sm.type, sm.content 
               FROM sys_messages sm 
               WHERE sm.type = %s 
               AND sm.id NOT IN (
                   SELECT em.sys_message_id 
                   FROM event_messaging em 
                   JOIN events e ON em.event_id = e.id 
                   WHERE e.is_finalized = 0
               )
               ORDER BY RANDOM()""",
            (SysMessageType.private,)
        )
        rows = cur.fetchall()
        return [
            SysMessage(
                id=row[0],
                type=SysMessageType(row[1]),
                content=row[2]
            )
            for row in rows
        ]

def associate_sys_message_with_event(event_id: int, sys_message_id: int) -> bool:
    """Associate a sys message with an event."""
    with get_db_cursor() as cur:
        try:
            cur.execute(
                "INSERT INTO event_messaging (event_id, sys_message_id) VALUES (%s, %s)",
                (event_id, sys_message_id)
            )
            cur.connection.commit()
            return True
        except Exception:
            # Handle case where association already exists or invalid IDs
            cur.connection.rollback()
            return False

def disassociate_sys_message_from_event(event_id: int, sys_message_id: int) -> bool:
    """Remove association between a sys message and an event."""
    with get_db_cursor() as cur:
        cur.execute(
            "DELETE FROM event_messaging WHERE event_id = %s AND sys_message_id = %s",
            (event_id, sys_message_id)
        )
        cur.connection.commit()
        return cur.rowcount > 0

def get_sys_messages_for_event(event_id: int) -> List[SysMessage]:
    """Get all sys messages associated with a specific event."""
    with get_db_cursor() as cur:
        cur.execute(
            """SELECT sm.id, sm.type, sm.content 
               FROM sys_messages sm 
               JOIN event_messaging em ON sm.id = em.sys_message_id 
               WHERE em.event_id = %s 
               ORDER BY sm.id DESC""",
            (event_id,)
        )
        rows = cur.fetchall()
        return [
            SysMessage(
                id=row[0],
                type=SysMessageType(row[1]),
                content=row[2]
            )
            for row in rows
        ]

def get_events_for_sys_message(sys_message_id: int) -> List[int]:
    """Get all event IDs associated with a specific sys message."""
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT event_id FROM event_messaging WHERE sys_message_id = %s",
            (sys_message_id,)
        )
        rows = cur.fetchall()
        return [row[0] for row in rows]
