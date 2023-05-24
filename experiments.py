from focus_time_app.focus_time_calendar.event import CalendarType
from focus_time_app.configuration import ConfigurationV1
from focus_time_app.configuration import Persistence

config = ConfigurationV1(calendar_type=CalendarType.Outlook365, calendar_look_ahead_hours=4, calendar_look_back_hours=5,
                         focustime_event_name="foo", start_commands=["foo"], stop_commands=["bar"],
                         focustime_os_profile_name="foo", adjust_event_reminder_time=False, event_reminder_time_minutes=3)
Persistence.store_configuration(config)
cfg = Persistence.load_configuration()
i = 2
