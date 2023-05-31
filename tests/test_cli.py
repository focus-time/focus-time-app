import subprocess
import sys
from os import getenv
from typing import IO

import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from command_execution.abstract_command_executor import CommandExecutorConstants
from configuration.persistence import Persistence

EMAILFIELD = (By.ID, "i0116")
PASSWORDFIELD = (By.ID, "i0118")
NEXTBUTTON = (By.ID, "idSIButton9")


def write_line_to_stream(stream: IO, input: str):
    stream.write(input + '\n')
    stream.flush()


# Consider using https://github.com/xloem/nonblocking_stream_queue ?
def test_configure():
    Persistence.get_config_file_path().unlink(missing_ok=True)
    config_process = subprocess.Popen(["./../dist/focus-time/focus-time.exe", "configure"], stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      universal_newlines=True)
    config_process.stdout.readline()  # asks whether to create a new configuration
    write_line_to_stream(config_process.stdin, "y")  # create a new configuration
    config_process.stdout.readline()  # asks for Calendar adapter
    write_line_to_stream(config_process.stdin, "1")  # Use Outlook
    config_process.stdout.readline()  # asks for Client ID
    write_line_to_stream(config_process.stdin, "bcc815bb-01d0-4765-ae14-e2bf0ee22445")
    config_process.stdout.readline()  # asks user to visit URL
    url = config_process.stdout.readline()  # contains the actual URL
    assert url.startswith("https://login.microsoftonline.com/common/oauth2/v2.0/authorize?response_type=code")
    config_process.stdout.readline()  # more Outlook-specific instructions
    config_process.stdout.readline()  # more Outlook-specific instructions
    auth_code_url = get_authorization_code_url(url)
    write_line_to_stream(config_process.stdin, auth_code_url)
    assert "Authentication Flow Completed. Oauth Access Token Stored. You can now use the API." \
           in config_process.stdout.readline()

    assert "Retrieving the list of calendars ..." in config_process.stdout.readline()
    assert "Please provide the name of your calendar (Calendar, United States holidays, Birthdays)" \
           in config_process.stdout.readline()
    write_line_to_stream(config_process.stdin, "Calendar")
    config_process.stdout.readline()  # What is the title or subject of your Focus time events in your calendar?
    write_line_to_stream(config_process.stdin, "Focustime")
    config_process.stdout.readline()  # asks for calendar_look_ahead_hours
    write_line_to_stream(config_process.stdin, "3")
    config_process.stdout.readline()  # asks for calendar_look_back_hours
    write_line_to_stream(config_process.stdin, "5")
    config_process.stdout.readline()  # asks for shell commands to run when a focus session starts
    write_line_to_stream(config_process.stdin, "dnd-start")
    write_line_to_stream(config_process.stdin, "")  # indicate that we are done providing commands
    config_process.stdout.readline()  # asks for shell commands to run when a focus session stops
    write_line_to_stream(config_process.stdin, "dnd-stop")
    write_line_to_stream(config_process.stdin, "")  # indicate that we are done providing commands
    if sys.platform == "win32":
        config_process.stdout.readline()  # asks for name of Windows Focus Assist profile
        write_line_to_stream(config_process.stdin, CommandExecutorConstants.WINDOWS_FOCUS_ASSIST_PRIORITY_ONLY_PROFILE)
    elif sys.platform == "darwin":
        config_process.stdout.readline()  # tells user how to change the focus name in the 'Shortcuts' app
    config_process.stdout.readline()  # asks for whether to overwrite the reminder time of the focus time events
    write_line_to_stream(config_process.stdin, "Y")
    config_process.stdout.readline()  # asks for reminder minutes
    write_line_to_stream(config_process.stdin, "15")

    config_process.communicate()
    assert config_process.returncode == 0


def get_authorization_code_url(request_url: str) -> str:
    chromedriver_autoinstaller.install()
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    driver.get('https://login.live.com')

    # wait for email field and enter email
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(EMAILFIELD)).send_keys(getenv("EMAIL"))
    # Click Next
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(NEXTBUTTON)).click()

    # wait for password field
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(PASSWORDFIELD)).send_keys(getenv("PASSWORD"))
    # Click Next
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(NEXTBUTTON)).click()

    driver.get(request_url)
    WebDriverWait(driver, 10).until(EC.url_matches("https://login.microsoftonline.com/common/oauth2/nativeclient"))
    return driver.current_url
