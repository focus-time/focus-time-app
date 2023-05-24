from typing import List

from focus_time_app.command_execution.abstract_command_executor import AbstractCommandExecutor


class WindowsCommandExecutor(AbstractCommandExecutor):

    def execute_commands(self, commands: List[str]):
        pass

    def install_dnd_helpers(self):
        pass

