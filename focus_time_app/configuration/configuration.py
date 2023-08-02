from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

import marshmallow.validate
import marshmallow_dataclass
from marshmallow.fields import Enum
from marshmallow_dataclass import NewType

from focus_time_app.focus_time_calendar.event import CalendarType

UUID = NewType("UUID", str, field=marshmallow.fields.UUID)


@dataclass
class Outlook365ConfigurationV1:
    client_id: UUID
    calendar_name: str = field(metadata={"validate": marshmallow.validate.Length(min=1)})


@dataclass
class CaldavConfigurationV1:
    calendar_url: str = field(metadata={"validate": marshmallow.validate.Length(min=1)})


@dataclass
class ConfigurationV1:
    calendar_type: CalendarType = field(metadata={"marshmallow_field": Enum(CalendarType)})
    calendar_look_ahead_hours: int = field(metadata={"validate": marshmallow.validate.Range(min=0)})
    calendar_look_back_hours: int = field(metadata={"validate": marshmallow.validate.Range(min=0)})
    focustime_event_name: str = field(metadata={"validate": marshmallow.validate.Length(min=1)})
    start_commands: List[str]
    stop_commands: List[str]
    dnd_profile_name: str = field(metadata={"validate": marshmallow.validate.Length(min=1)})
    set_event_reminder: bool
    event_reminder_time_minutes: int = field(metadata={"validate": marshmallow.validate.Range(min=0)})
    version: int = field(default=1)
    adapter_configuration: Optional[Dict[str, Any]] = field(default=None)


ConfigurationV1Schema = marshmallow_dataclass.class_schema(ConfigurationV1)
