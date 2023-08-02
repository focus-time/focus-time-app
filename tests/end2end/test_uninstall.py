import logging
import time

from focus_time_app.command_execution import CommandExecutorImpl
from tests.conftest import ConfiguredCLI
from tests.utils import run_cli_command_handle_output_error

logger = logging.getLogger("TestUninstallSyncCommand")


class TestUninstallSyncCommand:
    """
    Tests the "uninstall" CLI command.

    Note: you should set the environment variable defined in CI_ENV_VAR_NAME and
    USE_INSECURE_PASSWORD_PROMPT_ENV_VAR_NAME to any value when running pytest.
    """

    def test_uninstall(self, configured_cli_with_bg_jobs: ConfiguredCLI):
        """
        Verifies that after successfully running the "uninstall" command (which, among other things, uninstalls the
        background scheduler), the "sync" command is no longer triggered by the background scheduler.
        """
        run_cli_command_handle_output_error("start", additional_args=["1"])  # 1 minute

        if CommandExecutorImpl.is_dnd_helper_installed():
            assert CommandExecutorImpl.is_dnd_active()
        assert configured_cli_with_bg_jobs.verification_file_path.read_text() == "start\n"

        run_cli_command_handle_output_error("uninstall")

        logger.info("'uninstall' command was called, now waiting for 90 seconds")
        time.sleep(90)

        # Nothing should have changed compared to the previous check:
        if CommandExecutorImpl.is_dnd_helper_installed():
            assert CommandExecutorImpl.is_dnd_active()
        assert configured_cli_with_bg_jobs.verification_file_path.read_text() == "start\n"
