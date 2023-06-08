import subprocess
import sys
from pathlib import Path
from typing import List

import typer

from focus_time_app.command_execution.abstract_command_executor import AbstractCommandExecutor
from focus_time_app.command_execution.abstract_command_executor import CommandExecutorConstants


class MacOsCommandExecutor(AbstractCommandExecutor):
    FOCUS_MODE_SHORTCUT_FILENAME = "focus-time-app.shortcut"

    def execute_commands(self, commands: List[str], dnd_profile_name: str):
        for command in commands:
            if command == CommandExecutorConstants.DND_START_COMMAND:
                self.set_dnd_active(active=True, dnd_profile_name="unused")
            elif command == CommandExecutorConstants.DND_STOP_COMMAND:
                self.set_dnd_active(active=False, dnd_profile_name="unused")
            else:
                subprocess.check_call(command, shell=True)

    def install_dnd_helpers(self):
        while not self._is_shortcut_installed():
            self._install_shortcut()
            if self._is_shortcut_installed():
                typer.echo("Shortcut was successfully installed")
            else:
                typer.prompt("Could not detect that the shortcut has been installed. Press Enter to try again.",
                             default='', prompt_suffix='\n')

    def set_dnd_active(self, active: bool, dnd_profile_name: str):
        arg = "on" if active else "off"
        subprocess.check_call(f"shortcuts '{CommandExecutorConstants.MACOS_FOCUS_MODE_SHORTCUT_NAME}' <<< {arg}",
                              shell=True)

    @staticmethod
    def _is_shortcut_installed() -> bool:
        output_bytes = subprocess.check_output(["shortcuts", "list"], shell=True)
        output_lines = output_bytes.decode("utf-8").splitlines()
        return CommandExecutorConstants.MACOS_FOCUS_MODE_SHORTCUT_NAME in output_lines

    def _install_shortcut(self):
        typer.prompt("The Focus Time App needs to import a shortcut into the macOS 'Shortcuts' app, to be able to "
                     "start and stop Focus sessions on macOS. "
                     "Once you press Enter, a dialog opens in which you have to press the 'Add Shortcut' button.",
                     default='', prompt_suffix='\n')
        if getattr(sys, 'frozen', False):
            path = str(Path(sys.executable).parent / self.FOCUS_MODE_SHORTCUT_FILENAME)
        else:
            path = str(Path(__file__).parent.parent.parent.parent / "resources" / self.FOCUS_MODE_SHORTCUT_FILENAME)
        subprocess.check_call(["open", path])
        typer.prompt("Press Enter once you have installed the shortcut.", default='', prompt_suffix='\n')

    def uninstall_dnd_helpers(self):
        pass  # Does not seem to be possible - the "shortcuts" CLI has no remove/delete option!

    def is_dnd_active(self) -> bool:
        pass  # TODO call: defaults read com.apple.controlcenter "NSStatusItem Visible FocusModes"
        # it returns "1" or "0"
