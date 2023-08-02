import json
import logging
from json import JSONDecodeError
from typing import Optional

from O365.utils import BaseTokenBackend

from focus_time_app.focus_time_calendar.impl.keyring_credentials_store import KeyringCredentialsStore


class Outlook365KeyringBackend(BaseTokenBackend):
    def __init__(self, namespace_override: Optional[str] = None):
        super().__init__()
        self._credentials_store = KeyringCredentialsStore(namespace_override=namespace_override)
        self._logger = logging.getLogger(type(self).__name__)

    def load_token(self):
        if self.token:
            return self.token

        password_string = self._credentials_store.load_credentials()
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

        self._credentials_store.save_credentials(password_string)
        return True

    def delete_token(self):
        self._credentials_store.delete_credentials()
