import os.path
import subprocess
import sys
import winreg

from focus_time_app.cli.shell_availability.abstract_shell_availability import AbstractShellAvailability
from focus_time_app.utils import is_production_environment


class WindowsShellAvailability(AbstractShellAvailability):
    PARENT_DIR_PATH = os.path.dirname(sys.executable)

    def is_available(self) -> bool:
        if not is_production_environment():
            raise ValueError("Calling this method only makes sense for the frozen production binary")

        return self.PARENT_DIR_PATH in self._get_path().split(';')

    def make_available(self):
        if not is_production_environment():
            raise ValueError("Calling this method only makes sense for the frozen production binary")
        path = self._get_path()
        path += ";" + self.PARENT_DIR_PATH + ";"

        # Note: the following does not work: even though PATH is updated, it is not used by CMD/PowerShell
        # hkcu = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        # environment_key = winreg.OpenKey(hkcu, "Environment", access=winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE)
        # winreg.SetValueEx(environment_key, "Path", 0, winreg.REG_SZ, path)

        # This PowerShell-based approach seems to work, though
        subprocess.run(["powershell", "-Command", f'[Environment]::SetEnvironmentVariable("PATH", "{path}", "USER")'],
                       check=True)

    def requires_shell_restart(self) -> bool:
        return True

    @staticmethod
    def _get_path() -> str:
        hkcu = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        environment_key = winreg.OpenKey(hkcu, "Environment")
        return winreg.QueryValueEx(environment_key, "Path")[0].rstrip(';')
