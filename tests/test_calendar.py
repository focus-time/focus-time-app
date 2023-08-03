import logging
from datetime import timedelta

import pytest

from focus_time_app.focus_time_calendar.utils import get_active_focustime_event
from focus_time_app.focus_time_calendar.event import FocusTimeEvent
from tests import now_without_micros
from tests.utils.abstract_testing_calendar_adapter import AbstractTestingCalendarAdapter

logger = logging.getLogger("TestCalendar")


class TestCalendar:
    """
    Unit tests for the focus_time_calendar package.

    Note: you should set the environment variable defined in CI_ENV_VAR_NAME to any value when running pytest.
    """

    def test_adapter_query_timeframes(self, configured_calendar_adapter: AbstractTestingCalendarAdapter):
        """
        First verifies that adapter.get_events() returns an empty list, then creates an event.
        Then, get_events() is called multiple times (each with different from/to dates), expecting that the just-created
        event is contained (or not), depending on the provided from/to datetime.
        """
        events = configured_calendar_adapter.get_events()
        assert not events

        now = now_without_micros()
        from_date = now + timedelta(minutes=30)
        to_date = now + timedelta(minutes=60)
        created_event = configured_calendar_adapter.create_event(from_date, to_date)

        events = configured_calendar_adapter.get_events()
        assert len(events) == 1
        assert events[0].id == created_event.id
        assert events[0].start == from_date
        assert events[0].end == to_date

        empty_query_from = now + timedelta(hours=2)
        empty_query_to = empty_query_from + timedelta(hours=5)
        events_timeshifted = configured_calendar_adapter.get_events(date_range=(empty_query_from, empty_query_to))
        assert not events_timeshifted

    def test_adapter_remove_event(self, configured_calendar_adapter: AbstractTestingCalendarAdapter):
        """
        Verifies that removing an event works, and that it is no longer returned by get_events
        """
        now = now_without_micros()
        from_date1 = now + timedelta(minutes=30)
        to_date1 = now + timedelta(minutes=60)
        created_event1 = configured_calendar_adapter.create_event(from_date1, to_date1)

        from_date2 = now + timedelta(minutes=60)
        to_date2 = now + timedelta(minutes=90)
        created_event2 = configured_calendar_adapter.create_event(from_date2, to_date2)

        configured_calendar_adapter.remove_event(created_event1)

        events = configured_calendar_adapter.get_events()
        assert len(events) == 1
        assert events[0].id == created_event2.id
        assert events[0].start == from_date2
        assert events[0].end == to_date2

    def test_adapter_remove_non_existent_event(self, configured_calendar_adapter: AbstractTestingCalendarAdapter):
        """
        Verifies that trying to remove a non-existent event fails.
        """
        now = now_without_micros()
        from_date1 = now + timedelta(minutes=30)
        to_date1 = now + timedelta(minutes=60)
        created_event1 = configured_calendar_adapter.create_event(from_date1, to_date1)

        configured_calendar_adapter.remove_event(created_event1)

        with pytest.raises(Exception):  # the concrete error depends on the implementation
            configured_calendar_adapter.remove_event(created_event1)

    def test_adapter_update_event(self, configured_calendar_adapter: AbstractTestingCalendarAdapter):
        """
        Verifies that updates made to an event are correctly saved.
        """
        now = now_without_micros()
        from_date1 = now + timedelta(minutes=30)
        to_date1 = now + timedelta(minutes=60)
        created_event1 = configured_calendar_adapter.create_event(from_date1, to_date1)

        reminder_minutes = 100
        configured_calendar_adapter.update_event(event=created_event1, reminder_in_minutes=reminder_minutes)
        events = configured_calendar_adapter.get_events()
        assert len(events) == 1
        assert events[0].reminder_in_minutes == reminder_minutes

        from_date2 = now - timedelta(minutes=30)
        configured_calendar_adapter.update_event(event=created_event1, from_date=from_date2)
        events = configured_calendar_adapter.get_events()
        assert len(events) == 1
        assert events[0].reminder_in_minutes == reminder_minutes
        assert events[0].start == from_date2
        assert events[0].end == to_date1

        to_date2 = now
        configured_calendar_adapter.update_event(event=created_event1, to_date=to_date2)
        events = configured_calendar_adapter.get_events()
        assert len(events) == 1
        assert events[0].reminder_in_minutes == reminder_minutes
        assert events[0].start == from_date2
        assert events[0].end == to_date2

        created_event1.start = from_date2
        created_event1.end = to_date2
        configured_calendar_adapter.update_event(event=created_event1, reminder_in_minutes=0)
        events = configured_calendar_adapter.get_events()
        assert len(events) == 1
        assert events[0].reminder_in_minutes == 0

    def test_active_focus_time(self):
        """
        Tests that the get_active_focustime_event() function correctly determines an ongoing focus time event.
        """
        # Case 1: One event in the past, one now, one in the future
        now = now_without_micros()
        case_1 = [
            FocusTimeEvent(id="1", start=now - timedelta(hours=2), end=now - timedelta(hours=1), reminder_in_minutes=0),
            FocusTimeEvent(id="2", start=now - timedelta(hours=1), end=now + timedelta(hours=1), reminder_in_minutes=0),
            FocusTimeEvent(id="3", start=now + timedelta(hours=2), end=now + timedelta(hours=3), reminder_in_minutes=0)
        ]

        active_event_case_1 = get_active_focustime_event(events=case_1)
        assert active_event_case_1 is not None
        assert active_event_case_1.id == "2"

        # Case 2: check that no ongoing focus time is found
        now = now_without_micros()
        case_2 = [
            FocusTimeEvent(id="1", start=now - timedelta(hours=2), end=now - timedelta(hours=1), reminder_in_minutes=0),
            FocusTimeEvent(id="3", start=now + timedelta(hours=2), end=now + timedelta(hours=3), reminder_in_minutes=0)
        ]

        active_event_case_2 = get_active_focustime_event(events=case_2)
        assert active_event_case_2 is None
