from focus_time_app.cli.background_scheduler.abstract_background_scheduler import AbstractBackgroundScheduler


class WindowsBackgroundScheduler(AbstractBackgroundScheduler):
    def install_or_repair_background_scheduler(self):
        pass

    def uninstall_background_scheduler(self):
        super().uninstall_background_scheduler()
