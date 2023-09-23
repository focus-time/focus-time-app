import typer

from focus_time_app.cli.background_scheduler import BackgroundSchedulerImpl
from focus_time_app.command_execution import CommandExecutorImpl


class DoctorCommand:
    def run(self):
        BackgroundSchedulerImpl.install_or_repair_background_scheduler()
        typer.echo("Background scheduler has been reinstalled")

        CommandExecutorImpl.uninstall_dnd_helpers()
        CommandExecutorImpl.install_dnd_helpers()
