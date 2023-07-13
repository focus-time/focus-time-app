import string
import random
import subprocess
import sys
from pathlib import Path
from typing import Optional

from focus_time_app.configuration.configuration import ConfigurationV1
from focus_time_app.focus_time_calendar.abstract_calendar_adapter import AbstractCalendarAdapter
from focus_time_app.focus_time_calendar.adapter_factory import create_calendar_adapter
from focus_time_app.focus_time_calendar.utils import compute_calendar_query_start_and_stop


def get_random_event_name_postfix() -> str:
    source = string.ascii_letters + string.digits
    return ''.join((random.choice(source) for i in range(8)))


def get_frozen_binary_path() -> str:
    binary_ext = ".exe" if sys.platform == "win32" else ""
    return str(Path(__file__).parent.parent / "dist" / "focus-time" / f"focus-time{binary_ext}")


def get_configured_calendar_adapter(configuration: ConfigurationV1) -> AbstractCalendarAdapter:
    calendar_adapter = create_calendar_adapter(configuration)
    calendar_adapter.check_connection_and_credentials()
    return calendar_adapter


def clean_calendar(configuration: ConfigurationV1, calendar_adapter: AbstractCalendarAdapter):
    from_date, to_date = compute_calendar_query_start_and_stop(configuration)

    events = calendar_adapter.get_events(from_date, to_date)
    for event in events:
        calendar_adapter.remove_event(event)


def run_cli_command_handle_output_error(cli_command: str, additional_args: Optional[list[str]] = None):
    try:
        command_and_args = [get_frozen_binary_path(), cli_command]
        if additional_args:
            command_and_args.extend(additional_args)
        finished_process = subprocess.run(command_and_args, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        # Handle the error explicitly, because the stringification of CalledProcessError does not include stdout
        # or stderr, which is very useful for diagnosing errors
        raise RuntimeError(
            f"Encountered CalledProcessError: {e}.\nStdout:\n{e.stdout.decode('utf-8')}"
            f"\n\nStderr:\n{e.stderr.decode('utf-8')}") from None
    return finished_process.stdout.decode("utf-8")
