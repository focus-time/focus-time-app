from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

import marshmallow_dataclass
import typer
from O365 import Account
from O365.calendar import Schedule, Calendar
from click import Choice

from focus_time_app.configuration.configuration import ConfigurationV1, Outlook365ConfigurationV1
from focus_time_app.focus_time_calendar.abstract_calendar_adapter import AbstractCalendarAdapter
from focus_time_app.focus_time_calendar.event import FocusTimeEvent
from focus_time_app.focus_time_calendar.impl.outlook365_keyring_backend import Outlook365KeyringBackend


def consent_input_token(consent_url: str):
    typer.echo("Visit the following url to grant the Focus Time app access to your personal Outlook 365 calendars:")
    typer.echo(consent_url)
    typer.launch(consent_url)
    typer.echo("After you logged into your Microsoft account and granted consent, your browser should have redirected "
               "you to an empty (white) web page")
    return typer.prompt("Please copy the URL from the browser's address bar and paste it here, then press Enter")


outlook_configuration_v1_schema = marshmallow_dataclass.class_schema(Outlook365ConfigurationV1)()


class Outlook365CalendarAdapter(AbstractCalendarAdapter):

    def __init__(self, configuration: ConfigurationV1):
        self._configuration = configuration
        self._outlook_configuration: Optional[Outlook365ConfigurationV1] = None
        if configuration.adapter_configuration is not None:
            self._outlook_configuration: Outlook365ConfigurationV1 = outlook_configuration_v1_schema.load(
                configuration.adapter_configuration)
        self._account: Optional[Account] = None
        self._backend = Outlook365KeyringBackend()

    def authenticate(self) -> Optional[Dict[str, Any]]:
        client_id: str = typer.prompt("Provide the Client ID of your Azure App registration")
        self._account = Account(client_id, auth_flow_type='public', token_backend=self._backend)
        if self._account.authenticate(scopes=['basic', 'calendar_all'], handle_consent=consent_input_token):
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
                calendar_names = [calendar.name for calendar in calendars]
                name_choice = Choice(calendar_names)
                calendar_name = typer.prompt("Please provide the name of your calendar", type=name_choice)

            self._outlook_configuration = Outlook365ConfigurationV1(client_id=client_id, calendar_name=calendar_name)
            return outlook_configuration_v1_schema.dump(self._outlook_configuration)
        else:
            return None

    def check_connection_and_credentials(self):
        if not self._outlook_configuration:
            raise ValueError("Cannot check connection, Outlook configuration is missing")
        self._account = Account(str(self._outlook_configuration.client_id), auth_flow_type='public',
                                token_backend=self._backend)
        if not self._account.is_authenticated:
            raise RuntimeError("Unable to load auth token")
        schedule: Schedule = self._account.schedule()
        schedule.list_calendars()

    def get_events(self, from_date: datetime, to_date: datetime) -> List[FocusTimeEvent]:
        schedule, calendar = self._get_schedule_and_calendar()
        q = calendar.new_query('start').greater_equal(from_date).order_by('start', ascending=True)
        q.chain('and').on_attribute('end').less_equal(to_date)

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
        if self._configuration.event_reminder_time_minutes > 0:
            o365_event.remind_before_minutes = self._configuration.event_reminder_time_minutes

        success = o365_event.save()
        if not success:
            raise RuntimeError("Something went wrong trying to save the Outlook 365 event")

        return FocusTimeEvent(id=o365_event.ical_uid, start=from_date, end=to_date,
                              reminder_in_minutes=self._configuration.event_reminder_time_minutes)

    def update_event(self, event: FocusTimeEvent, from_date: Optional[datetime] = None,
                     to_date: Optional[datetime] = None, reminder_in_minutes: Optional[int] = None):
        schedule, calendar = self._get_schedule_and_calendar()
        q = calendar.new_query('start').greater_equal(event.start)
        q.chain('and').on_attribute('end').less_equal(event.end)
        q.chain('and').on_attribute('iCalUId').equals(event.id)

        o365_events = list(schedule.get_events(query=q))
        if len(o365_events) != 1:
            raise RuntimeError(f"Got unexpected number of events ({len(o365_events)}), expected exactly one")
        o365_event = o365_events[0]
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

    def _get_schedule_and_calendar(self) -> Tuple[Schedule, Calendar]:
        if not self._account:
            raise ValueError("You need to call check_connection_and_credentials() first")

        schedule: Schedule = self._account.schedule()
        calendar = schedule.get_calendar(calendar_name=self._outlook_configuration.calendar_name)
        return schedule, calendar
