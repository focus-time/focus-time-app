from dataclasses import dataclass
from os import getenv


@dataclass
class CalDavTestCredentials:
    calendar_url: str
    username: str
    password: str

    @staticmethod
    def read_from_env() -> "CalDavTestCredentials":
        calendar_url = getenv("CALDAV_CALENDAR_URL", None)
        username = getenv("CALDAV_USERNAME", None)
        password = getenv("CALDAV_PASSWORD", None)
        if calendar_url is None or username is None or password is None:
            raise ValueError("Environment variables CALDAV_CALENDAR_URL, CALDAV_USERNAME and CALDAV_PASSWORD "
                             "must be set")

        return CalDavTestCredentials(calendar_url=calendar_url, username=username, password=password)


OUTLOOK365_TEST_CLIENT_ID = "bcc815bb-01d0-4765-ae14-e2bf0ee22445"
