from abc import ABC, abstractmethod


class AbstractBackgroundScheduler(ABC):
    """
    Manages setting up (or removing) OS-specific background jobs.
    """

    @abstractmethod
    def install_or_repair_background_scheduler(self):
        """
        Installs or repairs a background job that calls the "sync" command of the Focus Time App CLI
        """

    def uninstall_background_scheduler(self):
        """
        Uninstalls any (possibly existing) background job.
        """
