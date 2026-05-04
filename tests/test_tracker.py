import tempfile
import unittest
from pathlib import Path

from src.tracker import (
    ActivityEvent,
    events_to_csv,
    export_csv,
    filter_events,
    format_event_table,
    load_events,
    parse_timestamp,
    save_events,
    summarize,
    summary_to_json,
)


class TrackerTests(unittest.TestCase):
    def test_summarize_counts_events_by_type(self):
        events = [
            ActivityEvent("2026-05-04T00:00:00+00:00", "commit", "initial commit"),
            ActivityEvent("2026-05-04T00:01:00+00:00", "commit", "docs update"),
            ActivityEvent("2026-05-04T00:02:00+00:00", "issue", "track question"),
        ]

        self.assertEqual(summarize(events), {"commit": 2, "issue": 1})

    def test_summary_to_json_outputs_sorted_pretty_json(self):
        self.assertEqual(summary_to_json({"issue": 1, "commit": 2}), '{\n  "commit": 2,\n  "issue": 1\n}\n')

    def test_filter_events_returns_only_requested_type(self):
        events = [
            ActivityEvent("2026-05-04T00:00:00+00:00", "commit", "initial commit"),
            ActivityEvent("2026-05-04T00:01:00+00:00", "issue", "track question"),
            ActivityEvent("2026-05-04T00:02:00+00:00", "commit", "docs update"),
        ]

        filtered = filter_events(events, "commit")

        self.assertEqual([event.title for event in filtered], ["initial commit", "docs update"])

    def test_filter_events_without_type_returns_all_events(self):
        events = [
            ActivityEvent("2026-05-04T00:00:00+00:00", "commit", "initial commit"),
            ActivityEvent("2026-05-04T00:01:00+00:00", "issue", "track question"),
        ]

        self.assertEqual(filter_events(events), events)

    def test_filter_events_returns_events_at_or_after_since_timestamp(self):
        events = [
            ActivityEvent("2026-05-04T00:00:00+00:00", "commit", "initial commit"),
            ActivityEvent("2026-05-04T00:01:00+00:00", "issue", "track question"),
            ActivityEvent("2026-05-04T00:02:00+00:00", "commit", "docs update"),
        ]

        filtered = filter_events(events, since="2026-05-04T00:01:00+00:00")

        self.assertEqual([event.title for event in filtered], ["track question", "docs update"])

    def test_filter_events_combines_type_and_since_filters(self):
        events = [
            ActivityEvent("2026-05-04T00:00:00+00:00", "commit", "initial commit"),
            ActivityEvent("2026-05-04T00:01:00+00:00", "issue", "track question"),
            ActivityEvent("2026-05-04T00:02:00+00:00", "commit", "docs update"),
        ]

        filtered = filter_events(events, event_type="commit", since="2026-05-04T00:01:00Z")

        self.assertEqual([event.title for event in filtered], ["docs update"])

    def test_parse_timestamp_treats_naive_values_as_utc(self):
        self.assertEqual(parse_timestamp("2026-05-04T00:00:00").tzinfo.utcoffset(None).total_seconds(), 0)

    def test_format_event_table_renders_headers_and_rows(self):
        events = [
            ActivityEvent("2026-05-04T00:00:00+00:00", "commit", "initial commit"),
            ActivityEvent("2026-05-04T00:01:00+00:00", "issue", "track question"),
        ]

        table = format_event_table(events)

        self.assertIn("timestamp", table)
        self.assertIn("event_type", table)
        self.assertIn("initial commit", table)
        self.assertIn("track question", table)

    def test_format_event_table_handles_empty_events(self):
        self.assertEqual(format_event_table([]), "No events recorded yet.")

    def test_empty_title_is_rejected(self):
        event = ActivityEvent("2026-05-04T00:00:00+00:00", "note", " ")

        with self.assertRaises(ValueError):
            event.validate()

    def test_invalid_timestamp_is_rejected(self):
        event = ActivityEvent("not-a-date", "note", "invalid timestamp")

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
