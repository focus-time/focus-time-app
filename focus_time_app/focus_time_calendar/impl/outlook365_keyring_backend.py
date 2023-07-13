import json
import logging
import math
import sys
from json import JSONDecodeError
from typing import Optional

import keyring
from O365.utils import BaseTokenBackend
from keyring.errors import PasswordDeleteError

from focus_time_app.utils import get_environment_suffix


class Outlook365KeyringBackend(BaseTokenBackend):
    PASSWORD_LENGTH_LIMITATION = {
        "win32": 500,
        "darwin": 0  # unlimited
    }

    def __init__(self, namespace_override: Optional[str] = None):
        super().__init__()
        namespace_suffix = f"-{namespace_override}" if namespace_override else get_environment_suffix()
        self._SERVICE_NAME = "FocusTimeApp" + namespace_suffix
        self._USERNAME = "FocusTimeApp" + namespace_suffix
        self._logger = logging.getLogger(type(self).__name__)

    def load_token(self):
        if self.token:
            return self.token

        pw_length_limit = Outlook365KeyringBackend.PASSWORD_LENGTH_LIMITATION[sys.platform]
        password_string = ""
        if pw_length_limit:
            for i in range(999999):
                password_substring = keyring.get_password(self._SERVICE_NAME, f"{self._USERNAME}-{i}")
                if not password_substring:
                    break
                password_string += password_substring
        else:
            password_string = keyring.get_password(self._SERVICE_NAME, self._USERNAME)

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

        try:
            # Avoid problems in rare cases where save_token() would not override ALL slots, and load_token() would
            # not detect it (via JSONDecodeError), causing errors such as
            # "CompactToken parsing failed with error code: 80049217"
            self.delete_token()
        except:
            pass

        pw_length_limit = Outlook365KeyringBackend.PASSWORD_LENGTH_LIMITATION[sys.platform]
        if pw_length_limit:
            offset = 0
            for offset in range(math.ceil(len(password_string) / pw_length_limit)):
                password_subset = password_string[offset * pw_length_limit: offset * pw_length_limit + pw_length_limit]
                keyring.set_password(self._SERVICE_NAME, f"{self._USERNAME}-{offset}", password_subset)

            # Make sure to break the sequence of older (not-properly deleted) passwords, if they exist
            try:
                keyring.delete_password(self._SERVICE_NAME, f"{self._USERNAME}-{offset + 1}")
            except PasswordDeleteError:
                pass
        else:
            keyring.set_password(self._SERVICE_NAME, self._USERNAME, password_string)

        return True

    def delete_token(self):
        pw_length_limit = Outlook365KeyringBackend.PASSWORD_LENGTH_LIMITATION[sys.platform]
        if pw_length_limit:
            for i in range(999999):
                password_substring = keyring.get_password(self._SERVICE_NAME, f"{self._USERNAME}-{i}")
                if not password_substring:
                    break
                keyring.delete_password(self._SERVICE_NAME, f"{self._USERNAME}-{i}")
        else:
            keyring.delete_password(self._SERVICE_NAME, self._USERNAME)
