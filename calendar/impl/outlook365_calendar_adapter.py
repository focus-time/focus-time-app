from datetime import datetime
from typing import List

from calendar.abstract_calendar_adapter import AbstractCalendarAdapter
from calendar.event import FocusTimeEvent
from configuration.configuration import ConfigurationV1


class Outlook365CalendarAdapter(AbstractCalendarAdapter):

    def __init__(self, configuration: ConfigurationV1):
        self._configuration = configuration

    def authenticate(self):
        pass

    def check_connection_and_credentials(self):
        pass

    def get_events(self, from_date: datetime, to_date: datetime) -> List[FocusTimeEvent]:
        pass

    def create_event(self, from_date: datetime, to_date: datetime) -> FocusTimeEvent:
        pass

    def update_event(self, event: FocusTimeEvent, from_date: datetime, to_date: datetime, reminder_in_minutes: int):
        pass
