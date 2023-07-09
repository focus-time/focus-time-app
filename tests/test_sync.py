import logging
import subprocess
import sys
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from focus_time_app.command_execution import CommandExecutorImpl
from tests.conftest import ConfiguredCLI
from tests.test_utils import get_frozen_binary_path

logger = logging.getLogger("TestCLISyncCommand")


class TestCLISyncCommand:
    """
    Tests the "sync" CLI command.

    Note: you should set the environment variable defined in CI_ENV_VAR_NAME to any value when running pytest.
    """

    def test_manual_on_off_sync(self, configured_cli_no_bg_jobs: ConfiguredCLI):
        """
        Performs all "sync" calls manually (without using the background scheduler). Creates a focus-time event in
        the near future, and verifies that "sync" always does the right thing (before the event starts, during the
        event, and afterwards).

        Note: DND / Focus time mode is only verified if the helper is actually installed.
        """
        calendar_adapter = configured_cli_no_bg_jobs.calendar_adapter
        configured_cli_no_bg_jobs.verification_file_path.unlink(missing_ok=True)

        # Create the blocker event that starts in 1 minute and is 2 minutes long
        from_date = datetime.now(ZoneInfo('UTC')) + timedelta(minutes=1)
        to_date = from_date + timedelta(minutes=2)
        calendar_adapter.create_event(from_date, to_date)
        logger.info("Created focus time event")

        # run sync, nothing should change. DND should be turned off
        assert self._run_sync_command().startswith("No focus time is active. Exiting ...")
        if CommandExecutorImpl.is_dnd_helper_installed():
            assert not CommandExecutorImpl.is_dnd_active()
        assert not configured_cli_no_bg_jobs.verification_file_path.exists()

        logger.info("Sleeping for one minute")
        time.sleep(60)

        # run sync, should enable DND
        assert self._run_sync_command().startswith("Found a new focus time, calling start command(s) ...")
        if CommandExecutorImpl.is_dnd_helper_installed():
            assert CommandExecutorImpl.is_dnd_active()
        assert configured_cli_no_bg_jobs.verification_file_path.read_text() == "start\n"
        logger.info("Successfully verified that DND has been activated")

        # run sync again immediately, nothing should change (DND should still be on)
        assert self._run_sync_command().startswith("Focus time is already active. Exiting ...")
        if CommandExecutorImpl.is_dnd_helper_installed():
            assert CommandExecutorImpl.is_dnd_active()
        assert configured_cli_no_bg_jobs.verification_file_path.read_text() == "start\n"
        logger.info("Successfully verified that DND is still activated, now sleeping for 2 minutes")

        time.sleep(120)

        # run sync again, DND should be turned off
        assert self._run_sync_command().startswith("No focus time is active, calling stop command(s) ...")
        if CommandExecutorImpl.is_dnd_helper_installed():
            assert not CommandExecutorImpl.is_dnd_active()
        assert configured_cli_no_bg_jobs.verification_file_path.read_text() == "start\nstop\n"
        logger.info("Successfully verified that DND has been deactivated")

        # run sync again immediately, nothing should change
        assert self._run_sync_command().startswith("No focus time is active. Exiting ...")
        if CommandExecutorImpl.is_dnd_helper_installed():
            assert not CommandExecutorImpl.is_dnd_active()
        assert configured_cli_no_bg_jobs.verification_file_path.read_text() == "start\nstop\n"
        logger.info("Successfully verified that DND is still deactivated")

    def test_automated_on_off_sync(self, configured_cli_with_bg_jobs: ConfiguredCLI):
        """
        Like test_manual_on_off_sync, but the "sync" command is not called manually. Instead, the background scheduler
        is expected to make the sync call internally.
        """
        calendar_adapter = configured_cli_with_bg_jobs.calendar_adapter
        configured_cli_with_bg_jobs.verification_file_path.unlink(missing_ok=True)

        # TODO Remove
        if sys.platform == "win32":
            output = subprocess.check_output(["schtasks"], shell=True).decode("utf-8")
            logger.info(output)

        # Create the blocker event that starts now and is 2 minutes long
        from_date = datetime.now(ZoneInfo('UTC'))
        to_date = from_date + timedelta(minutes=2)
        calendar_adapter.create_event(from_date, to_date)
        logger.info("Created focus time event")

        # DND should be turned off
        if CommandExecutorImpl.is_dnd_helper_installed():
            assert not CommandExecutorImpl.is_dnd_active()
        assert not configured_cli_with_bg_jobs.verification_file_path.exists()

        logger.info("Sleeping for one minute")
        time.sleep(60)

        # TODO Remove
        if sys.platform == "win32":
            output = subprocess.check_output(["schtasks"], shell=True).decode("utf-8")
            logger.info(output)

        if CommandExecutorImpl.is_dnd_helper_installed():
            assert CommandExecutorImpl.is_dnd_active()
        assert configured_cli_with_bg_jobs.verification_file_path.read_text() == "start\n"
        logger.info("Successfully verified that DND has been activated, now sleeping for 2 minutes")

        time.sleep(120)

        if CommandExecutorImpl.is_dnd_helper_installed():
            assert not CommandExecutorImpl.is_dnd_active()
        assert configured_cli_with_bg_jobs.verification_file_path.read_text() == "start\nstop\n"
        logger.info("Successfully verified that DND has been deactivated")

    @staticmethod
    def _run_sync_command() -> str:
        try:
            finished_process = subprocess.run([get_frozen_binary_path(), "sync"], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            # Handle the error explicitly, because the stringification of CalledProcessError does not include stdout
            # or stderr, which is very useful for diagnosing errors
            raise RuntimeError(
                f"Encountered CalledProcessError: {e}.\nStdout:\n{e.stdout.decode('utf-8')}"
                f"\n\nStderr:\n{e.stderr.decode('utf-8')}") from None
        return finished_process.stdout.decode("utf-8")
