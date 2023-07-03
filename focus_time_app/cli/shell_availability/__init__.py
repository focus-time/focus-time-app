import sys
from typing import Optional

from focus_time_app.cli.shell_availability.abstract_shell_availability import AbstractShellAvailability

ShellAvailabilityImpl: Optional[AbstractShellAvailability] = None

if sys.platform == "win32":
    from focus_time_app.cli.shell_availability.impl.win_shell_availability import WindowsShellAvailability

    ShellAvailabilityImpl = WindowsShellAvailability()
elif sys.platform == "darwin":
    from focus_time_app.cli.shell_availability.impl.macos_shell_availability import MacOsShellAvailability

    ShellAvailabilityImpl = MacOsShellAvailability()
else:
    raise NotImplementedError
