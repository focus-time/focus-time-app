from dataclasses import dataclass
from datetime import datetime, timedelta
from os import getenv
from zoneinfo import ZoneInfo


@dataclass
class CalDavTestCredentials:
    calendar_url: str
    username: str
    password: str

    @staticmethod
    def read_from_env(use_dedicated_unit_test_calendar: bool) -> "CalDavTestCredentials":
        """
        Reads the credentials for a CalDAV test instance from environment variables and returns them.

        We need to differentiate between unit tests and E2E tests (where use_dedicated_unit_test_calendar == False).
        Unit tests do not use any prefixes for the subjects/titles of calendar events, and therefore might interfere
        with E2E tests that are going on at the same time for a different operating system. For instance,
        if using just a single calendar, the macOS UNIT test that tests the CalDAV library might delete events that
        the E2E test (running on Windows) expects. To avoid this kind of interference, there are TWO CalDAV calendars
        set up in the testing Nextcloud instance: one for E2E tests, one for unit tests.
        """
        if use_dedicated_unit_test_calendar:
            calendar_url = getenv("CALDAV_CALENDAR_UNIT_URL", None)
        else:
            calendar_url = getenv("CALDAV_CALENDAR_E2E_URL", None)
        username = getenv("CALDAV_USERNAME", None)
        password = getenv("CALDAV_PASSWORD", None)

        if calendar_url is None or username is None or password is None:
            raise ValueError("Environment variables CALDAV_CALENDAR_UNIT_URL, CALDAV_CALENDAR_E2E_URL, "
                             "CALDAV_USERNAME and CALDAV_PASSWORD must be set")

        return CalDavTestCredentials(calendar_url=calendar_url, username=username, password=password)


OUTLOOK365_TEST_CLIENT_ID = "bcc815bb-01d0-4765-ae14-e2bf0ee22445"


def now_without_micros() -> datetime:
    """
    Helper method that returns a <now> datetime object, but with micro-seconds set to 0, because some calendar
    implementations do not support such a high timestamp accuracy.
    """
    now = datetime.now(ZoneInfo('UTC'))
    if now.microsecond:
        now = now - timedelta(microseconds=now.microsecond)
    return now
