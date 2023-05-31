from cli.background_scheduler import BackgroundSchedulerImpl
from command_execution import CommandExecutorImpl


class UninstallCommand:
    def run(self):
        CommandExecutorImpl.uninstall_dnd_helpers()
        BackgroundSchedulerImpl.uninstall_background_scheduler()
