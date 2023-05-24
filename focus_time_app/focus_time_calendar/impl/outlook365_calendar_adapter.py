from datetime import datetime
from typing import List, Optional, Dict, Any

import marshmallow_dataclass
import typer
from O365 import Account
from O365.calendar import Schedule
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
            self._outlook_configuration = outlook_configuration_v1_schema.load(configuration.adapter_configuration)
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
            raise ValueError("Unable to load auth token")
        schedule: Schedule = self._account.schedule()
        schedule.list_calendars()

    def get_events(self, from_date: datetime, to_date: datetime) -> List[FocusTimeEvent]:
        pass

    def create_event(self, from_date: datetime, to_date: datetime) -> FocusTimeEvent:
        pass

    def update_event(self, event: FocusTimeEvent, from_date: datetime, to_date: datetime, reminder_in_minutes: int):
        pass
