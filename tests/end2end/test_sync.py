import logging
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from focus_time_app.command_execution import CommandExecutorImpl
from focus_time_app.focus_time_calendar.event import CalendarType
from tests.conftest import ConfiguredCLI
from tests.utils import run_cli_command_handle_output_error

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
        if configured_cli_no_bg_jobs.configuration.calendar_type is CalendarType.CalDAV:
            pytest.skip("As this test is slow (due to 'sleep()'), run it only for Outlook365")

        calendar_adapter = configured_cli_no_bg_jobs.calendar_adapter

        # Create the blocker event that starts in 1 minute and is 2 minutes long
        from_date = datetime.now(ZoneInfo('UTC')) + timedelta(minutes=1)
        to_date = from_date + timedelta(minutes=2)
        calendar_adapter.create_event(from_date, to_date)
        logger.info("Created focus time event")

        # run sync, nothing should change. DND should be turned off
        assert run_cli_command_handle_output_error("sync").startswith("No focus time is active. Exiting ...")
        if CommandExecutorImpl.is_dnd_helper_installed():
            assert not CommandExecutorImpl.is_dnd_active()
        assert not configured_cli_no_bg_jobs.verification_file_path.exists()

        logger.info("Sleeping for one minute")
        time.sleep(60)

        # run sync, should enable DND
        assert "calling start command(s) ..." in run_cli_command_handle_output_error("sync")
        if CommandExecutorImpl.is_dnd_helper_installed():
            assert CommandExecutorImpl.is_dnd_active()
        assert configured_cli_no_bg_jobs.verification_file_path.read_text() == "start\n"
        logger.info("Successfully verified that DND has been activated")

        # run sync again immediately, nothing should change (DND should still be on)
        assert run_cli_command_handle_output_error("sync").startswith("Focus time is already active. Exiting ...")
        if CommandExecutorImpl.is_dnd_helper_installed():
            assert CommandExecutorImpl.is_dnd_active()
        assert configured_cli_no_bg_jobs.verification_file_path.read_text() == "start\n"
        logger.info("Successfully verified that DND is still activated, now sleeping for 2 minutes")

        time.sleep(120)

        # run sync again, DND should be turned off
        assert run_cli_command_handle_output_error("sync").startswith(
            "No focus time is active anymore, calling stop command(s) ...")
        if CommandExecutorImpl.is_dnd_helper_installed():
            assert not CommandExecutorImpl.is_dnd_active()
        assert configured_cli_no_bg_jobs.verification_file_path.read_text() == "start\nstop\n"
        logger.info("Successfully verified that DND has been deactivated")

        # run sync again immediately, nothing should change
        assert run_cli_command_handle_output_error("sync").startswith("No focus time is active. Exiting ...")
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

        # Create the blocker event that starts now and is 2 minutes long
        from_date = datetime.now(ZoneInfo('UTC'))
        to_date = from_date + timedelta(minutes=2)
        calendar_adapter.create_event(from_date, to_date)
        logger.info("Created focus time event")

        # DND should be turned off
        if CommandExecutorImpl.is_dnd_helper_installed():
            assert not CommandExecutorImpl.is_dnd_active()
        assert not configured_cli_with_bg_jobs.verification_file_path.exists()

        # Note: the GitHub CI/CD runners are slow to run the jobs - waiting for EXACTLY 60 seconds was too little,
        # the background job was still in a running state
        logger.info("Sleeping for one minute and 20 seconds")
        time.sleep(80)

        if CommandExecutorImpl.is_dnd_helper_installed():
            assert CommandExecutorImpl.is_dnd_active()
        assert configured_cli_with_bg_jobs.verification_file_path.read_text() == "start\n"
        logger.info("Successfully verified that DND has been activated, now sleeping for 2 minutes")

        time.sleep(120)

        if CommandExecutorImpl.is_dnd_helper_installed():
            assert not CommandExecutorImpl.is_dnd_active()
        assert configured_cli_with_bg_jobs.verification_file_path.read_text() == "start\nstop\n"
        logger.info("Successfully verified that DND has been deactivated")

    def test_reminder(self, configured_cli_no_bg_jobs: ConfiguredCLI):
        """
        Verifies that the "sync" command enables the reminder for focus time blocker events that were created without
        such a reminder.
        """
        # Create the blocker event that starts now and is 2 minutes long, having a different reminder time configured
        old_event_reminder_time_minutes = configured_cli_no_bg_jobs.configuration.event_reminder_time_minutes
        new_event_reminder_time_minutes = 30
        assert new_event_reminder_time_minutes != old_event_reminder_time_minutes, "Choose a new reminder time " \
                                                                                   "that is different"
        try:
            configured_cli_no_bg_jobs.configuration.event_reminder_time_minutes = new_event_reminder_time_minutes

            now = datetime.now(ZoneInfo('UTC'))
            from_date = now
            to_date = from_date + timedelta(minutes=2)
            configured_cli_no_bg_jobs.calendar_adapter.create_event(from_date, to_date)
        finally:
            # Restore the original setting to avoid causing problems in other tests
            configured_cli_no_bg_jobs.configuration.event_reminder_time_minutes = old_event_reminder_time_minutes

        # Verify that the event reminder is not set
        events = configured_cli_no_bg_jobs.calendar_adapter.get_events((now - timedelta(minutes=1),
                                                                        now + timedelta(minutes=2)))
        assert len(events) == 1
        assert events[0].reminder_in_minutes == new_event_reminder_time_minutes

        # The sync call should set the event reminder time
        assert "calling start command(s) ..." in run_cli_command_handle_output_error("sync")

        events = configured_cli_no_bg_jobs.calendar_adapter.get_events((now - timedelta(minutes=1),
                                                                        now + timedelta(minutes=2)))
        assert len(events) == 1
        assert events[0].reminder_in_minutes == configured_cli_no_bg_jobs.configuration.event_reminder_time_minutes
