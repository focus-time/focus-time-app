import re
import time
from os import getenv
from typing import Optional

from O365.calendar import Calendar
from playwright.sync_api import BrowserContext, expect

from focus_time_app.configuration.configuration import ConfigurationV1
from focus_time_app.focus_time_calendar.impl.outlook365_calendar_adapter import Outlook365CalendarAdapter
from tests import OUTLOOK365_TEST_CLIENT_ID
from tests.utils import CI_ENV_NAMESPACE_OVERRIDE
from tests.utils.abstract_testing_calendar_adapter import AbstractTestingCalendarAdapter


def get_outlook365_authorization_code_url(browser_context: BrowserContext, request_url: str) -> str:
    email = getenv("OUTLOOK365_EMAIL", None)
    password = getenv("OUTLOOK365_PASSWORD", None)
    if email is None or password is None:
        raise ValueError("Environment variables OUTLOOK365_EMAIL and OUTLOOK365_PASSWORD must be set")

    authenticated_page_url_pattern = re.compile(r'^https://focus-time\.github\.io/focus-time-app.*')

    page = browser_context.new_page()
    page.goto(request_url)

    try:
        expect(page).to_have_url(authenticated_page_url_pattern)
        return page.url  # happy path, we are already logged in
    except AssertionError:
        pass

    # Fill email, click next
    page.locator('id=i0116').fill(email)
    page.locator('id=idSIButton9').click()

    time.sleep(5)

    # Fill password, click next
    page.locator('id=i0118').fill(password)
    page.locator('id=idSIButton9').click()

    expect(page).to_have_url(authenticated_page_url_pattern)

    return page.url


class Outlook365TestingCalendarAdapter(AbstractTestingCalendarAdapter, Outlook365CalendarAdapter):
    def __init__(self, configuration: ConfigurationV1, browser_context: BrowserContext):
        super().__init__(configuration, environment_namespace_override=CI_ENV_NAMESPACE_OVERRIDE)
        self._browser_context = browser_context

    def _get_client_id(self) -> str:
        return OUTLOOK365_TEST_CLIENT_ID

    def _get_tenant_id(self) -> Optional[str]:
        return None

    def _get_consent_callback(self, consent_url: str) -> str:
        return get_outlook365_authorization_code_url(self._browser_context, consent_url)

    def _get_calendar_name(self, calendars: list[Calendar]) -> str:
        return "Calendar"
