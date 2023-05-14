from typing import Optional

from calendar.abstract_calendar_adapter import AbstractCalendarAdapter
from configuration.configuration import ConfigurationV1


class ConfigurationCommand:
    def __init__(self, configuration: Optional[ConfigurationV1], calendar_adapter: Optional[AbstractCalendarAdapter]):
        pass

    def run(self):
        pass
