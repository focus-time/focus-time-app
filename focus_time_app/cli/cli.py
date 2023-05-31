from typing import Tuple, Annotated

import typer

from focus_time_app.cli.commands.uninstall_command import UninstallCommand
from focus_time_app.focus_time_calendar.abstract_calendar_adapter import AbstractCalendarAdapter
from focus_time_app.focus_time_calendar.adapter_factory import create_calendar_adapter
from focus_time_app.cli.commands.configuration_command import ConfigurationCommand
from focus_time_app.cli.commands.start_command import StartCommand
from focus_time_app.cli.commands.stop_command import StopCommand
from focus_time_app.cli.commands.sync_command import SyncCommand
from focus_time_app.configuration.configuration import ConfigurationV1
from focus_time_app.configuration.persistence import Persistence

app = typer.Typer(help="CLI tool that triggers your desktop OS's Do-Not-Disturb feature (and other arbitrary scripts), "
                       "based on blocker events on your calendar. ")

NO_CONFIG_FILE_ERROR_MSG = "For this command to work, you first need to run the 'configure' command " \
                           "to set the necessary configuration!"


def _load_configuration_and_adapter() -> Tuple[ConfigurationV1, AbstractCalendarAdapter]:
    """
    Attempts to load the configuration of this app from disk and return it, together with the implementation of the
    calendar adapter.

    If no configuration file could be found, a FileNotFoundError is raised. If anything else goes wrong, other
    errors are raised.
    """
    configuration = Persistence.load_configuration()
    calendar_adapter = create_calendar_adapter(configuration)
    return configuration, calendar_adapter


def _check_adapter_is_valid_or_exit(adapter: AbstractCalendarAdapter):
    try:
        adapter.check_connection_and_credentials()
    except Exception as e:
        typer.echo(f"Could not establish a valid connection to your calendar (are the credentials valid?): {e}")
        raise typer.Exit(code=1) from None


@app.command()
def sync():
    """
    Synchronizes the Do-Not-Disturb state of your local machine with your focus time calendar events. If there is an
    active focus time calendar event, the Do-Not-Disturb mode (and other start commands you configured) is activated
    (unless this app already recently activated it). If there is no active calendar event (anymore), Do-Not-Disturb is
    deactivated again (if this app has set it), and other possibly configured stop commands are called.
    """
    try:
        config, calendar_adapter = _load_configuration_and_adapter()
    except FileNotFoundError:  # Note: other exceptions might be raised
        typer.echo(NO_CONFIG_FILE_ERROR_MSG)
        raise typer.Exit(code=1)

    _check_adapter_is_valid_or_exit(calendar_adapter)

    SyncCommand(config, calendar_adapter).run()


@app.command()
def start(duration: Annotated[int, typer.Option(min=1, help="")]):
    """
    Creates a new focus time calendar event in your calendar that starts now and ends in <duration> minutes. Also
    runs the 'sync' command internally, so that your start command(s) are immediately executed.
    """
    try:
        config, calendar_adapter = _load_configuration_and_adapter()
    except FileNotFoundError:  # Note: other exceptions might be raised
        typer.echo(NO_CONFIG_FILE_ERROR_MSG)
        raise typer.Exit(code=1)

    _check_adapter_is_valid_or_exit(calendar_adapter)

    StartCommand(config, calendar_adapter, duration).run()
    SyncCommand(config, calendar_adapter).run()


@app.command()
def stop():
    """
    Stops an ongoing focus time calendar event, by shortening it so that it ends right now. Also runs the 'sync'
    command internally, so that your stop command(s) are immediately executed.
    """
    try:
        config, calendar_adapter = _load_configuration_and_adapter()
    except FileNotFoundError:  # Note: other exceptions might be raised
        typer.echo(NO_CONFIG_FILE_ERROR_MSG)
        raise typer.Exit(code=1)

    _check_adapter_is_valid_or_exit(calendar_adapter)

    StopCommand(config, calendar_adapter).run()
    SyncCommand(config, calendar_adapter).run()


@app.command()
def configure(skip_background_scheduler_setup: Annotated[
    bool, typer.Option(help="Whether to skip the set up of operating-system-specific background "
                            "scheduler that regularly calls the 'sync' command")
] = False):
    """
    Checks the existing configuration for validity and lets you create a new configuration. All configuration options
    are interactively prompted.
    """
    try:
        config, calendar_adapter = _load_configuration_and_adapter()
    except FileNotFoundError:  # Note: other exceptions might be raised
        config = calendar_adapter = None

    ConfigurationCommand(config, calendar_adapter, skip_background_scheduler_setup).run()


@app.command()
def uninstall():
    """
    Removes scheduled background jobs and Do-Not-Disturb helpers, if the operating system supports the removal.
    """
    UninstallCommand().run()
