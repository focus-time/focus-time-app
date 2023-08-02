import logging
from datetime import datetime, timedelta
from typing import Tuple
from zoneinfo import ZoneInfo

import caldav
import icalendar
import pytest

from tests import CalDavTestCredentials, now_without_micros

logger = logging.getLogger("TestCalDavClient")


@pytest.fixture
def caldav_calendar() -> caldav.Calendar:
    test_credentials = CalDavTestCredentials.read_from_env()
    with caldav.DAVClient(url=test_credentials.calendar_url, username=test_credentials.username,
                          password=test_credentials.password) as client:
        client.propfind()
        my_principal = client.principal()
        calendars = my_principal.calendars()
        assert len(calendars) > 0
        calendar = calendars[0]

        events = calendar.search(start=datetime.now(ZoneInfo('UTC')) - timedelta(days=1),
                                 end=datetime.now(ZoneInfo('UTC')) + timedelta(days=1), event=True, expand=True)
        for event in events:
            event.delete()

        yield calendar


def get_typical_search_time_window() -> Tuple[datetime, datetime]:
    """
    Returns a from/to datetime object that is large enough to cover the time period needed by tests, but smaller
    than the interval cleared by the caldav_calendar fixture.
    """
    now = now_without_micros()
    start = now - timedelta(hours=12)
    end = now + timedelta(hours=12)
    return start, end


class TestCalDavClient:
    """
    Tests various features of the CalDAV Python library
    """

    def test_create_read_delete_event(self, caldav_calendar: caldav.Calendar):
        """
        Tests that creating an event works (we can read it, and it has no reminder set). Then deleting it should work,
        and we verify that it can no longer be found.
        """
        start = now_without_micros()
        end = start + timedelta(minutes=2)
        summary = "Some useful subject"
        event = caldav_calendar.save_event(dtstart=start, dtend=end, summary=summary)

        search_start, search_end = get_typical_search_time_window()
        events = caldav_calendar.search(start=search_start, end=search_end, event=True, expand=True)
        assert len(events) == 1
        event_component = events[0].icalendar_component
        assert event.id == event_component["uid"]
        assert start == event_component["dtstart"].dt
        assert end == event_component["dtend"].dt
        assert summary == event_component["summary"]
        assert len(event_component.subcomponents) == 0  # no reminders configured

        events[0].delete()

        events = caldav_calendar.search(start=search_start, end=search_end, event=True, expand=True)
        assert len(events) == 0

    def test_create_with_reminder(self, caldav_calendar: caldav.Calendar):
        """
        Creates an event that has a reminder time set, then reads the event, verifying that the reminder is really set.
        Finally, removes the reminder again.
        """
        start = now_without_micros()
        end = start + timedelta(minutes=2)
        summary = "Event with reminder"
        # Note: save_event() does not support adding reminders (iCal-speak: "alarm") directly
        # (see https://github.com/python-caldav/caldav/issues/132), thus we have to create the event without an alarm
        # and then add the alarm afterward
        event = caldav_calendar.save_event(dtstart=start, dtend=end, summary=summary)
        ia = icalendar.Alarm()
        ia.add("action", "DISPLAY")
        ia.add("trigger", timedelta(minutes=-15))
        event.icalendar_component.add_component(ia)
        event.save()

        # Verify that the reminder is really set
        search_start, search_end = get_typical_search_time_window()
        events = caldav_calendar.search(start=search_start, end=search_end, event=True, expand=True)
        assert len(events) == 1
        event_component = events[0].icalendar_component
        assert len(event_component.subcomponents) == 1
        alarm: icalendar.Alarm = event_component.subcomponents[0]
        assert (isinstance(alarm, icalendar.Alarm))
        assert alarm["TRIGGER"].dt == timedelta(minutes=-15)

        # Remove the reminder again
        del event_component.subcomponents[0]
        events[0].save()

        # Verify that the reminder has been removed
        events = caldav_calendar.search(start=search_start, end=search_end, event=True, expand=True)
        assert len(events) == 1
        assert len(events[0].icalendar_component.subcomponents) == 0

    def test_update_event(self, caldav_calendar: caldav.Calendar):
        """
        Creates an event, saves it, then changes the start date, saves the changes, and verifies that the changes have
        been applied successfully.
        """
        now = now_without_micros()
        start = now
        end = start + timedelta(minutes=10)
        event = caldav_calendar.save_event(dtstart=start, dtend=end, summary="Event")

        updated_start = start + timedelta(minutes=2)
        event.icalendar_component["dtstart"].dt = updated_start
        event.save()

        # Verify that the reminder is really set
        search_start, search_end = get_typical_search_time_window()
        events = caldav_calendar.search(start=search_start, end=search_end, event=True, expand=True)
        assert len(events) == 1
        event_component = events[0].icalendar_component
        assert event.id == event_component["uid"]
        assert updated_start == event_component["dtstart"].dt
        assert end == event_component["dtend"].dt

    def test_sorting_by_date(self, caldav_calendar: caldav.Calendar):
        """
        Creates multiple events, retrieves them, and verifies that the CalDAV library applies the date-based sorting
        properly.
        """
        now = now_without_micros()
        start1 = now + timedelta(minutes=30)
        end1 = start1 + timedelta(minutes=10)
        start2 = now
        end2 = start2 + timedelta(minutes=10)
        # Note: save_event() does not support adding reminders (iCal-speak: "alarm") directly
        # (see https://github.com/python-caldav/caldav/issues/132), thus we have to create the event without an alarm
        # and then add the alarm afterward
        event1 = caldav_calendar.save_event(dtstart=start1, dtend=end1, summary="Event 1")
        event2 = caldav_calendar.save_event(dtstart=start2, dtend=end2, summary="Event 2")

        # Verify that the events are returned with the start time in ascending order
        search_start, search_end = get_typical_search_time_window()
        events = caldav_calendar.search(start=search_start, end=search_end, event=True, expand=True,
                                        sort_keys=("dtstart",))
        assert len(events) == 2
        assert event2.id == events[0].icalendar_component["uid"]
        assert event1.id == events[1].icalendar_component["uid"]

    def test_filtering_by_summary(self, caldav_calendar: caldav.Calendar):
        """
        Creates two events with different subjects, then retrieves the events using a filter that should only match
        one event. However, the test (Nextcloud) server does not honor the filter query sent to it, and still returns
        both events, meaning that client-side filtering is highly recommended.
        """
        start = now_without_micros()
        end = start + timedelta(minutes=10)

        event_foo = caldav_calendar.save_event(dtstart=start, dtend=end, summary="Foo")
        event_bar = caldav_calendar.save_event(dtstart=start, dtend=end, summary="Bar")
        assert event_foo.id != event_bar.id

        search_start, search_end = get_typical_search_time_window()
        events = caldav_calendar.search(start=search_start, end=search_end, event=True, expand=True, summary="Foo")
        assert len(events) == 2
