import sys
from typing import Optional

from focus_time_app.cli.background_scheduler.abstract_background_scheduler import AbstractBackgroundScheduler

BackgroundSchedulerImpl: Optional[AbstractBackgroundScheduler] = None

if sys.platform == "win32":
    from focus_time_app.cli.background_scheduler.impl.win_background_scheduler import WindowsBackgroundScheduler

    BackgroundSchedulerImpl = WindowsBackgroundScheduler()
elif sys.platform == "darwin":
    from focus_time_app.cli.background_scheduler.impl.macos_background_scheduler import MacOsBackgroundScheduler

    BackgroundSchedulerImpl = MacOsBackgroundScheduler()
else:
    raise NotImplementedError
