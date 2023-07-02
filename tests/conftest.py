import subprocess
import sys
from dataclasses import dataclass
from os import getenv
from pathlib import Path
from subprocess import Popen
from typing import IO, Any, List

import marshmallow_dataclass
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from focus_time_app.cli.background_scheduler import BackgroundSchedulerImpl
from focus_time_app.command_execution import CommandExecutorImpl
from focus_time_app.command_execution.abstract_command_executor import CommandExecutorConstants
from focus_time_app.configuration.configuration import ConfigurationV1, Outlook365ConfigurationV1
from focus_time_app.configuration.persistence import Persistence
from focus_time_app.focus_time_calendar.abstract_calendar_adapter import AbstractCalendarAdapter
from focus_time_app.focus_time_calendar.event import CalendarType
from focus_time_app.focus_time_calendar.impl.outlook365_calendar_adapter import Outlook365CalendarAdapter, \
    Outlook365TestingOverrides
from tests.test_utils import get_frozen_binary_path, clean_calendar, get_random_event_name_postfix

OUTLOOK365_TEST_CLIENT_ID = "bcc815bb-01d0-4765-ae14-e2bf0ee22445"


@dataclass
class ConfiguredCommands:
    commands: List[str]
    verification_file_path: Path


@pytest.fixture
def start_commands(tmp_path: Path) -> ConfiguredCommands:
    """
    Returns the start command(s) that should be run by the Focus time app. The commands depend on the operating system.

    On macOS, we cannot use the "dnd-start" command yet, because we are unable to achieve an UNATTENDED installation
    of the Shortcuts DND helper:
     - On the stable macOS 12 runner OS, the Shortcuts app cannot be controlled using AppleScript, for unknown reasons
     - On the still-in-beta macOS 13 runner OS, the Shortcut app can be controlled, but the  macOS 13 does not
       support AppleScript yet, see https://github.com/actions/runner-images/issues/7531
    """
    verification_file_path = tmp_path / "verification.txt"
    if sys.platform == "win32":
        # Note: you need to omit the <space> between "start" and ">>" as otherwise the space would become part of the
        # file
        return ConfiguredCommands(commands=["dnd-start", f"echo start>> {verification_file_path}"],
                                  verification_file_path=verification_file_path)
    elif sys.platform == "darwin":
        return ConfiguredCommands(commands=[f"echo start >> {verification_file_path}"],
                                  verification_file_path=verification_file_path)
    raise NotImplementedError


@pytest.fixture
def stop_commands(tmp_path: Path) -> ConfiguredCommands:
    """
    Returns the stop command(s) that should be run by the Focus time app. The commands depend on the operating system.
    """
    verification_file_path = str(tmp_path / "verification.txt")
    if sys.platform == "win32":
        # Note: you need to omit the <space> between "stop" and ">>" as otherwise the space would become part of the
        # file
        return ConfiguredCommands(commands=["dnd-stop", f"echo stop>> {verification_file_path}"],
                                  verification_file_path=verification_file_path)
    elif sys.platform == "darwin":
        return ConfiguredCommands(commands=[f"echo stop >> {verification_file_path}"],
                                  verification_file_path=verification_file_path)
    raise NotImplementedError


def write_line_to_stream(stream: IO, input: Any):
    stream.write(str(input) + '\n')
    stream.flush()


@dataclass
class ConfiguredCLI:
    configuration: ConfigurationV1
    calendar_adapter: AbstractCalendarAdapter
    verification_file_path: Path


@pytest.fixture(params=[CalendarType.Outlook365])
def configured_cli_no_bg_jobs(request, start_commands, stop_commands) -> ConfiguredCLI:
    yield from configured_cli(request.param, skip_background_scheduler_setup=True, start_commands=start_commands,
                              stop_commands=stop_commands)


@pytest.fixture(params=[CalendarType.Outlook365])
def configured_cli_with_bg_jobs(request, start_commands, stop_commands) -> ConfiguredCLI:
    yield from configured_cli(request.param, skip_background_scheduler_setup=False, start_commands=start_commands,
                              stop_commands=stop_commands)


