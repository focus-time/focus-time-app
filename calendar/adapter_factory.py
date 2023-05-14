from calendar.abstract_calendar_adapter import AbstractCalendarAdapter
from calendar.event import CalendarType
from calendar.impl.outlook365_calendar_adapter import Outlook365CalendarAdapter
from configuration.configuration import ConfigurationV1


def create_calendar_adapter(configuration: ConfigurationV1) -> AbstractCalendarAdapter:
    if configuration.calendar_type is CalendarType.Outlook365:
        return Outlook365CalendarAdapter(configuration=configuration)
