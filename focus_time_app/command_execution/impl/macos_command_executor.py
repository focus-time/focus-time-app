import subprocess
import sys
import time
from pathlib import Path
from typing import List

import typer

from focus_time_app.command_execution.abstract_command_executor import AbstractCommandExecutor
from focus_time_app.command_execution.abstract_command_executor import CommandExecutorConstants
from focus_time_app.utils import is_production_environment


class MacOsCommandExecutor(AbstractCommandExecutor):

    def execute_commands(self, commands: List[str], dnd_profile_name: str):
        for command in commands:
            if command == CommandExecutorConstants.DND_START_COMMAND:
                self.set_dnd_active(active=True, dnd_profile_name="unused")
            elif command == CommandExecutorConstants.DND_STOP_COMMAND:
                self.set_dnd_active(active=False, dnd_profile_name="unused")
            else:
                subprocess.check_call(command, shell=True)

    def install_dnd_helpers(self):
        while not self.is_dnd_helper_installed():
            self._install_shortcut()
            if self.is_dnd_helper_installed():
                typer.echo("Shortcut was successfully installed")
            else:
                typer.prompt("Could not detect that the shortcut has been installed. Press Enter to try again.",
                             default='', prompt_suffix='\n')

    def set_dnd_active(self, active: bool, dnd_profile_name: str):
        arg = "on" if active else "off"
        subprocess.check_call(f"shortcuts run '{CommandExecutorConstants.MACOS_FOCUS_MODE_SHORTCUT_NAME}' <<< {arg}",
                              shell=True)

    def is_dnd_helper_installed(self) -> bool:
        output_bytes = subprocess.check_output(["/usr/bin/shortcuts", "list"], shell=True)
        output_lines = output_bytes.decode("utf-8").splitlines()
        return CommandExecutorConstants.MACOS_FOCUS_MODE_SHORTCUT_NAME in output_lines

    def _install_shortcut(self):
        typer.prompt("The Focus Time App needs to import a shortcut into the macOS 'Shortcuts' app, to be able to "
                     "start and stop Focus sessions on macOS. "
                     "Once you press Enter, a dialog opens in which you have to press the 'Add Shortcut' button.",
                     default='', prompt_suffix='\n')
        if is_production_environment():
            path = str(Path(sys.executable).parent
                       / f"{CommandExecutorConstants.MACOS_FOCUS_MODE_SHORTCUT_NAME}.shortcut")
            if hasattr(sys, "_MEIPASS"):
                path = str(Path(sys._MEIPASS) / f"{CommandExecutorConstants.MACOS_FOCUS_MODE_SHORTCUT_NAME}.shortcut")
        else:
            path = str(Path(__file__).parent.parent.parent.parent / "resources"
                       / f"{CommandExecutorConstants.MACOS_FOCUS_MODE_SHORTCUT_NAME}.shortcut")
        subprocess.check_call(["open", path], shell=True)
        typer.prompt("Press Enter once you have installed the shortcut.", default='', prompt_suffix='\n')

    def uninstall_dnd_helpers(self):
        pass  # Does not seem to be possible - the "shortcuts" CLI has no remove/delete option!

    def is_dnd_active(self) -> bool:
        # On macOS, the on/off detection of the "defaults" command executed below is "slow".
        # Because the is_dnd_active() method is only used in integration tests, the easiest fix is to sleep a bit,
        # for the detection to catch up
        time.sleep(10)

        result = subprocess.check_output('defaults read com.apple.controlcenter "NSStatusItem Visible FocusModes"',
                                         shell=True)
        result = result.decode("utf-8").rstrip('\n')
        if result not in ["0", "1"]:
            raise RuntimeError(f"Unexpected result from 'defaults ...' command: {result}")

        return result == "1"