def configured_cli(calendar_type: CalendarType, skip_background_scheduler_setup: bool,
                   start_commands: ConfiguredCommands, stop_commands: ConfiguredCommands) -> ConfiguredCLI:
    reset_dnd_and_bg_scheduler()
    if Persistence.ongoing_focustime_markerfile_exists():
        Persistence.set_ongoing_focustime(ongoing=False)

    dnd_profile_name = CommandExecutorConstants.WINDOWS_FOCUS_ASSIST_PRIORITY_ONLY_PROFILE if sys.platform == "win32" \
        else "unused"
    # We use a different Focustime event blocker name for every test, to allow multiple tests to run in parallel,
    # without interfering with each other
    focustime_event_name = "Focustime-" + get_random_event_name_postfix()
    config = ConfigurationV1(calendar_type=calendar_type, calendar_look_ahead_hours=3, calendar_look_back_hours=5,
                             focustime_event_name=focustime_event_name,
                             start_commands=start_commands.commands, stop_commands=stop_commands.commands,
                             dnd_profile_name=dnd_profile_name, adjust_event_reminder_time=True,
                             event_reminder_time_minutes=15)

    Persistence.get_config_file_path().unlink(missing_ok=True)

    cli_with_args = [get_frozen_binary_path(), "configure"]
    if skip_background_scheduler_setup:
        cli_with_args.append("--skip-background-scheduler-setup")
    config_process = subprocess.Popen(cli_with_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, universal_newlines=True)

    # TODO: consider using https://github.com/xloem/nonblocking_stream_queue ? Calling readline() too often will
    #  cause the CI test to hang until the CI job times out
    out = config_process.stdout.readline()  # asks whether to create a new configuration
    write_line_to_stream(config_process.stdin, "y")  # create a new configuration
    out = config_process.stdout.readline()  # asks for Calendar adapter

    if calendar_type is CalendarType.Outlook365:
        configure_outlook365_calendar_adapter(config_process, config)

    out = config_process.stdout.readline()  # What is the title or subject of your Focus time events in your calendar?
    write_line_to_stream(config_process.stdin, config.focustime_event_name)
    out = config_process.stdout.readline()  # asks for calendar_look_ahead_hours
    write_line_to_stream(config_process.stdin, config.calendar_look_back_hours)
    out = config_process.stdout.readline()  # asks for calendar_look_back_hours
    write_line_to_stream(config_process.stdin, config.calendar_look_ahead_hours)

    for start_command in config.start_commands:
        out = config_process.stdout.readline()  # asks for shell commands to run when a focus session starts
        write_line_to_stream(config_process.stdin, start_command)
    out = config_process.stdout.readline()  # asks for shell commands to run when a focus session starts
    write_line_to_stream(config_process.stdin, "")  # indicate that we are done providing commands

    for stop_command in config.stop_commands:
        out = config_process.stdout.readline()  # asks for shell commands to run when a focus session stops
        write_line_to_stream(config_process.stdin, stop_command)
    out = config_process.stdout.readline()  # asks for shell commands to run when a focus session stops
    write_line_to_stream(config_process.stdin, "")  # indicate that we are done providing commands

    out = config_process.stdout.readline()  # asks for whether to overwrite the reminder time of the focus time events
    write_line_to_stream(config_process.stdin, "Y" if config.adjust_event_reminder_time else "n")
    if config.adjust_event_reminder_time:
        out = config_process.stdout.readline()  # asks for reminder minutes
        write_line_to_stream(config_process.stdin, config.event_reminder_time_minutes)

    if sys.platform == "win32":
        out = config_process.stdout.readline()  # asks for name of Windows Focus Assist profile
        write_line_to_stream(config_process.stdin, config.dnd_profile_name)
    elif sys.platform == "darwin":
        out = config_process.stdout.readline()  # tells user how to change the focus name in the 'Shortcuts' app

    stdout, stderr = config_process.communicate()
    assert config_process.returncode == 0, f"configure command exited with non-zero command. " \
                                           f"Stdout output:\n{stdout}\n" \
                                           f"Stderr output:\n{stderr}"

    calendar_adapter = get_configured_calendar_adapter_for_testing(config)

    yield ConfiguredCLI(configuration=config, calendar_adapter=calendar_adapter,
                        verification_file_path=start_commands.verification_file_path)

    clean_calendar(configuration=config, calendar_adapter=calendar_adapter)
    reset_dnd_and_bg_scheduler()


