from datetime import datetime
from zoneinfo import ZoneInfo

import typer

from calendar.abstract_calendar_adapter import AbstractCalendarAdapter
from calendar.utils import compute_calendar_query_start_and_stop, get_active_focustime_event
from configuration.configuration import ConfigurationV1


class StopCommand:
    def __init__(self, configuration: ConfigurationV1, calendar_adapter: AbstractCalendarAdapter):
        self._calendar_adapter = calendar_adapter
        self._configuration = configuration

    def run(self):
        from_date, to_date = compute_calendar_query_start_and_stop(self._configuration)
        events = self._calendar_adapter.get_events(from_date, to_date)
        active_focustime_event = get_active_focustime_event(events)
        if not active_focustime_event:
            typer.echo("There is no ongoing focus time event, therefore the focus time cannot be stopped")
            raise typer.Exit(code=1)

        date_now = datetime.now(ZoneInfo('UTC'))
        self._calendar_adapter.update_event(active_focustime_event, to_date=date_now)
