from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any

from focus_time_app.focus_time_calendar.event import FocusTimeEvent


class AbstractCalendarAdapter(ABC):
    """
    Abstraction over concrete online calendar providers, such as Outlook 365, GMail, etc.
    """

    @abstractmethod
    def authenticate(self) -> Optional[Dict[str, Any]]:
        """
        Interactively queries the user for information (in the terminal) necessary to access events from the calendar.
        Typically involves asking for some application ID (e.g. OAuth Client ID), endpoint URLs, or the name of the
        calendar (in case the user account contains multiple calendars).

        Is not expected to raise errors, but instead print user-friendly error descriptions to <stdout>.

        :return: Dict that contains the adapter-specific configuration (if authentication was successful),
            None otherwise
        """

    @abstractmethod
    def check_connection_and_credentials(self):
        """
        Verifies that the connection to the calendar server can be established and that the cached credentials are
        still valid. Raises an error if something goes wrong.
        """

    @abstractmethod
    def get_events(self, date_range: Optional[tuple[datetime, datetime]] = None) -> list[FocusTimeEvent]:
        """
        Retrieves all focus time calendar events, sorted by ascending start time. By default, the range is computed
        from the Configuration object. Otherwise, a tuple of the start and end time is expected, and events with a
        start date >= date_range[0] and end date <= date_range[1] are returned.
        """

    @abstractmethod
    def create_event(self, from_date: datetime, to_date: datetime) -> FocusTimeEvent:
        """
        Creates a new focus time calendar event that starts at from_date and ends at to_date.
        Configures values from the configuration, such as event_reminder_time_minutes.
        """

    @abstractmethod
    def update_event(self, event: FocusTimeEvent, from_date: Optional[datetime] = None,
                     to_date: Optional[datetime] = None, reminder_in_minutes: Optional[int] = None):
        """
        Updates an existing focus time calendar event, for all those fields that are not None.

        :param event: the event to update
        :param from_date: new start date/time
        :param to_date: new end date/time
        :param reminder_in_minutes: whether to configure a reminder
        """

    @abstractmethod
    def remove_event(self, event: FocusTimeEvent):
        """
        Deletes an existing focus time calendar event.

        :param event: the event to delete
        """
