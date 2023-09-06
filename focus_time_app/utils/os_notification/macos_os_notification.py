import os

from focus_time_app.utils.os_notification import AbstractOsNotification


class MacosOsNotification(AbstractOsNotification):
    def send_notification(self, title: str, message: str):
        # TODO: replace this approach with https://pypi.org/project/macos-notifications
        #  once https://github.com/Jorricks/macos-notifications/issues/11 is resolved
        appleScriptNotification = f'display notification "{message}" with title "{title}"'
        os.system(f"osascript -e '{appleScriptNotification}'")
