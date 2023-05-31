import os.path
import subprocess
import sys
from pathlib import Path
from typing import List

from command_execution.abstract_command_executor import CommandExecutorConstants
from focus_time_app.command_execution.abstract_command_executor import AbstractCommandExecutor


class MacOsCommandExecutor(AbstractCommandExecutor):
    FOCUS_MODE_SHORTCUT_FILENAME = "focus-time-app.shortcut"

    def execute_commands(self, commands: List[str], dnd_profile_name: str):
        for command in commands:
            if command == CommandExecutorConstants.DND_START_COMMAND:
                subprocess.check_call(f"shortcuts '{CommandExecutorConstants.MACOS_FOCUS_MODE_SHORTCUT_NAME}' <<< on",
                                      shell=True)
            elif command == CommandExecutorConstants.DND_STOP_COMMAND:
                subprocess.check_call(f"shortcuts '{CommandExecutorConstants.MACOS_FOCUS_MODE_SHORTCUT_NAME}' <<< off",
                                      shell=True)
            else:
                subprocess.check_call(command, shell=True)

    def install_dnd_helpers(self):
        if not self._is_shortcut_installed():
            self._install_shortcut()

    @staticmethod
    def _is_shortcut_installed() -> bool:
        output_bytes = subprocess.check_output(["shortcuts", "list"], shell=True)
        output_lines = output_bytes.decode("utf-8").splitlines()
        return CommandExecutorConstants.MACOS_FOCUS_MODE_SHORTCUT_NAME in output_lines

    def _install_shortcut(self):
        # TODO: do we need to print instructions for the user?
        # TODO is "open" really enough or do we need to click a button? Could this be automated with AppleScript, e.g.
        #  https://stackoverflow.com/questions/48660465/how-can-i-click-ok-with-apple-script
        if getattr(sys, 'frozen', False):
            path = os.path.join(sys.executable, self.FOCUS_MODE_SHORTCUT_FILENAME)
        else:
            path = str(Path(__file__).parent.parent.parent.parent / "resources" / self.FOCUS_MODE_SHORTCUT_FILENAME)
        subprocess.check_call(["open", path])

    def uninstall_dnd_helpers(self):
        pass  # Does not seem to be possible - the "shortcuts" CLI has no remove/delete option!
