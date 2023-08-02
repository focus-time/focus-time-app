import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Callable

import caldav
import icalendar
import marshmallow_dataclass
import pwinput
import typer
from click import Choice

from focus_time_app.configuration.configuration import ConfigurationV1, CaldavConfigurationV1
from focus_time_app.focus_time_calendar.abstract_calendar_adapter import AbstractCalendarAdapter
from focus_time_app.focus_time_calendar.event import FocusTimeEvent
from focus_time_app.focus_time_calendar.impl.keyring_credentials_store import KeyringCredentialsStore
from focus_time_app.utils import USE_INSECURE_PASSWORD_PROMPT_ENV_VAR_NAME


@dataclass
class CaldavTestingOverrides:
    credentials_callback: Callable[[], tuple[str, str]]
    server_url: str
    namespace: str
    calendar_url: str


caldav_configuration_v1_schema = marshmallow_dataclass.class_schema(CaldavConfigurationV1)()


class CaldavCalendarAdapter(AbstractCalendarAdapter):
    """
    Calendar adapter for the CalDAV protocol. The user needs to provide the server URL, username and password.
    """
    _CREDENTIALS_SEPARATOR = "||"

    def __init__(self, configuration: ConfigurationV1, testing_overrides: Optional[CaldavTestingOverrides] = None):
        self._configuration = configuration
        self._testing_overrides = testing_overrides
        self._caldav_configuration: Optional[CaldavConfigurationV1] = None
        if configuration.adapter_configuration is not None:
            self._caldav_configuration: CaldavConfigurationV1 = caldav_configuration_v1_schema.load(
                configuration.adapter_configuration)
        self._username = ""
        self._password = ""
        self._caldav_calendar: Optional[caldav.Calendar] = None
        namespace_override = None if testing_overrides is None else testing_overrides.namespace
        self._credentials_store = KeyringCredentialsStore(namespace_override=namespace_override)

    def authenticate(self) -> Optional[Dict[str, Any]]:
        server_url_override = None if self._testing_overrides is None else self._testing_overrides.server_url
        server_url: str = server_url_override or \
                          typer.prompt("Provide the CalDAV URL", prompt_suffix='\n')
        credentials_callback = self._testing_overrides.credentials_callback if self._testing_overrides is not None \
            else self._get_credentials_input
        self._username, self._password = credentials_callback()

        client = caldav.DAVClient(url=server_url, username=self._username, password=self._password)
        try:
            principal = client.principal()
            calendars = principal.calendars()
            if len(calendars) == 0:
                typer.echo("Your account does not have any calendars - aborting ...")
                return None
            elif len(calendars) == 1:
                typer.echo(f"Found only one calendar named '{calendars[0].name}', which will be chosen")
                calendar_url = str(calendars[0].url)
                self._caldav_calendar = calendars[0]
            else:
                if self._testing_overrides is not None:
                    calendar_url = self._testing_overrides.calendar_url
                else:
                    calendar_names = [calendar.name for calendar in calendars]
                    name_choice = Choice(calendar_names)
                    calendar_name = typer.prompt("Please provide the name of your calendar", type=name_choice,
                                                 prompt_suffix='\n')
                    calendar_url = [str(c.url) for c in calendars if c.name == calendar_name][0]
                    self._caldav_calendar = [c for c in calendars if c.name == calendar_name][0]

            self._save_credentials()
            self._caldav_configuration = CaldavConfigurationV1(calendar_url=calendar_url)
            return caldav_configuration_v1_schema.dump(self._caldav_configuration)
        except Exception as e:
            # TODO check for more specific errors
            typer.echo(f"Unable to authenticate: {e}")
            return None

    def check_connection_and_credentials(self):
        # can use calendar.get_supported_components() to verify that the URL and credentials work
        if not self._caldav_configuration:
            raise ValueError("Cannot check connection, CalDAV configuration is missing")

        self._load_credentials()
        client = caldav.DAVClient(url=self._caldav_configuration.calendar_url, username=self._username,
                                  password=self._password)
        principal = client.principal()  # verifies the credentials
        self._caldav_calendar = principal.calendar(cal_url=self._caldav_configuration.calendar_url)
        self._caldav_calendar.get_supported_components()  # verifies the calendar URL

    def get_events(self, from_date: datetime, to_date: datetime) -> List[FocusTimeEvent]:
        caldav_events = self._caldav_calendar.search(start=from_date, end=to_date, event=True, expand=True,
                                                     sort_keys=("dtstart",))
        events_filtered = [e for e in caldav_events if
                           self._get_event_subject(e) == self._configuration.focustime_event_name]

        events: List[FocusTimeEvent] = []

        for caldav_event in events_filtered:
            events.append(self._get_focustime_event_from_caldav(caldav_event))

        return events

    def create_event(self, from_date: datetime, to_date: datetime) -> FocusTimeEvent:
        event = self._caldav_calendar.save_event(dtstart=from_date, dtend=to_date,
                                                 summary=self._configuration.focustime_event_name)

        reminder_in_minutes = 0
        if self._configuration.set_event_reminder and self._configuration.event_reminder_time_minutes > 0:
            self._add_reminder_to_event_and_save(event)
            reminder_in_minutes = self._configuration.event_reminder_time_minutes

        return FocusTimeEvent(id=event.icalendar_component["uid"], start=from_date, end=to_date,
                              reminder_in_minutes=reminder_in_minutes)

    def update_event(self, event: FocusTimeEvent, from_date: Optional[datetime] = None,
                     to_date: Optional[datetime] = None, reminder_in_minutes: Optional[int] = None):
        caldav_event = self._caldav_calendar.event_by_uid(event.id)

        if from_date:
            caldav_event.icalendar_component["dtstart"].dt = from_date
        if to_date:
            caldav_event.icalendar_component["dtend"].dt = to_date
        if reminder_in_minutes is not None:
            self._remove_all_reminders_and_save(caldav_event)
            if reminder_in_minutes > 0:
                self._add_reminder_to_event_and_save(caldav_event)

        caldav_event.save()

    def remove_event(self, event: FocusTimeEvent):
        caldav_event = self._caldav_calendar.event_by_uid(event.id)
        caldav_event.delete()

    @staticmethod
    def _get_credentials_input() -> tuple[str, str]:
        username = typer.prompt("Please provide your username", prompt_suffix='\n')
        if os.getenv(USE_INSECURE_PASSWORD_PROMPT_ENV_VAR_NAME, None) is not None:
            # In automated tests, writing to the CLI's "stdin" won't work when using secure password prompt methods
            # (such as pwinput() or getpass()), thus we use normal (insecure) input-reading instead
            password = typer.prompt("Please provide your password", prompt_suffix='\n')
        else:
            password = pwinput.pwinput("Please provide your password:\n")
        return username, password

    def _save_credentials(self):
        try:
            self._credentials_store.delete_credentials()  # delete outdated credentials, for good measure
        except:
            pass

        credentials_string = self._username + self._CREDENTIALS_SEPARATOR + self._password
        self._credentials_store.save_credentials(credentials_string)

    def _load_credentials(self):
        credentials = self._credentials_store.load_credentials()
        if not credentials:
            raise ValueError("CalDAV credentials are missing")

        creds_list = credentials.split(self._CREDENTIALS_SEPARATOR, maxsplit=1)
        if len(creds_list) != 2:
            self._credentials_store.delete_credentials()
            raise ValueError(f"Invalid CalDAV credentials, number of elements is {len(creds_list)} but expected two")

        self._username, self._password = creds_list

    @staticmethod
    def _get_event_subject(e: caldav.CalendarObjectResource) -> str:
        return e.icalendar_component["summary"]

    @staticmethod
    def _get_focustime_event_from_caldav(e: caldav.CalendarObjectResource) -> FocusTimeEvent:
        reminder_minutes = 0
        for subcomponent in e.icalendar_component.subcomponents:
            if isinstance(subcomponent, icalendar.Alarm):
                reminder_minutes_td: timedelta = subcomponent["TRIGGER"].dt
                reminder_minutes = -1 * reminder_minutes_td.total_seconds() // 60
        return FocusTimeEvent(id=e.icalendar_component["uid"], start=e.icalendar_component["dtstart"].dt,
                              end=e.icalendar_component["dtend"].dt, reminder_in_minutes=reminder_minutes)

    def _add_reminder_to_event_and_save(self, event: caldav.CalendarObjectResource):
        ia = icalendar.Alarm()
        ia.add("action", "DISPLAY")
        ia.add("trigger", timedelta(minutes=-1 * self._configuration.event_reminder_time_minutes))
        event.icalendar_component.add_component(ia)
        event.save()

    @staticmethod
    def _remove_all_reminders_and_save(event: caldav.CalendarObjectResource):
        alarm_subcomponents = []
        for subcomponent in event.icalendar_component.subcomponents:
            if isinstance(subcomponent, icalendar.Alarm):
                alarm_subcomponents.append(subcomponent)

        if alarm_subcomponents:
            for alarm_subcomponent in alarm_subcomponents:
                event.icalendar_component.subcomponents.remove(alarm_subcomponent)
            event.save()
