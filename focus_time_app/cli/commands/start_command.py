from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import typer

from focus_time_app.configuration.configuration import ConfigurationV1
from focus_time_app.focus_time_calendar.abstract_calendar_adapter import AbstractCalendarAdapter
from focus_time_app.focus_time_calendar.utils import get_active_focustime_event


class StartCommand:
    def __init__(self, configuration: ConfigurationV1, calendar_adapter: AbstractCalendarAdapter,
                 duration_in_minutes: int):
        self._calendar_adapter = calendar_adapter
        self._configuration = configuration
        self._duration_in_minutes = duration_in_minutes

    def run(self):
        events = self._calendar_adapter.get_events()
        if get_active_focustime_event(events):
            typer.echo("Cannot create a new focus time event because there is already one active")
            raise typer.Exit(code=1)

        from_date = datetime.now(ZoneInfo('UTC'))
        to_date = from_date + timedelta(minutes=self._duration_in_minutes)
        self._calendar_adapter.create_event(from_date, to_date)
