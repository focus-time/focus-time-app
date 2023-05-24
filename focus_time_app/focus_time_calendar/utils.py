from datetime import datetime
from typing import Tuple, List, Optional

from focus_time_app.focus_time_calendar.event import FocusTimeEvent
from focus_time_app.configuration.configuration import ConfigurationV1


def compute_calendar_query_start_and_stop(configuration: ConfigurationV1) -> Tuple[datetime, datetime]:
    pass  # TODO


def get_active_focustime_event(events: List[FocusTimeEvent]) -> Optional[FocusTimeEvent]:
    pass  # TODO
