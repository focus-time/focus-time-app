from focus_time_app.configuration.configuration import ConfigurationV1
from focus_time_app.focus_time_calendar.abstract_calendar_adapter import AbstractCalendarAdapter
from focus_time_app.focus_time_calendar.event import CalendarType
from focus_time_app.focus_time_calendar.impl.outlook365_calendar_adapter import Outlook365CalendarAdapter
from focus_time_app.focus_time_calendar.impl.webdav_calendar_adapter import CaldavCalendarAdapter


def create_calendar_adapter(configuration: ConfigurationV1) -> AbstractCalendarAdapter:
    if configuration.calendar_type is CalendarType.Outlook365:
        return Outlook365CalendarAdapter(configuration=configuration)
    if configuration.calendar_type is CalendarType.CalDAV:
        return CaldavCalendarAdapter(configuration=configuration)
