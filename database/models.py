from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from datetime import datetime
import enum


class SysMessageType(str, enum.Enum):
    private = "private"
    aggregated = "aggregated"


@dataclass
class User:
    uuid: UUID
    slack_id: Optional[str]


@dataclass
class Event:
    id: str
    time_start: Optional[datetime]
    day_duration: Optional[int]


@dataclass
class SysMessage:
    id: str
    type: SysMessageType
    content: Optional[str]


@dataclass
class Response:
    id: str
    entry: Optional[str]
    submitted_at: Optional[datetime]
    user_id: UUID
    event_id: str


@dataclass
class EventMessaging:
    event_id: str
    sys_message_id: str
