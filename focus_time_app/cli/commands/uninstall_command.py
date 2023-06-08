import typer

from focus_time_app.cli.background_scheduler import BackgroundSchedulerImpl
from focus_time_app.command_execution import CommandExecutorImpl


class UninstallCommand:
    def run(self):
        CommandExecutorImpl.uninstall_dnd_helpers()
        BackgroundSchedulerImpl.uninstall_background_scheduler()
        typer.echo("All scheduled background jobs and Do-Not-Disturb helpers were successfully uninstalled")
