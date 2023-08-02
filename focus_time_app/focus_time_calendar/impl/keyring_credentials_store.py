import math
import sys
from typing import Optional

import keyring
from keyring.errors import PasswordDeleteError

from focus_time_app.utils import get_environment_suffix


class KeyringCredentialsStore:
    PASSWORD_LENGTH_LIMITATION = {
        "win32": 500,
        "darwin": 0  # unlimited
    }

    def __init__(self, namespace_override: Optional[str] = None):
        namespace_suffix = f"-{namespace_override}" if namespace_override else get_environment_suffix()
        self._SERVICE_NAME = "FocusTimeApp" + namespace_suffix
        self._USERNAME = "FocusTimeApp" + namespace_suffix

    def load_credentials(self) -> str:
        pw_length_limit = self.PASSWORD_LENGTH_LIMITATION[sys.platform]
        credentials_string = ""
        if pw_length_limit:
            for i in range(999999):
                password_substring = keyring.get_password(self._SERVICE_NAME, f"{self._USERNAME}-{i}")
                if not password_substring:
                    break
                credentials_string += password_substring
        else:
            credentials_string = keyring.get_password(self._SERVICE_NAME, self._USERNAME)

        return credentials_string

    def save_credentials(self, credentials: str):
        pw_length_limit = self.PASSWORD_LENGTH_LIMITATION[sys.platform]
        if pw_length_limit:
            offset = 0
            for offset in range(math.ceil(len(credentials) / pw_length_limit)):
                password_subset = credentials[offset * pw_length_limit: offset * pw_length_limit + pw_length_limit]
                keyring.set_password(self._SERVICE_NAME, f"{self._USERNAME}-{offset}", password_subset)

            # Make sure to break the sequence of older (not-properly deleted) passwords, if they exist
            try:
                keyring.delete_password(self._SERVICE_NAME, f"{self._USERNAME}-{offset + 1}")
            except PasswordDeleteError:
                pass
        else:
            keyring.set_password(self._SERVICE_NAME, self._USERNAME, credentials)

    def delete_credentials(self):
        pw_length_limit = self.PASSWORD_LENGTH_LIMITATION[sys.platform]
        if pw_length_limit:
            for i in range(999999):
                password_substring = keyring.get_password(self._SERVICE_NAME, f"{self._USERNAME}-{i}")
                if not password_substring:
                    break
                keyring.delete_password(self._SERVICE_NAME, f"{self._USERNAME}-{i}")
        else:
            keyring.delete_password(self._SERVICE_NAME, self._USERNAME)
