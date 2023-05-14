from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from calendar.event import FocusTimeEvent


class AbstractCalendarAdapter(ABC):
    @abstractmethod
    def authenticate(self):
        """

        :return:
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
