import sys
from typing import Optional

import typer
from click import Choice

from focus_time_app.cli.background_scheduler import BackgroundSchedulerImpl
from focus_time_app.cli.shell_availability import ShellAvailabilityImpl
from focus_time_app.cli.utils import IntEnumChoice
from focus_time_app.command_execution import CommandExecutorImpl
from focus_time_app.command_execution.abstract_command_executor import CommandExecutorConstants
from focus_time_app.configuration.configuration import ConfigurationV1
from focus_time_app.configuration.persistence import Persistence
from focus_time_app.focus_time_calendar.abstract_calendar_adapter import AbstractCalendarAdapter
from focus_time_app.focus_time_calendar.adapter_factory import create_calendar_adapter
from focus_time_app.focus_time_calendar.event import CalendarType
from focus_time_app.utils import is_production_environment


class ConfigurationCommand:
    def __init__(self, configuration: Optional[ConfigurationV1], calendar_adapter: Optional[AbstractCalendarAdapter],
                 skip_background_scheduler_setup: bool, skip_install_dnd_helper: bool):
        self._configuration = configuration
        self._calendar_adapter = calendar_adapter
        self._skip_background_scheduler_setup = skip_background_scheduler_setup
        self._skip_install_dnd_helper = skip_install_dnd_helper

    def run(self):
        if self._configuration and self._calendar_adapter:
            typer.echo(f"There is already an active configuration stored at {Persistence.get_config_file_path()}")

            ex: Optional[Exception] = None
            try:
                self._calendar_adapter.check_connection_and_credentials()
            except Exception as e:
                ex = e

            if ex:
                typer.echo(f"Unable to establish a working connection to your configured calendar: {ex}")
            else:
                typer.echo("Successfully established a test connection to your configured calendar")

        if not typer.confirm("Do you want to create a new configuration?", default=False, prompt_suffix='\n'):
            return

        if Persistence.get_config_file_path().exists():
            Persistence.get_config_file_path().unlink()
            typer.echo("Deleted old configuration")

        choices = IntEnumChoice(CalendarType)
        calendar_type: CalendarType = typer.prompt(text="Choose your calendar provider", type=choices,
                                                   prompt_suffix='\n')
        configuration = ConfigurationV1(calendar_type=calendar_type, calendar_look_ahead_hours=0,
                                        calendar_look_back_hours=0, focustime_event_name="Foo", start_commands=[],
                                        stop_commands=[], dnd_profile_name="foo",
                                        set_event_reminder=False, event_reminder_time_minutes=0)
        calendar_adapter = create_calendar_adapter(configuration)
        while True:
            adapter_configuration = calendar_adapter.authenticate()
            if adapter_configuration:
                configuration.adapter_configuration = adapter_configuration
                break
            if not typer.confirm("Do you want to try again configuring the calendar provider?", default=True,
                                 prompt_suffix='\n'):
                typer.echo("Aborting the configuration process")
                raise typer.Exit(code=1)

        configuration.focustime_event_name = \
            typer.prompt("What is the title or subject of your Focus time events in your calendar?",
                         default="Focustime", prompt_suffix='\n')
        self._configure_calendar_query_time_interval(configuration)

        self._configure_start_and_stop_commands(configuration)

        self._configure_event_reminders(configuration)

        if not self._skip_install_dnd_helper:
            CommandExecutorImpl.install_dnd_helpers()

        self._configure_dnd_profile_name(configuration)

        if is_production_environment() and not self._skip_background_scheduler_setup:
            BackgroundSchedulerImpl.install_or_repair_background_scheduler()

        if is_production_environment() and not ShellAvailabilityImpl.is_available():
            if typer.confirm("Do you want to make the focus-time binary generally available on your shell (via the "
                             "PATH environment variable)?",
                             default=False, prompt_suffix='\n'):
                try:
                    ShellAvailabilityImpl.make_available()
                    typer.echo("The focus-time binary has been successfully made generally available.")
                    if ShellAvailabilityImpl.requires_shell_restart():
                        typer.echo("Note that for the change to take effect, you first need to close the current shell "
                                   "window and open a new one!")
                except Exception as e:
                    typer.echo(f"An error occurred while trying to make the focus-time binary generally available: {e}")

        Persistence.store_configuration(configuration)

        typer.echo("Configuration completed. You can manually change the configuration by editing the "
                   f"file at '{Persistence.get_config_file_path()}'")

    @staticmethod
    def _configure_calendar_query_time_interval(configuration: ConfigurationV1):
        configuration.calendar_look_back_hours = \
            typer.prompt("When querying your calendar for focus time events, how many hours into the past should "
                         "the query look? Choose a number that is by 1 larger than the longest Focus time event "
                         "duration you will ever create", type=int, default=3, prompt_suffix='\n')
        configuration.calendar_look_ahead_hours = \
            typer.prompt("When querying your calendar for focus time events, how many hours into the future should "
                         "the query look? Choose a number that is at least by 1 larger than the longest Focus time "
                         "event duration you will ever create", type=int, prompt_suffix='\n')

    @staticmethod
    def _configure_start_and_stop_commands(configuration: ConfigurationV1):
        start_cmd_prompt = "Which shell command do you want the Focus Time app to run once a focus time event has started? " \
                           "You can enter multiple commands, if desired. To complete providing commands, just press " \
                           "Enter without providing any input. " \
                           f"Use the magic command '{CommandExecutorConstants.DND_START_COMMAND}' to begin a " \
                           "Do-Not-Disturb session (called 'Focus assist' on Windows, or 'Focus' on macOS)"
        while start_command := typer.prompt(start_cmd_prompt, default='', prompt_suffix='\n'):
            configuration.start_commands.append(start_command)
        stop_cmd_prompt = "Which shell command do you want the Focus Time app to run once a focus time event has ended? " \
                          "You can enter multiple commands, if desired. To complete providing commands, just press " \
                          "Enter without providing any input. " \
                          f"Use the magic command '{CommandExecutorConstants.DND_STOP_COMMAND}' to stop the on-going " \
                          "Do-Not-Disturb session"
        while len(stop_command := typer.prompt(stop_cmd_prompt, default='', prompt_suffix='\n')) > 0:
            configuration.stop_commands.append(stop_command)

    @staticmethod
    def _configure_dnd_profile_name(configuration: ConfigurationV1):
        if sys.platform == "win32":
            prompt = "Please specify the name of the Microsoft Windows Focus Assist profile you want the Focus Time " \
                     "app to use when starting a focus assist session (due to the magic " \
                     f"'{CommandExecutorConstants.DND_START_COMMAND}' command)"
            type_ = Choice(choices=[CommandExecutorConstants.WINDOWS_FOCUS_ASSIST_PRIORITY_ONLY_PROFILE,
                                    CommandExecutorConstants.WINDOWS_FOCUS_ASSIST_ALARMS_ONLY_PROFILE])
            configuration.dnd_profile_name = typer.prompt(prompt, type=type_, prompt_suffix='\n')
        elif sys.platform == "darwin":
            typer.echo(f"To change the name of the macOS Focus profile you want the Focus Time App to use when "
                       f"starting a focus session, open the 'Shortcuts' app and change the "
                       f"focus profile in the '{CommandExecutorConstants.MACOS_FOCUS_MODE_SHORTCUT_NAME}' shortcut")
        else:
            raise NotImplementedError

    @staticmethod
    def _configure_event_reminders(configuration: ConfigurationV1):
        configuration.set_event_reminder = \
            typer.confirm("Do you want the Focus Time app to set a reminder for the focus time calendar events? "
                          "The app will also overwrite the reminder setting for existing(!) focus time events that "
                          "were not created by the app", default=True, prompt_suffix='\n')

        if configuration.set_event_reminder:
            while True:
                configuration.event_reminder_time_minutes = \
                    typer.prompt("How many minutes prior to a focus time calendar event starting should the "
                                 "reminder be shown?", type=int, default=15, prompt_suffix='\n')
                if configuration.event_reminder_time_minutes > 0:
                    break
