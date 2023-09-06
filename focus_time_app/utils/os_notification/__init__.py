import sys
from typing import Optional

from focus_time_app.utils.os_notification.abstract_os_notification import AbstractOsNotification

OsNativeNotificationImpl: Optional[AbstractOsNotification] = None

if sys.platform == "win32":
    from focus_time_app.utils.os_notification.win_os_notification import WinOsNotification

    OsNativeNotificationImpl = WinOsNotification()
elif sys.platform == "darwin":
    from focus_time_app.utils.os_notification.macos_os_notification import MacosOsNotification

    OsNativeNotificationImpl = MacosOsNotification()
else:
    raise NotImplementedError
