import os.path
import sys

from focus_time_app.cli.shell_availability import AbstractShellAvailability
from focus_time_app.utils import is_production_environment


class MacOsShellAvailability(AbstractShellAvailability):
    BINARY_NAME = os.path.basename(sys.executable)

    def is_available(self) -> bool:
        if not is_production_environment():
            raise ValueError("Calling this method only makes sense for the frozen production binary")

        return os.path.exists(f"/usr/local/bin/{self.BINARY_NAME}")

    def make_available(self):
        if not is_production_environment():
            raise ValueError("Calling this method only makes sense for the frozen production binary")

        os.symlink(src=sys.executable, dst=f"/usr/local/bin/{self.BINARY_NAME}")

    def requires_shell_restart(self) -> bool:
        return False


