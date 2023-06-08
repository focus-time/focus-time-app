import sys
from pathlib import Path

from focus_time_app.configuration.configuration import ConfigurationV1
from focus_time_app.focus_time_calendar.abstract_calendar_adapter import AbstractCalendarAdapter
from focus_time_app.focus_time_calendar.adapter_factory import create_calendar_adapter
from focus_time_app.focus_time_calendar.utils import compute_calendar_query_start_and_stop


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
