# from mac_notifications import client
import os

from focus_time_app.utils.os_notification import AbstractOsNotification


class MacosOsNotification(AbstractOsNotification):
    def send_notification(self, title: str, message: str):
        # client.create_notification(title=title, text=message)  # Note: we could also set an icon, if we wanted to
        # TODO: replace this approach with https://pypi.org/project/macos-notifications
        #  once https://github.com/Jorricks/macos-notifications/issues/12 is resolved
        appleScriptNotification = f'display notification "{message}" with title "{title}"'
        os.system(f"osascript -e '{appleScriptNotification}'")
