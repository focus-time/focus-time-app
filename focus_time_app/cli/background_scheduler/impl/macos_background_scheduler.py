import plistlib
import subprocess
import sys
from copy import copy
from pathlib import Path

from focus_time_app.cli.background_scheduler.abstract_background_scheduler import AbstractBackgroundScheduler
from focus_time_app.utils import is_production_environment


class MacOsBackgroundScheduler(AbstractBackgroundScheduler):
    """
    Uses macOS launch daemon (see also https://launchd.info/) to implement regularly triggered background jobs.
    """

    LAUNCHD_AGENT_DICT = {
        "Label": "FocusTimeApp",
        "KeepAlive": True,
        "ThrottleInterval": 60  # seconds
    }
    LAUNCHD_AGENT_FILE = Path.home() / "Library" / "LaunchAgents" / "focus-time-app.plist"

    def install_or_repair_background_scheduler(self):
        self.uninstall_background_scheduler()

        plist_dict = copy(self.LAUNCHD_AGENT_DICT)

        if is_production_environment(ci_means_dev=False):
            plist_dict["ProgramArguments"] = [sys.executable, "sync"]
        else:
            plist_dict["ProgramArguments"] = [sys.executable, "focus_time_app/main.py", "sync"]
            plist_dict["WorkingDirectory"] = str(Path(__file__).parent.parent.parent.parent.parent)

        with self.LAUNCHD_AGENT_FILE.open("wb") as f:
            plistlib.dump(plist_dict, f)

        subprocess.run(["/bin/launchctl", "load", str(self.LAUNCHD_AGENT_FILE)], check=True, capture_output=True)

    def uninstall_background_scheduler(self):
        subprocess.run(["/bin/launchctl", "unload", str(self.LAUNCHD_AGENT_FILE)], check=True, capture_output=True)
        self.LAUNCHD_AGENT_FILE.unlink(missing_ok=True)
