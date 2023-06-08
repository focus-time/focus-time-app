import logging
import subprocess
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

    Note: you should set the environment variable "CI" to any value when running pytest.
    """

    def test_manual_on_off_sync(self, configured_cli_no_bg_jobs: ConfiguredCLI):
        """
        Performs all "sync" calls manually (without using the background scheduler). Creates a focus-time event in
        the near future, and verifies that "sync" always does the right thing (before the event starts, during the
        event, and afterwards).
        """
        calendar_adapter = configured_cli_no_bg_jobs.calendar_adapter

        # Create the blocker event that starts in 1 minute and is 2 minutes long
        from_date = datetime.now(ZoneInfo('UTC')) + timedelta(minutes=1)
        to_date = from_date + timedelta(minutes=2)
        calendar_adapter.create_event(from_date, to_date)
        logger.info("Created focus time event")

        # run sync, nothing should change. DND should be turned off
        assert self._run_sync().startswith("No focus time is active. Exiting ...")
        assert not CommandExecutorImpl.is_dnd_active()

        logger.info("Sleeping for one minute")
        time.sleep(60)

        # run sync, should enable DND
        assert self._run_sync().startswith("Found a new focus time, calling start command(s) ...")
        assert CommandExecutorImpl.is_dnd_active()
        logger.info("Successfully verified that DND has been activated")

        # run sync again immediately, nothing should change (DND should still be on)
        assert self._run_sync().startswith("Focus time is already active. Exiting ...")
        assert CommandExecutorImpl.is_dnd_active()
        logger.info("Successfully verified that DND is still activated, now sleeping for 2 minutes")

        time.sleep(120)

        # run sync again, DND should be turned off
        assert self._run_sync().startswith("No focus time is active, calling stop command(s) ...")
        assert not CommandExecutorImpl.is_dnd_active()
        logger.info("Successfully verified that DND has been deactivated")

        # run sync again immediately, nothing should change
        assert self._run_sync().startswith("No focus time is active. Exiting ...")
        assert not CommandExecutorImpl.is_dnd_active()
        logger.info("Successfully verified that DND is still deactivated")

    @staticmethod
    def _run_sync() -> str:
        # TODO get better output, the stringification of CalledProcessError does not include stdout or stderr, but it
        #  would be useful to have it
        finished_process = subprocess.run([get_frozen_binary_path(), "sync"], check=True, capture_output=True)
        return finished_process.stdout.decode("utf-8")
