from abc import ABC, abstractmethod


class AbstractBackgroundScheduler(ABC):
    @abstractmethod
    def install_or_repair_background_scheduler(self):
        """

        :return:
        """

    def uninstall_background_scheduler(self):
        """

        :return:
        """
