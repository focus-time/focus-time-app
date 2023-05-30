from abc import ABC, abstractmethod
from typing import List


class CommandExecutorConstants:
    DND_START_COMMAND = "dnd-start"
    DND_STOP_COMMAND = "dnd-stop"
    WINDOWS_FOCUS_ASSIST_PRIORITY_ONLY_PROFILE = "prio-only"
    WINDOWS_FOCUS_ASSIST_ALARMS_ONLY_PROFILE = "alarms-only"


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
