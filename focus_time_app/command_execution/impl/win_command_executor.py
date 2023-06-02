import os
import subprocess
import sys
from pathlib import Path
from typing import List

from focus_time_app.command_execution.abstract_command_executor import CommandExecutorConstants
from focus_time_app.command_execution.abstract_command_executor import AbstractCommandExecutor


class WindowsCommandExecutor(AbstractCommandExecutor):
    DND_HELPER_BINARY_NAME = "windows-dnd.exe"

    def execute_commands(self, commands: List[str], dnd_profile_name: str):
        if dnd_profile_name not in [CommandExecutorConstants.WINDOWS_FOCUS_ASSIST_PRIORITY_ONLY_PROFILE,
                                    CommandExecutorConstants.WINDOWS_FOCUS_ASSIST_ALARMS_ONLY_PROFILE]:
            raise ValueError(f"Unsupported DND profile name '{dnd_profile_name}', only "
                             f"'{CommandExecutorConstants.WINDOWS_FOCUS_ASSIST_ALARMS_ONLY_PROFILE}' and "
                             f"'{CommandExecutorConstants.WINDOWS_FOCUS_ASSIST_PRIORITY_ONLY_PROFILE}' are supported")

        for command in commands:
            if command in [CommandExecutorConstants.DND_START_COMMAND, CommandExecutorConstants.DND_STOP_COMMAND]:
                dnd_command = "set-priority-only" if command == CommandExecutorConstants.DND_START_COMMAND \
                    else "set-off"
                self._run_dnd_helper_with_arg(dnd_command)
            else:
                subprocess.check_call(command, shell=True)

    def install_dnd_helpers(self):
        pass  # Nothing to do

    def uninstall_dnd_helpers(self):
        pass  # Nothing to do

    @staticmethod
    def _run_dnd_helper_with_arg(arg: str) -> str:
        if getattr(sys, 'frozen', False):
            path = os.path.join(sys.executable, WindowsCommandExecutor.DND_HELPER_BINARY_NAME)
        else:
            path = str(Path(__file__).parent.parent.parent.parent / WindowsCommandExecutor.DND_HELPER_BINARY_NAME)
        return subprocess.check_output([path, arg]).decode("utf-8")
