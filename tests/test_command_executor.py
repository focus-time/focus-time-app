from focus_time_app.command_execution import CommandExecutorImpl
from focus_time_app.command_execution.abstract_command_executor import CommandExecutorConstants
from tests.conftest import ConfiguredCommands


class TestCommandExecutor:
    """
    Unit tests for the CommandExecutor implementation.
    """

    def test_commands(self, start_commands: ConfiguredCommands, stop_commands: ConfiguredCommands):
        CommandExecutorImpl.execute_commands(start_commands.commands,
                                             dnd_profile_name=CommandExecutorConstants.WINDOWS_FOCUS_ASSIST_PRIORITY_ONLY_PROFILE)

        if CommandExecutorImpl.is_dnd_helper_installed():
            assert CommandExecutorImpl.is_dnd_active()
        assert start_commands.verification_file_path.read_text() == "start\n"

        CommandExecutorImpl.execute_commands(stop_commands.commands,
                                             dnd_profile_name=CommandExecutorConstants.WINDOWS_FOCUS_ASSIST_PRIORITY_ONLY_PROFILE)

        if CommandExecutorImpl.is_dnd_helper_installed():
            assert not CommandExecutorImpl.is_dnd_active()
        assert stop_commands.verification_file_path.read_text() == "start\nstop\n"
