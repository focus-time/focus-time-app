from os import getenv

from O365.calendar import Calendar
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from focus_time_app.configuration.configuration import ConfigurationV1
from focus_time_app.focus_time_calendar.impl.outlook365_calendar_adapter import Outlook365CalendarAdapter
from focus_time_calendar.impl.outlook365_calendar_adapter import OUTLOOK365_REDIRECT_URL
from tests import OUTLOOK365_TEST_CLIENT_ID
from tests.utils import CI_ENV_NAMESPACE_OVERRIDE
from tests.utils.abstract_testing_calendar_adapter import AbstractTestingCalendarAdapter


def get_outlook365_authorization_code_url(request_url: str) -> str:
    EMAILFIELD = (By.ID, "i0116")
    PASSWORDFIELD = (By.ID, "i0118")
    NEXTBUTTON = (By.ID, "idSIButton9")

    email = getenv("OUTLOOK365_EMAIL", None)
    password = getenv("OUTLOOK365_PASSWORD", None)
    if email is None or password is None:
        raise ValueError("Environment variables OUTLOOK365_EMAIL and OUTLOOK365_PASSWORD must be set")

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    driver.get('https://login.live.com')

    # wait for email field and enter email
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(EMAILFIELD)).send_keys(email)
    # Click Next
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(NEXTBUTTON)).click()

    # wait for password field
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(PASSWORDFIELD)).send_keys(password)
    # Click Next
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(NEXTBUTTON)).click()

    driver.get(request_url)
    WebDriverWait(driver, 10).until(EC.url_matches(OUTLOOK365_REDIRECT_URL))
    return driver.current_url


class Outlook365TestingCalendarAdapter(AbstractTestingCalendarAdapter, Outlook365CalendarAdapter):
    def __init__(self, configuration: ConfigurationV1):
        super().__init__(configuration, environment_namespace_override=CI_ENV_NAMESPACE_OVERRIDE)

    def _get_client_id(self) -> str:
        return OUTLOOK365_TEST_CLIENT_ID

    def _get_consent_callback(self, consent_url: str) -> str:
        return get_outlook365_authorization_code_url(consent_url)

    def _get_calendar_name(self, calendars: list[Calendar]) -> str:
        return "Calendar"
