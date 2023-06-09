from abc import ABC, abstractmethod
from typing import List


class CommandExecutorConstants:
    DND_START_COMMAND = "dnd-start"
    DND_STOP_COMMAND = "dnd-stop"
    WINDOWS_FOCUS_ASSIST_PRIORITY_ONLY_PROFILE = "prio-only"
    WINDOWS_FOCUS_ASSIST_ALARMS_ONLY_PROFILE = "alarms-only"
    MACOS_FOCUS_MODE_SHORTCUT_NAME = "focus-time-app"  # must match the filename in the "resources" folder


# TODO document

class AbstractCommandExecutor(ABC):

    @abstractmethod
    def execute_commands(self, commands: List[str], dnd_profile_name: str):
        """

        :param commands:
        :return:
        """

    @abstractmethod
    def install_dnd_helpers(self):
        """

        :return:
        """

    @abstractmethod
    def is_dnd_helper_installed(self) -> bool:
        """

        :return:
        """

    def uninstall_dnd_helpers(self):
        """

        :return:
        """

    def is_dnd_active(self) -> bool:
        """

        """

    def set_dnd_active(self, active: bool, dnd_profile_name: str):
        """

        """
