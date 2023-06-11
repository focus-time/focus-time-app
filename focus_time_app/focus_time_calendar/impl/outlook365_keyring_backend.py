import json
import logging
import math
import subprocess
import sys
from json import JSONDecodeError

from O365.utils import BaseTokenBackend

import keyring
from keyring.errors import PasswordDeleteError

from focus_time_app.utils import is_production_environment


class Outlook365KeyringBackend(BaseTokenBackend):
    SERVICE_NAME = "FocusTimeApp" if is_production_environment(ci_means_dev=True) else "FocusTimeApp-Dev"
    USERNAME = "FocusTimeApp" if is_production_environment(ci_means_dev=True) else "FocusTimeApp-Dev"
    PASSWORD_LENGTH_LIMITATION = {
        "win32": 500,
        "darwin": 0  # unlimited
    }

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(type(self).__name__)

    def load_token(self):
        if self.token:
            return self.token

        pw_length_limit = Outlook365KeyringBackend.PASSWORD_LENGTH_LIMITATION[sys.platform]
        password_string = ""
        if pw_length_limit:
            for i in range(999999):
                password_substring = keyring.get_password(Outlook365KeyringBackend.SERVICE_NAME,
                                                          f"{Outlook365KeyringBackend.USERNAME}-{i}")
                if not password_substring:
                    break
                password_string += password_substring
        else:
            password_string = keyring.get_password(Outlook365KeyringBackend.SERVICE_NAME,
                                                   Outlook365KeyringBackend.USERNAME)

        if password_string:
            try:
                return json.loads(password_string)
            except Exception as e:
                self._logger.warning("Unable to decode the JSON-encoded password string from the OS credentials "
                                     f"manager: {e}")
                if isinstance(e, JSONDecodeError):
                    self.delete_token()
                    self._logger.warning("The existing password has been deleted")
                return None

    def save_token(self):
        if self.token is None:
            raise ValueError('You have to set the "token" first.')

        password_string = json.dumps(self.token)

        pw_length_limit = Outlook365KeyringBackend.PASSWORD_LENGTH_LIMITATION[sys.platform]
        if pw_length_limit:
            offset = 0
            for offset in range(math.ceil(len(password_string) / pw_length_limit)):
                password_subset = password_string[offset * pw_length_limit: offset * pw_length_limit + pw_length_limit]
                keyring.set_password(Outlook365KeyringBackend.SERVICE_NAME,
                                     f"{Outlook365KeyringBackend.USERNAME}-{offset}",
                                     password_subset)

            # Make sure to break the sequence of older (not-properly deleted) passwords, if they exist
            try:
                keyring.delete_password(Outlook365KeyringBackend.SERVICE_NAME,
                                        f"{Outlook365KeyringBackend.USERNAME}-{offset + 1}")
            except PasswordDeleteError:
                pass
        else:
            keyring.set_password(Outlook365KeyringBackend.SERVICE_NAME, Outlook365KeyringBackend.USERNAME,
                                 password_string)

        return True

    def delete_token(self):
        pw_length_limit = Outlook365KeyringBackend.PASSWORD_LENGTH_LIMITATION[sys.platform]
        if pw_length_limit:
            for i in range(999999):
                password_substring = keyring.get_password(Outlook365KeyringBackend.SERVICE_NAME,
                                                          f"{Outlook365KeyringBackend.USERNAME}-{i}")
                if not password_substring:
                    break
                keyring.delete_password(Outlook365KeyringBackend.SERVICE_NAME,
                                        f"{Outlook365KeyringBackend.USERNAME}-{i}")
        else:
            keyring.delete_password(Outlook365KeyringBackend.SERVICE_NAME, Outlook365KeyringBackend.USERNAME)

    @staticmethod
    def macos_credentials_hack():
        """
        On macOS, the "focus-time" binary executed by the integration test creates an entry in the "login" keychain
        that can only be read from the "focus-time" binary - trying to read it from the pytest "python" binary (done
        to get the calendar adapter in the "configured_cli" fixture) results in an interactive prompt, which we want
        to avoid. We can circumvent this by first creating a passwordless entry with the shell command below,
        where the "-A" flag specifies that ALL applications may access the entry (without macOS showing any prompts).
        """
        if sys.platform == "darwin":
            try:
                if keyring.get_password(Outlook365KeyringBackend.SERVICE_NAME, Outlook365KeyringBackend.USERNAME):
                    keyring.delete_password(Outlook365KeyringBackend.SERVICE_NAME, Outlook365KeyringBackend.USERNAME)
            except:
                raise ValueError(f"Unable to delete the existing macOS keyring entry "
                                 f"'{Outlook365KeyringBackend.SERVICE_NAME}', you need to delete it manually")
            subprocess.run([
                "/usr/bin/security",
                "add-generic-password",
                "-a", Outlook365KeyringBackend.USERNAME,
                "-s", Outlook365KeyringBackend.SERVICE_NAME,
                "-A"
            ], shell=False, check=True)
