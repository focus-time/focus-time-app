import logging
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from focus_time_app.command_execution import CommandExecutorImpl
from tests.conftest import ConfiguredCLI
from tests.test_utils import run_cli_command_handle_output_error

logger = logging.getLogger("TestCLIStartStopCommand")


class TestCLIStartStopCommand:
    """
    Tests the "start" and "stop" CLI commands.

    Note: you should set the environment variable defined in CI_ENV_VAR_NAME and
    USE_INSECURE_PASSWORD_PROMPT_ENV_VAR_NAME to any value when running pytest.
    """
    DATE_COMPARISON_FUZZY_DELTA = timedelta(seconds=10)

    def test_start_stop_simple(self, configured_cli_no_bg_jobs: ConfiguredCLI):
        """
        Runs the "start" command, verifies that DND is activated, waits a bit, then verifies that "sync" does not
        change anything. After running "stop", DND is verified to be deactivated, and that the focus time blocker event
        has been shortened.

        Note: DND / Focus time mode is only verified if the helper is actually installed.
        """
        calendar_adapter = configured_cli_no_bg_jobs.calendar_adapter

        focus_time_duration_minutes = 2
        output = run_cli_command_handle_output_error("start", additional_args=[str(focus_time_duration_minutes)])
        assert output.startswith("Found a new focus time, calling start command(s) ...")

        if CommandExecutorImpl.is_dnd_helper_installed():
            assert CommandExecutorImpl.is_dnd_active()
        assert configured_cli_no_bg_jobs.verification_file_path.read_text() == "start\n"

        # Verify that the created focus time blocker event has the expected start and stop time
        now_at_start = datetime.now(ZoneInfo('UTC'))
        events = calendar_adapter.get_events(from_date=now_at_start - timedelta(minutes=1),
                                             to_date=now_at_start + timedelta(minutes=5))
        assert len(events) == 1
        self._assert_date_approx_equal(actual=events[0].start, expected=now_at_start)
        self._assert_date_approx_equal(actual=events[0].end,
                                       expected=now_at_start + timedelta(minutes=focus_time_duration_minutes))

        # Sleep for a bit
        logger.info("'start' called successfully, sleeping for 1 minute")
        time.sleep(60)

        # Verify that running "sync" does not change anything
        assert run_cli_command_handle_output_error("sync").startswith("Focus time is already active. Exiting ...")
        if CommandExecutorImpl.is_dnd_helper_installed():
            assert CommandExecutorImpl.is_dnd_active()

        # Run the "stop" command, verify that DND is then disabled
        output = run_cli_command_handle_output_error("stop")
        assert output.startswith("No focus time is active, calling stop command(s) ...")

        if CommandExecutorImpl.is_dnd_helper_installed():
            assert not CommandExecutorImpl.is_dnd_active()
        assert configured_cli_no_bg_jobs.verification_file_path.read_text() == "start\nstop\n"

        # Verify that the event has been shortened
        now_at_stop = datetime.now(ZoneInfo('UTC'))
        events_after_stop = calendar_adapter.get_events(from_date=now_at_start - timedelta(minutes=5),
                                                        to_date=now_at_start + timedelta(minutes=5))
        assert len(events_after_stop) == 1
        self._assert_date_approx_equal(actual=events_after_stop[0].start, expected=now_at_start)
        self._assert_date_approx_equal(actual=events_after_stop[0].end, expected=now_at_stop)

        # Verify that running "sync" does not change anything
        assert run_cli_command_handle_output_error("sync").startswith("No focus time is active. Exiting ...")
        if CommandExecutorImpl.is_dnd_helper_installed():
            assert not CommandExecutorImpl.is_dnd_active()
        assert configured_cli_no_bg_jobs.verification_file_path.read_text() == "start\nstop\n"

    def _assert_date_approx_equal(self, actual: datetime, expected: datetime):
        min_dt = expected - self.DATE_COMPARISON_FUZZY_DELTA
        max_dt = expected + self.DATE_COMPARISON_FUZZY_DELTA
        assert min_dt <= actual <= max_dt
