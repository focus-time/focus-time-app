from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class CalendarType(Enum):
    Outlook365 = 1


@dataclass
class FocusTimeEvent:
    id: str
    start: datetime
    end: datetime
    reminder_in_minutes: int
