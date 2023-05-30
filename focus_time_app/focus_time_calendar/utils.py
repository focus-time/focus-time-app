from datetime import datetime, timedelta
from typing import Tuple, List, Optional
from zoneinfo import ZoneInfo

from focus_time_app.focus_time_calendar.event import FocusTimeEvent
from focus_time_app.configuration.configuration import ConfigurationV1


def compute_calendar_query_start_and_stop(configuration: ConfigurationV1) -> Tuple[datetime, datetime]:
    now = datetime.now(ZoneInfo('UTC'))
    from_date = now - timedelta(hours=configuration.calendar_look_back_hours)
    to_date = now + timedelta(hours=configuration.calendar_look_ahead_hours)
    return from_date, to_date


def get_active_focustime_event(events: List[FocusTimeEvent]) -> Optional[FocusTimeEvent]:
    now = datetime.now(ZoneInfo('UTC'))
    for event in events:
        if event.start <= now <= event.end:
            return event
