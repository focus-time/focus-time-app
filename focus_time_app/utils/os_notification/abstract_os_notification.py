from abc import ABC


class AbstractOsNotification(ABC):
    def send_notification(self, title: str, message: str):
        """
        Shows an OS-native notification to the user
        """
