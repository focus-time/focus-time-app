from datetime import datetime
from zoneinfo import ZoneInfo

import typer

from focus_time_app.configuration.configuration import ConfigurationV1
from focus_time_app.focus_time_calendar.abstract_calendar_adapter import AbstractCalendarAdapter
from focus_time_app.focus_time_calendar.utils import get_active_focustime_event


class StopCommand:
    def __init__(self, configuration: ConfigurationV1, calendar_adapter: AbstractCalendarAdapter):
        self._calendar_adapter = calendar_adapter
        self._configuration = configuration

    def run(self):
        events = self._calendar_adapter.get_events()
        active_focustime_event = get_active_focustime_event(events)
        if not active_focustime_event:
            typer.echo("There is no ongoing focus time event, therefore the focus time cannot be stopped")
            raise typer.Exit(code=1)

        date_now = datetime.now(ZoneInfo('UTC'))
        self._calendar_adapter.update_event(active_focustime_event, to_date=date_now)
