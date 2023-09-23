from abc import ABC, abstractmethod
from typing import List


class CommandExecutorConstants:
    DND_START_COMMAND = "dnd-start"
    DND_STOP_COMMAND = "dnd-stop"
    WINDOWS_FOCUS_ASSIST_PRIORITY_ONLY_PROFILE = "prio-only"
    WINDOWS_FOCUS_ASSIST_ALARMS_ONLY_PROFILE = "alarms-only"
    MACOS_FOCUS_MODE_SHORTCUT_NAME = "focus-time-app"  # must match the filename in the "resources" folder


class AbstractCommandExecutor(ABC):
    """
    Implementations of AbstractCommandExecutor execute CLI/terminal/Bash commands in a shell environment.
    The CommandExecutorConstants.DND_START_COMMAND/DND_STOP_COMMAND are special keywords which then (de)activate the
    operating system's underlying Do-Not-Disturb / Focus-Mode mechanism.
    """

    @abstractmethod
    def execute_commands(self, commands: List[str], dnd_profile_name: str):
        """
        Executes all specified shell commands, using subprocess.check_call(), raising if something goes wrong.

        If a command matches CommandExecutorConstants.DND_START_COMMAND/DND_STOP_COMMAND, then instead the
        operating system's underlying Do-Not-Disturb / Focus-Mode mechanism is (de)activated.

        :param commands: the commands to execute, e.g. "echo test"
        :param dnd_profile_name: the OS-specific name of the Focus-Mode/DND profile,
            e.g. WINDOWS_FOCUS_ASSIST_PRIORITY_ONLY_PROFILE
        """

    @abstractmethod
    def install_dnd_helpers(self):
        """
        Installs Do-Not-Disturb helpers, if required by the OS (e.g. for macOS, a specific shortcut for Shortcut.app).
        """

    @abstractmethod
    def is_dnd_helper_installed(self) -> bool:
        """
        Returns True if the operating system does not need a DND helper, or if it needs one which actually is
        installed, False otherwise.
        """

    def uninstall_dnd_helpers(self):
        """
        Uninstalls any installed DND helpers, if possible.
        """

    def is_dnd_active(self) -> bool:
        """
        Returns whether any DND / Focus Mode is currently active.
        """

    def set_dnd_active(self, active: bool, dnd_profile_name: str):
        """
        Enables the requested DND profile (if active=True), or disables the DND mode.
        """
