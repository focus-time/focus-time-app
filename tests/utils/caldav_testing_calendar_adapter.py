import caldav

from focus_time_app.configuration.configuration import ConfigurationV1
from focus_time_app.focus_time_calendar.impl.webdav_calendar_adapter import CaldavCalendarAdapter
from tests import CalDavTestCredentials
from tests.utils import CI_ENV_NAMESPACE_OVERRIDE
from tests.utils.abstract_testing_calendar_adapter import AbstractTestingCalendarAdapter


class CaldavTestingCalendarAdapter(AbstractTestingCalendarAdapter, CaldavCalendarAdapter):
    def __init__(self, configuration: ConfigurationV1):
        super().__init__(configuration, environment_namespace_override=CI_ENV_NAMESPACE_OVERRIDE)
        self._test_credentials = CalDavTestCredentials.read_from_env()

    def _get_server_url(self) -> str:
        return self._test_credentials.calendar_url

    def _get_credentials(self) -> tuple[str, str]:
        return self._test_credentials.username, self._test_credentials.password

    def _get_calendar(self, calendars: list[caldav.Calendar]) -> caldav.Calendar:
        return [c for c in calendars if str(c.url) == self._test_credentials.calendar_url][0]



