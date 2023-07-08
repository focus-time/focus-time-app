from abc import ABC, abstractmethod


class AbstractShellAvailability(ABC):
    """
    Helper class used to determine whether the frozen(!) "focus-time" binary is generally available in the
    shell (e.g. because it is on the PATH) - or to make it available.
    """

    @abstractmethod
    def is_available(self) -> bool:
        """
        Returns true if the frozen binary is generally available, False otherwise.
        """

    @abstractmethod
    def make_available(self):
        """
        Makes the binary generally available.
        """

    def requires_shell_restart(self) -> bool:
        """
        Returns True if the underlying mechanism requires the user to restart the shell, False otherwise.
        """
