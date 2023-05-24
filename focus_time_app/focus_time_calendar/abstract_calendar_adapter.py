from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any

from focus_time_app.focus_time_calendar.event import FocusTimeEvent


class AbstractCalendarAdapter(ABC):
    @abstractmethod
    def authenticate(self) -> Optional[Dict[str, Any]]:
        """
        Interactively queries the user for information (in the terminal) necessary to retrieve events from the calendar.
        Typically involves asking for some application ID (e.g. OAuth Client ID), endpoint URLs, or the name of the
        calendar (in case the user account can host multiple calendars).

        :return: Dict that contains the adapter-specific configuration (if authentication was successful),
            None otherwise
        """

    @abstractmethod
    def check_connection_and_credentials(self):
        """

        :return:
        """

    @abstractmethod
    def get_events(self, from_date: datetime, to_date: datetime) -> List[FocusTimeEvent]:
        """

        :param from_date:
        :param to_date:
        :return:
        """

    @abstractmethod
    def create_event(self, from_date: datetime, to_date: datetime) -> FocusTimeEvent:
        """

        :param from_date:
        :param to_date:
        :return:
        """

    @abstractmethod
    def update_event(self, event: FocusTimeEvent, from_date: datetime, to_date: datetime, reminder_in_minutes: int):
        """

        :param event:
        :param from_date:
        :param to_date:
        :param reminder_in_minutes:
        :return:
        """
