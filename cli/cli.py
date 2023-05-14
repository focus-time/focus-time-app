# TODO helpful stuff from Typer
# raise typer.Exit()
# typer.get_app_dir()
# typer.launch("https://typer.tiangolo.com")
from typing import Tuple, Annotated

import typer

from calendar.abstract_calendar_adapter import AbstractCalendarAdapter
from calendar.adapter_factory import create_calendar_adapter
from cli.commands.configuration_command import ConfigurationCommand
from cli.commands.start_command import StartCommand
from cli.commands.stop_command import StopCommand
from cli.commands.sync_command import SyncCommand
from configuration.configuration import ConfigurationV1
from configuration.persistence import Persistence

app = typer.Typer()  # TODO add configuration, e.g. help text

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
    TODO docs
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
    Creates a new focus time event in your calendar that starts now and ends in <duration> minutes. Also runs the
    'sync' command internally, so that your start command(s) are immediately executed.
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
    Stops an ongoing focus time event, by shortening it so that it ends right now. Also runs the
    'sync' command internally, so that your stop command(s) are immediately executed.
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
def configure():
    """
    TODO docs
    """
    try:
        config, calendar_adapter = _load_configuration_and_adapter()
    except FileNotFoundError:  # Note: other exceptions might be raised
        config = calendar_adapter = None

    ConfigurationCommand(config, calendar_adapter).run()

# TODO: create an "uninstall" command?
