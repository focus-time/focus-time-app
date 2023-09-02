import os
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

import marshmallow_dataclass
import pytz
import typer
from O365 import Account
from O365.calendar import Schedule, Calendar, Event
from click import Choice

from focus_time_app.configuration.configuration import ConfigurationV1, Outlook365ConfigurationV1
from focus_time_app.focus_time_calendar.abstract_calendar_adapter import AbstractCalendarAdapter
from focus_time_app.focus_time_calendar.event import FocusTimeEvent
from focus_time_app.focus_time_calendar.impl.outlook365_keyring_backend import Outlook365KeyringBackend
from focus_time_app.focus_time_calendar.utils import compute_calendar_query_start_and_stop
from focus_time_app.utils import CI_ENV_VAR_NAME

OUTLOOK365_REDIRECT_URL = "https://focus-time.github.io/focus-time-app"
OUTLOOK365_OAUTH_COMMON_TENANT = "common"

outlook_configuration_v1_schema = marshmallow_dataclass.class_schema(Outlook365ConfigurationV1)()


class Outlook365CalendarAdapter(AbstractCalendarAdapter):

    def __init__(self, configuration: ConfigurationV1, environment_namespace_override: Optional[str] = None):
        self._configuration = configuration
        self._outlook_configuration: Optional[Outlook365ConfigurationV1] = None
        if configuration.adapter_configuration is not None:
            self._outlook_configuration: Outlook365ConfigurationV1 = outlook_configuration_v1_schema.load(
                configuration.adapter_configuration)
        self._account: Optional[Account] = None
        self._backend = Outlook365KeyringBackend(environment_namespace_override)

    def authenticate(self) -> Optional[Dict[str, Any]]:
        client_id = self._get_client_id()
        tenant_id = self._get_tenant_id()
        self._account = Account(client_id, auth_flow_type="public", token_backend=self._backend,
                                tenant_id=tenant_id or OUTLOOK365_OAUTH_COMMON_TENANT)
        if self._account.authenticate(scopes=["basic", "calendar_all"], handle_consent=self._get_consent_callback,
                                      redirect_uri=OUTLOOK365_REDIRECT_URL):
            typer.echo("Retrieving the list of calendars ...")
            schedule: Schedule = self._account.schedule()
            calendars = schedule.list_calendars()
            if len(calendars) == 0:
                typer.echo("Your account does not have any calendars - aborting ...")
                return None
            elif len(calendars) == 1:
                calendar_name = calendars[0].name
                typer.echo(f"Found only one calendar named '{calendar_name}', which will be chosen")
            else:
                calendar_name = self._get_calendar_name(calendars)

            self._outlook_configuration = Outlook365ConfigurationV1(client_id=client_id, tenant_id=tenant_id,
                                                                    calendar_name=calendar_name)
            return outlook_configuration_v1_schema.dump(self._outlook_configuration)
        else:
            return None

    def check_connection_and_credentials(self):
        if not self._outlook_configuration:
            raise ValueError("Cannot check connection, Outlook configuration is missing")
        # Note: we set the "timezone=pytz.UTC" argument only to avoid PytzUsageWarning that point to
        # https://pytz-deprecation-shim.readthedocs.io/en/latest/migration.html
        # The issue is known (https://github.com/O365/python-o365/issues/753) but unlikely to be fixed soon
        self._account = Account(str(self._outlook_configuration.client_id), auth_flow_type="public",
                                token_backend=self._backend, timezone=pytz.UTC,
                                tenant_id=self._outlook_configuration.tenant_id or OUTLOOK365_OAUTH_COMMON_TENANT)
        if not self._account.is_authenticated:
            raise RuntimeError("Unable to load auth token")
        schedule: Schedule = self._account.schedule()
        schedule.list_calendars()

    def get_events(self, date_range: Optional[tuple[datetime, datetime]] = None) -> list[FocusTimeEvent]:
        schedule, calendar = self._get_schedule_and_calendar()
        if date_range:
            from_date, to_date = date_range
        else:
            from_date, to_date = compute_calendar_query_start_and_stop(self._configuration)

        q = calendar.new_query("start").greater_equal(from_date).order_by("start", ascending=True)
        q.chain("and").on_attribute("end").less_equal(to_date)
        q.chain("and").on_attribute("subject").equals(self._configuration.focustime_event_name)

        events: List[FocusTimeEvent] = []
        o365_events = schedule.get_events(query=q)
        for o365_event in o365_events:
            reminder_in_minutes = o365_event.remind_before_minutes if o365_event.is_reminder_on else 0
            event = FocusTimeEvent(id=o365_event.ical_uid, start=o365_event.start, end=o365_event.end,
                                   reminder_in_minutes=reminder_in_minutes)
            events.append(event)

        return events

    def create_event(self, from_date: datetime, to_date: datetime) -> FocusTimeEvent:
        schedule, calendar = self._get_schedule_and_calendar()
        o365_event = calendar.new_event(subject=self._configuration.focustime_event_name)
        o365_event.start = from_date
        o365_event.end = to_date
        if self._configuration.set_event_reminder and self._configuration.event_reminder_time_minutes > 0:
            o365_event.remind_before_minutes = self._configuration.event_reminder_time_minutes
        else:
            o365_event.is_reminder_on = False

        success = o365_event.save()
        if not success:
            raise RuntimeError("Something went wrong trying to save the Outlook 365 event")

        return FocusTimeEvent(id=o365_event.ical_uid, start=from_date, end=to_date,
                              reminder_in_minutes=self._configuration.event_reminder_time_minutes)

    def update_event(self, event: FocusTimeEvent, from_date: Optional[datetime] = None,
                     to_date: Optional[datetime] = None, reminder_in_minutes: Optional[int] = None):
        o365_event = self._find_event(event)
        if from_date:
            o365_event.start = from_date
        if to_date:
            o365_event.end = to_date
        if reminder_in_minutes is not None:
            if reminder_in_minutes > 0:
                o365_event.remind_before_minutes = reminder_in_minutes
            else:
                o365_event.is_reminder_on = False

        success = o365_event.save()
        if not success:
            raise RuntimeError("Something went wrong trying to update the Outlook 365 event")

    def remove_event(self, event: FocusTimeEvent):
        o365_event = self._find_event(event)
        success = o365_event.delete()
        if not success:
            raise RuntimeError("Something went wrong trying to delete the Outlook 365 event")

    def _find_event(self, event: FocusTimeEvent) -> Event:
        schedule, calendar = self._get_schedule_and_calendar()
        q = calendar.new_query("start").greater_equal(event.start)
        q.chain("and").on_attribute("end").less_equal(event.end)
        q.chain("and").on_attribute("iCalUId").equals(event.id)
        q.chain("and").on_attribute("subject").equals(self._configuration.focustime_event_name)

        o365_events = list(schedule.get_events(query=q))
        if len(o365_events) != 1:
            raise RuntimeError(f"Got unexpected number of events ({len(o365_events)}), expected exactly one")
        return o365_events[0]

    def _get_schedule_and_calendar(self) -> Tuple[Schedule, Calendar]:
        if not self._account:
            raise ValueError("You need to call check_connection_and_credentials() first")

        schedule: Schedule = self._account.schedule()
        calendar = schedule.get_calendar(calendar_name=self._outlook_configuration.calendar_name)
        return schedule, calendar

    def _get_client_id(self) -> str:
        return typer.prompt("Provide the Client ID of your Azure App registration", prompt_suffix='\n')

    def _get_tenant_id(self) -> Optional[str]:
        if not typer.confirm("Does your Azure App registration belong to a custom tenant of which you know the ID?",
                             default=False, prompt_suffix='\n'):
            return None
        return typer.prompt("Provide the tenant ID", prompt_suffix='\n')

    def _get_consent_callback(self, consent_url: str) -> str:
        typer.echo("Visit the following url to grant the Focus Time app access to your personal Outlook 365 calendars:")
        typer.echo(consent_url)
        if os.getenv(CI_ENV_VAR_NAME, None) is None:
            typer.launch(consent_url)
        typer.echo(
            "After you logged into your Microsoft account and granted consent, your browser should have redirected "
            "you to a web page that shows the code that you need to paste here")
        pasted_code: str = typer.prompt("On the page, please click the 'Copy' button, then "
                                        "paste the clipboard content here, then press Enter", prompt_suffix='\n')

        # On macOS, the Terminal only allows pasting content with up to 1024 characters. When the Azure app
        # registration requires a tenant, the returned URL (that contains the OAuth authorization code) has 1046
        # characters. We work around this problem by omitting the value of OUTLOOK365_REDIRECT_URL (43 chars) in the
        # pasted content, adding it here. This saves just enough characters to stay below the 1024 limit.
        if not pasted_code.startswith(OUTLOOK365_REDIRECT_URL):
            return OUTLOOK365_REDIRECT_URL + "/" + pasted_code
        return pasted_code

    def _get_calendar_name(self, calendars: list[Calendar]) -> str:
        calendar_names = [calendar.name for calendar in calendars]
        name_choice = Choice(calendar_names)
        return typer.prompt("Please provide the name of your calendar", type=name_choice,
                            prompt_suffix='\n')
