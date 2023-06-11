import subprocess
import sys
from pathlib import Path
from typing import List

from focus_time_app.command_execution.abstract_command_executor import AbstractCommandExecutor
from focus_time_app.command_execution.abstract_command_executor import CommandExecutorConstants
from focus_time_app.utils import is_production_environment


class WindowsCommandExecutor(AbstractCommandExecutor):
    DND_HELPER_BINARY_NAME = "windows-dnd.exe"

    def execute_commands(self, commands: List[str], dnd_profile_name: str):
        self._validate_dnd_profile_name(dnd_profile_name)

        for command in commands:
            if command == CommandExecutorConstants.DND_START_COMMAND:
                self.set_dnd_active(active=True, dnd_profile_name=dnd_profile_name)
            elif command == CommandExecutorConstants.DND_STOP_COMMAND:
                self.set_dnd_active(active=False, dnd_profile_name=dnd_profile_name)
            else:
                subprocess.check_call(command, shell=True)

    def install_dnd_helpers(self):
        pass  # Nothing to do

    def uninstall_dnd_helpers(self):
        pass  # Nothing to do

    def is_dnd_active(self) -> bool:
        output = self._run_dnd_helper_with_arg("get-profile")
        if output not in ["priority-only", "alarms-only", "off"]:
            raise RuntimeError(f"Unexpected reported Focus assist mode: {output}")
        return output in ["priority-only", "alarms-only"]

    def set_dnd_active(self, active: bool, dnd_profile_name: str):
        if active:
            self._validate_dnd_profile_name(dnd_profile_name)
            if dnd_profile_name == CommandExecutorConstants.WINDOWS_FOCUS_ASSIST_PRIORITY_ONLY_PROFILE:
                dnd_command = "set-priority-only"
            else:
                dnd_command = "set-alarms-only"
            self._run_dnd_helper_with_arg(dnd_command)
        else:
            self._run_dnd_helper_with_arg("set-off")

    @staticmethod
    def _validate_dnd_profile_name(dnd_profile_name):
        if dnd_profile_name not in [CommandExecutorConstants.WINDOWS_FOCUS_ASSIST_PRIORITY_ONLY_PROFILE,
                                    CommandExecutorConstants.WINDOWS_FOCUS_ASSIST_ALARMS_ONLY_PROFILE]:
            raise ValueError(f"Unsupported DND profile name '{dnd_profile_name}', only "
                             f"'{CommandExecutorConstants.WINDOWS_FOCUS_ASSIST_ALARMS_ONLY_PROFILE}' and "
                             f"'{CommandExecutorConstants.WINDOWS_FOCUS_ASSIST_PRIORITY_ONLY_PROFILE}' are supported")

    @staticmethod
    def _run_dnd_helper_with_arg(arg: str) -> str:
        if is_production_environment(ci_means_dev=False):
            path = str(Path(sys.executable).parent / WindowsCommandExecutor.DND_HELPER_BINARY_NAME)
        else:
            path = str(Path(__file__).parent.parent.parent.parent / WindowsCommandExecutor.DND_HELPER_BINARY_NAME)
        return subprocess.check_output([path, arg]).decode("utf-8")
