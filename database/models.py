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
    id: int
    slack_id: Optional[str]


@dataclass
class Event:
    id: int
    time_start: Optional[datetime]
    day_duration: Optional[int]


@dataclass
class SysMessage:
    id: int
    type: SysMessageType
    content: Optional[str]


@dataclass
class Response:
    id: int
    entry: Optional[str]
    submitted_at: Optional[datetime]
    user_id: UUID
    event_id: int


@dataclass
class EventMessaging:
    event_id: int
    sys_message_id: int

@dataclass
class SlackEnterprise:
    id: int
    enterprise_name: str
    description: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]