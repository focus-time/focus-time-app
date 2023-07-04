import os.path
import sys
from pathlib import Path

from focus_time_app.cli.shell_availability import AbstractShellAvailability
from focus_time_app.utils import is_production_environment


class MacOsShellAvailability(AbstractShellAvailability):
    SYMLINK = Path("/usr/local/bin") / os.path.basename(sys.executable)

    def is_available(self) -> bool:
        if not is_production_environment():
            raise ValueError("Calling this method only makes sense for the frozen production binary")

        return self.SYMLINK.is_symlink() and self.SYMLINK.readlink() == Path(sys.executable)

    def make_available(self):
        if not is_production_environment():
            raise ValueError("Calling this method only makes sense for the frozen production binary")

        self.SYMLINK.unlink(missing_ok=True)  # existing symbolic link might be outdated, so we always refresh it
        self.SYMLINK.symlink_to(sys.executable)

    def requires_shell_restart(self) -> bool:
        return False


