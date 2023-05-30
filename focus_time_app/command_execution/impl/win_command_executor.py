import subprocess
from typing import List

from command_execution.abstract_command_executor import CommandExecutorConstants
from focus_time_app.command_execution.abstract_command_executor import AbstractCommandExecutor


class WindowsCommandExecutor(AbstractCommandExecutor):

    def execute_commands(self, commands: List[str], dnd_profile_name: str):
        for command in commands:
            if command == CommandExecutorConstants.DND_START_COMMAND:
                print("start DND")  # TODO implement
            elif command == CommandExecutorConstants.DND_STOP_COMMAND:
                print("stop DND")  # TODO implement
            else:
                subprocess.check_call(command, shell=True)

    def install_dnd_helpers(self):
        pass  # Nothing to do
