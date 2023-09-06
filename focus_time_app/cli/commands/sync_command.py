import logging
import time
from _zoneinfo import ZoneInfo
from datetime import datetime

import typer

from focus_time_app.command_execution import CommandExecutorImpl
from focus_time_app.configuration.configuration import ConfigurationV1
from focus_time_app.configuration.persistence import Persistence
from focus_time_app.focus_time_calendar.abstract_calendar_adapter import AbstractCalendarAdapter
from focus_time_app.focus_time_calendar.event import FocusTimeEvent
from focus_time_app.focus_time_calendar.utils import get_active_focustime_event
from focus_time_app.utils import human_readable_timedelta
from focus_time_app.utils.os_notification import OsNativeNotificationImpl

NOTIFICATION_TIME_FORMAT = "%H:%M"


class SyncCommand:
    def __init__(self, configuration: ConfigurationV1, calendar_adapter: AbstractCalendarAdapter):
        self._calendar_adapter = calendar_adapter
        self._configuration = configuration
        self._logger = logging.getLogger(type(self).__name__)

    def run(self):
        events = self._calendar_adapter.get_events()
        self._adjust_reminder_time_if_necessary(events)
        marker_file_exists = Persistence.ongoing_focustime_markerfile_exists()
        if active_focustime := get_active_focustime_event(events):
            if marker_file_exists:
                msg = "Focus time is already active. Exiting ..."
                typer.echo(msg)
                self._logger.info(msg)
            else:
                if self._configuration.show_notification:
                    title = "Focus time starts now"
                    remaining_minutes = human_readable_timedelta(active_focustime.end - datetime.now(ZoneInfo('UTC')))
                    message = f"Time remaining: {remaining_minutes} " \
                              f"(until {active_focustime.end.astimezone().strftime(NOTIFICATION_TIME_FORMAT)})"
                    OsNativeNotificationImpl.send_notification(title, message)

                msg = f"Found a new focus time (from {active_focustime.start} to {active_focustime.end}), " \
                      f"calling start command(s) ..."
                typer.echo(msg)
                self._logger.info(msg)
                try:
                    CommandExecutorImpl.execute_commands(self._configuration.start_commands,
                                                         self._configuration.dnd_profile_name)
                finally:
                    Persistence.set_ongoing_focustime(ongoing=True)

        else:
            if marker_file_exists:
                msg = "No focus time is active anymore, calling stop command(s) ..."
                typer.echo(msg)
                self._logger.info(msg)
                try:
                    CommandExecutorImpl.execute_commands(self._configuration.stop_commands,
                                                         self._configuration.dnd_profile_name)

                    if self._configuration.show_notification:
                        title = "Focus time has ended"
                        message = "Your configured stop-commands have been called"
                        OsNativeNotificationImpl.send_notification(title, message)
                finally:
                    Persistence.set_ongoing_focustime(ongoing=False)
            else:
                msg = "No focus time is active. Exiting ..."
                typer.echo(msg)
                self._logger.info(msg)

    def _adjust_reminder_time_if_necessary(self, events: list[FocusTimeEvent]):
        configured_reminder_time = self._configuration.event_reminder_time_minutes \
            if self._configuration.set_event_reminder else 0
        for event in events:
            if configured_reminder_time != event.reminder_in_minutes:
                self._logger.debug(f"Adjusting reminder time of existing focus time event "
                                   f"(start={event.start}, end={event.end}) from {event.reminder_in_minutes} "
                                   f"to {configured_reminder_time} minutes")
                self._calendar_adapter.update_event(event, reminder_in_minutes=configured_reminder_time)
