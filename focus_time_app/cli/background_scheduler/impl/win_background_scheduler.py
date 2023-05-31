import datetime
import sys

import win32com.client
from win32com.universal import com_error

from focus_time_app.cli.background_scheduler.abstract_background_scheduler import AbstractBackgroundScheduler


class WindowsBackgroundScheduler(AbstractBackgroundScheduler):
    """
    Windows COM-based implementation that creates background jobs using Windows' "task scheduler" feature.
    """

    TASK_NAME = "Focus Time App Synchronization Trigger"

    def __init__(self):
        self._scheduler = win32com.client.Dispatch("Schedule.Service")
        self._scheduler.Connect()
        self._root_folder = self._scheduler.GetFolder('\\')

    def install_or_repair_background_scheduler(self):
        self.uninstall_background_scheduler()

    def uninstall_background_scheduler(self):
        if self._trigger_sync_task_exists():
            self._root_folder.DeleteTask(WindowsBackgroundScheduler.TASK_NAME, 0)

    def _trigger_sync_task_exists(self) -> bool:
        try:
            self._root_folder.GetTask(WindowsBackgroundScheduler.TASK_NAME)
            return True
        except com_error:  # no such task exists
            return False

    def _create_trigger_sync_task(self):
        task_def = self._scheduler.NewTask(0)

        start_time = datetime.datetime.now() + datetime.timedelta(minutes=1)

        # 2 means "Daily Trigger", 1 means "One time run"
        trigger = task_def.Triggers.Create(2)
        trigger.Repetition.Interval = "PT1M"  # repeat every 1 minute
        trigger.StartBoundary = start_time.isoformat()

        action = task_def.Actions.Create(0)  # 0 means to execute a command
        action.ID = "Trigger sync"
        action.Path = sys.executable
        action.Arguments = "sync"

        # Set parameters
        task_def.RegistrationInfo.Description = "Triggers the Focus Time App synchronization mechanism"
        task_def.Settings.Enabled = True
        task_def.Settings.StopIfGoingOnBatteries = False

        # Register task
        self._root_folder.RegisterTaskDefinition(
            self.TASK_NAME,
            task_def,
            6,  # create or update
            '',  # No user
            '',  # No password
            0  # NOT on logon
        )
