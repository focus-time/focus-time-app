from abc import ABC
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from focus_time_app.focus_time_calendar.abstract_calendar_adapter import AbstractCalendarAdapter


class AbstractTestingCalendarAdapter(AbstractCalendarAdapter, ABC):
    def clean_calendar(self):
        now = datetime.now(ZoneInfo('UTC'))
        from_date = now - timedelta(days=1)
        to_date = now + timedelta(days=2)

        events = self.get_events((from_date, to_date))
        for event in events:
            self.remove_event(event)