def reset_dnd_and_bg_scheduler():
    CommandExecutorImpl.set_dnd_active(active=False, dnd_profile_name="unused")
    BackgroundSchedulerImpl.uninstall_background_scheduler()


def configure_outlook365_calendar_adapter(config_process: Popen, config: ConfigurationV1):
    """
    Provides the inputs to the "configure" command that are necessary to configure the Outlook 365 calendar adapter.
    Requires the environment variables OUTLOOK365_EMAIL and OUTLOOK365_PASSWORD to be set for the corresponding
    Microsoft 365 account (whose owner must already have granted permission to the Client ID used below).
    """
    adapter_configuration = Outlook365ConfigurationV1(client_id=OUTLOOK365_TEST_CLIENT_ID, calendar_name="Calendar")

    write_line_to_stream(config_process.stdin, "1")  # Use Outlook
    out = config_process.stdout.readline()  # asks for Client ID
    write_line_to_stream(config_process.stdin, adapter_configuration.client_id)
    out = config_process.stdout.readline()  # asks user to visit URL
    url = config_process.stdout.readline()  # contains the actual URL
    assert url.startswith("https://login.microsoftonline.com/common/oauth2/v2.0/authorize?response_type=code")
    out = config_process.stdout.readline()  # more Outlook-specific instructions
    out = config_process.stdout.readline()  # more Outlook-specific instructions
    auth_code_url = get_outlook365_authorization_code_url(url)
    write_line_to_stream(config_process.stdin, auth_code_url)
    assert "Authentication Flow Completed. Oauth Access Token Stored. You can now use the API." \
           in config_process.stdout.readline()

    assert "Retrieving the list of calendars ..." in config_process.stdout.readline()
    assert "Please provide the name of your calendar (Calendar, United States holidays, Birthdays)" \
           in config_process.stdout.readline()
    write_line_to_stream(config_process.stdin, adapter_configuration.calendar_name)

    outlook_configuration_v1_schema = marshmallow_dataclass.class_schema(Outlook365ConfigurationV1)()
    config.adapter_configuration = outlook_configuration_v1_schema.dump(adapter_configuration)


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
    WebDriverWait(driver, 10).until(EC.url_matches("https://login.microsoftonline.com/common/oauth2/nativeclient"))
    return driver.current_url


def get_configured_calendar_adapter_for_testing(configuration: ConfigurationV1) -> AbstractCalendarAdapter:
    """
    Creates a dedicated calendar adapter for the automated test. This is particularly necessary because on macOS,
    there are issues with the Keychain access, which make it impossible to "reuse" the credentials created by the
    frozen focus-time app that being tested: in general, the credentials created in a keychain by app #A (e.g. the
    frozen focus-time binary) cannot be read by any other apps #B (e.g. Python running pytest).
    """

    def _get_authorization_code(consent_url: str) -> str:
        return get_outlook365_authorization_code_url(consent_url)

    if configuration.calendar_type is CalendarType.Outlook365:
        testing_overrides = Outlook365TestingOverrides(
            handle_consent_callback=_get_authorization_code,
            namespace="ci-runner",
            client_id=OUTLOOK365_TEST_CLIENT_ID,
            calendar_name="Calendar"
        )
        adapter = Outlook365CalendarAdapter(configuration=configuration, testing_overrides=testing_overrides)
        adapter.authenticate()
    else:
        raise NotImplementedError

    adapter.check_connection_and_credentials()
    return adapter
