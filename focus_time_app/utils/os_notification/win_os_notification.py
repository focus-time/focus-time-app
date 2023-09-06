from windows_toasts import WindowsToaster, Toast

from focus_time_app.utils.os_notification import AbstractOsNotification


class WinOsNotification(AbstractOsNotification):
    def send_notification(self, title: str, message: str):
        toaster = WindowsToaster('Focus Time App')
        t = Toast()
        t.text_fields = [title, message]
        toaster.show_toast(t)
