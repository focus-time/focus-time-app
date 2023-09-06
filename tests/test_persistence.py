from focus_time_app.configuration.configuration import ConfigurationV1
from focus_time_app.configuration.persistence import Persistence
from focus_time_app.focus_time_calendar.event import CalendarType


class TestPersistence:
    """
    Unit tests for the Persistence module.

    Note: you should set the environment variable defined in CI_ENV_VAR_NAME to any value when running pytest.
    """

    def test_store_load_configuration(self):
        """
        Verifies that an example configuration can be successfully stored and loaded, and that both objects have the
        same values.
        """
        config = ConfigurationV1(calendar_type=CalendarType.Outlook365, calendar_look_ahead_hours=3,
                                 calendar_look_back_hours=5, focustime_event_name="ft", start_commands=["start"],
                                 stop_commands=["stop"], dnd_profile_name="dnd", set_event_reminder=True,
                                 event_reminder_time_minutes=15, show_notification=False)
        Persistence.store_configuration(config)

        config_loaded = Persistence.load_configuration()

        assert config == config_loaded
        assert id(config) != id(config_loaded)

    def test_ongoing_focus_time(self):
        """
        Verifies that the persistence of the "is focus time ongoing" marker file works.
        """

        Persistence.set_ongoing_focustime(False)
        assert not Persistence.ongoing_focustime_markerfile_exists()

        # Repeating the call should not raise an error
        Persistence.set_ongoing_focustime(False)
        assert not Persistence.ongoing_focustime_markerfile_exists()

        Persistence.set_ongoing_focustime(True)
        assert Persistence.ongoing_focustime_markerfile_exists()

        # Repeating the call should not raise an error
        Persistence.set_ongoing_focustime(True)
        assert Persistence.ongoing_focustime_markerfile_exists()
