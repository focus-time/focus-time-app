from typing import List

from command_execution.abstract_command_executor import AbstractCommandExecutor


class WindowsCommandExecutor(AbstractCommandExecutor):

    def execute_commands(self, commands: List[str]):
        pass
