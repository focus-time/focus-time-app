import json
import math
import sys
from json import JSONDecodeError

from O365.utils import BaseTokenBackend

import keyring
from keyring.errors import PasswordDeleteError


class Outlook365KeyringBackend(BaseTokenBackend):
    SERVICE_NAME = "FocusTimeApp"  # TODO: should differentiate between prod (frozen) and dev mode
    USERNAME = "FocusTimeApp"
    PASSWORD_LENGTH_LIMITATION = {
        "win32": 500,
        "darwin": 0  # unlimited
    }

    def __init__(self):
        super().__init__()

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
                # TODO log
                if isinstance(e, JSONDecodeError):
                    self.delete_token()
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
        Unsure whether this is needed: On macOS, the "focus-time" binary executed by the integration test creates an
        entry in the "login" keychain that can only be read from the "focus-time" binary - trying to read it from the
        pytest ("python" binary) results in an interactive prompt. If this becomes a problem in CI, we can circumvent
        this by creating a passwordless entry with the command below. The "-A" flag specifies that ALL applications may
        access the entry.
        """
        pass  # security add-generic-password -a FocusTimeApp -s FocusTimeApp -A
