from dataclasses import dataclass, field
from typing import List

import marshmallow.validate
import marshmallow_dataclass
from marshmallow.fields import Enum

from calendar.event import CalendarType


# CalendarTypeType = NewType("CalendarType", str, field=marshmallow.fields.Enum)

@dataclass
class ConfigurationV1:
    calendar_type: CalendarType = field(metadata={"marshmallow_field": Enum(CalendarType)})
    calendar_look_ahead_hours: int = field(metadata={"validate": marshmallow.validate.Range(min=0)})
    calendar_look_back_hours: int = field(metadata={"validate": marshmallow.validate.Range(min=0)})
    focustime_event_name: str = field(metadata={"validate": marshmallow.validate.Length(min=1)})
    start_commands: List[str]
    stop_commands: List[str]
    focustime_os_profile_name: str = field(metadata={"validate": marshmallow.validate.Length(min=1)})
    adjust_event_reminder_time: bool
    event_reminder_time_minutes: int = field(metadata={"validate": marshmallow.validate.Range(min=1)})
    version: int = field(default=1)


ConfigurationV1Schema = marshmallow_dataclass.class_schema(ConfigurationV1)
