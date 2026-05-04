import tempfile
import unittest
from pathlib import Path

from src.tracker import (
    ActivityEvent,
    events_to_csv,
    export_csv,
    load_events,
    save_events,
    summarize,
)


class TrackerTests(unittest.TestCase):
    def test_summarize_counts_events_by_type(self):
        events = [
            ActivityEvent("2026-05-04T00:00:00+00:00", "commit", "initial commit"),
            ActivityEvent("2026-05-04T00:01:00+00:00", "commit", "docs update"),
            ActivityEvent("2026-05-04T00:02:00+00:00", "issue", "track question"),
        ]

        self.assertEqual(summarize(events), {"commit": 2, "issue": 1})

    def test_empty_title_is_rejected(self):
        event = ActivityEvent("2026-05-04T00:00:00+00:00", "note", " ")

        with self.assertRaises(ValueError):
            event.validate()

    def test_events_round_trip_to_json(self):
        events = [ActivityEvent("2026-05-04T00:00:00+00:00", "refactor", "split helpers")]

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "events.json"
            save_events(events, path)

            self.assertEqual(load_events(path), events)

    def test_events_to_csv_includes_header_and_escaped_fields(self):
        events = [
            ActivityEvent(
                "2026-05-04T00:00:00+00:00",
                "note",
                "review export",
                "contains, comma",
            )
        ]

        self.assertEqual(
            events_to_csv(events),
            'timestamp,event_type,title,details\n2026-05-04T00:00:00+00:00,note,review export,"contains, comma"\n',
        )

    def test_export_csv_writes_file(self):
        events = [ActivityEvent("2026-05-04T00:00:00+00:00", "commit", "initial commit")]

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "exports" / "activity.csv"
            export_csv(path, events)

            self.assertTrue(path.exists())
            self.assertIn("initial commit", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
