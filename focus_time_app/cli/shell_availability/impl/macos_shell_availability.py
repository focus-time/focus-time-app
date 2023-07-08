import os.path
import sys
from pathlib import Path

from focus_time_app.cli.shell_availability import AbstractShellAvailability
from focus_time_app.utils import is_production_environment


class MacOsShellAvailability(AbstractShellAvailability):
    PROFILE_MARKER_COMMENT = "# Make the focus-time app available on the shell by adding it to PATH"

    def is_available(self) -> bool:
        if not is_production_environment():
            raise ValueError("Calling this method only makes sense for the frozen production binary")

        return sys.executable in os.getenv("PATH")

    def make_available(self):
        if not is_production_environment():
            raise ValueError("Calling this method only makes sense for the frozen production binary")

        active_shell = os.getenv("SHELL", None)
        if active_shell is None:
            raise ValueError("Unable to detect the active shell (environment variable SHELL is not set)")

        profile_file = self._get_profile_file(active_shell)

        if not profile_file:
            raise ValueError(f"Unsupported SHELL {active_shell} - profile file that needs to be modified is not known")

        profile_file.touch(exist_ok=True)

        if not self._path_is_already_in_profile(profile_file):
            self._add_path_to_profile(profile_file)

    def requires_shell_restart(self) -> bool:
        return True

    @staticmethod
    def _get_profile_file(active_shell: str) -> Path:
        if active_shell.endswith("/zsh"):
            return Path.home() / ".zprofile"
        elif active_shell.endswith("/sh"):
            return Path.home() / ".profile"
        elif active_shell.endswith("/bash"):
            return Path.home() / ".bash_profile"

    def _path_is_already_in_profile(self, profile_file: Path) -> bool:
        profile_content = profile_file.read_text()
        lines = profile_content.splitlines()
        for i, line in enumerate(lines):
            if line == self.PROFILE_MARKER_COMMENT:
                return True

        return False

    def _add_path_to_profile(self, profile_file: Path):
        profile_content = profile_file.read_text()
        if profile_content:
            profile_content += "\n\n"
        profile_content += self.PROFILE_MARKER_COMMENT + '\n' + f'export PATH="$PATH:{sys.executable}"'
        profile_file.write_text(profile_content)
