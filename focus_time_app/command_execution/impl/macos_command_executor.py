import subprocess
from typing import List

from focus_time_app.command_execution.abstract_command_executor import AbstractCommandExecutor

# TODO implement

class MacOsCommandExecutor(AbstractCommandExecutor):
    FOCUS_MODE_SHORTCUT_NAME = "Focus Time (do not edit)"

    def execute_commands(self, commands: List[str], dnd_profile_name: str):
        pass

    def install_dnd_helpers(self):
        if not self._is_shortcut_installed():
            self._install_shortcut()

    def _is_shortcut_installed(self) -> bool:
        output_bytes = subprocess.check_output(["shortcuts", "list"], shell=True)
        output_lines = output_bytes.decode("utf-8").splitlines()
        return self.FOCUS_MODE_SHORTCUT_NAME in output_lines

    def _install_shortcut(self):
        subprocess.check_call(["open", "/path/to/file.shortcut"])  # TODO
