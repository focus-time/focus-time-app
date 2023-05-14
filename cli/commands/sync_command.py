import typer

from calendar.abstract_calendar_adapter import AbstractCalendarAdapter
from calendar.utils import compute_calendar_query_start_and_stop, get_active_focustime_event
from command_execution import CommandExecutorImpl
from configuration.configuration import ConfigurationV1
from configuration.persistence import Persistence


class SyncCommand:
    def __init__(self, configuration: ConfigurationV1, calendar_adapter: AbstractCalendarAdapter):
        self._calendar_adapter = calendar_adapter
        self._configuration = configuration

    def run(self):
        from_date, to_date = compute_calendar_query_start_and_stop(self._configuration)
        events = self._calendar_adapter.get_events(from_date, to_date)
        marker_file_exists = Persistence.ongoing_focustime_markerfile_exists()
        if get_active_focustime_event(events):
            if marker_file_exists:
                typer.echo("Focus time is already active. Exiting ...")
            else:
                typer.echo("Found a new focus time, calling start command(s) ...")
                try:
                    CommandExecutorImpl.execute_commands(self._configuration.start_commands)
                finally:
                    Persistence.set_ongoing_focustime(ongoing=True)

        else:
            if marker_file_exists:
                typer.echo("No focus time is active, calling stop command(s) ...")
                try:
                    CommandExecutorImpl.execute_commands(self._configuration.stop_commands)
                finally:
                    Persistence.set_ongoing_focustime(ongoing=False)
            else:
                typer.echo("No focus time is active. Exiting ...")
