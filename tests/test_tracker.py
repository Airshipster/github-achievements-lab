import tempfile
import unittest
from pathlib import Path

from src.tracker import (
    ActivityEvent,
    events_to_csv,
    export_csv,
    filter_events,
    format_event_table,
    limit_events,
    load_events,
    order_events,
    parse_timestamp,
    record_event,
    save_events,
    summarize,
    summary_total,
    summary_to_json,
    validate_events,
)


class TrackerTests(unittest.TestCase):
    def test_order_events_can_reverse_event_order(self):
        events = [
            ActivityEvent("2026-05-04T00:00:00+00:00", "commit", "initial commit"),
            ActivityEvent("2026-05-04T00:01:00+00:00", "issue", "track question"),
        ]

        self.assertEqual([event.title for event in order_events(events, reverse=True)], ["track question", "initial commit"])
    def test_limit_events_returns_requested_prefix(self):
        events = [
            ActivityEvent("2026-05-04T00:00:00+00:00", "commit", "initial commit"),
            ActivityEvent("2026-05-04T00:01:00+00:00", "issue", "track question"),
            ActivityEvent("2026-05-04T00:02:00+00:00", "commit", "docs update"),
        ]

        self.assertEqual([event.title for event in limit_events(events, 2)], ["initial commit", "track question"])

    def test_limit_events_rejects_negative_limit(self):
        with self.assertRaises(ValueError):
            limit_events([], -1)
    def test_validate_events_returns_count_for_valid_events(self):
        events = [
            ActivityEvent("2026-05-04T00:00:00+00:00", "commit", "initial commit"),
            ActivityEvent("2026-05-04T00:01:00+00:00", "issue", "track question"),
        ]

        self.assertEqual(validate_events(events), 2)
    def test_summarize_counts_events_by_type(self):
        events = [
            ActivityEvent("2026-05-04T00:00:00+00:00", "commit", "initial commit"),
            ActivityEvent("2026-05-04T00:01:00+00:00", "commit", "docs update"),
            ActivityEvent("2026-05-04T00:02:00+00:00", "issue", "track question"),
        ]

        self.assertEqual(summarize(events), {"commit": 2, "issue": 1})

    def test_summary_total_counts_all_summary_values(self):
        self.assertEqual(summary_total({"commit": 2, "issue": 1}), 3)
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

    def test_record_event_accepts_explicit_timestamp(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            data_path = Path(tmp_dir) / "events.json"
            markdown_path = Path(tmp_dir) / "activity-log.md"
            event = record_event(
                "note",
                "imported event",
                timestamp="2026-05-04T00:00:00Z",
                data_path=data_path,
                markdown_path=markdown_path,
            )

        self.assertEqual(event.timestamp, "2026-05-04T00:00:00Z")

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

    def test_filtered_events_can_be_exported_to_csv(self):
        events = [
            ActivityEvent("2026-05-04T00:00:00+00:00", "commit", "initial commit"),
            ActivityEvent("2026-05-04T00:01:00+00:00", "issue", "track question"),
            ActivityEvent("2026-05-04T00:02:00+00:00", "commit", "docs update"),
        ]

        csv_output = events_to_csv(filter_events(events, event_type="commit", since="2026-05-04T00:01:00Z"))

        self.assertIn("docs update", csv_output)
        self.assertNotIn("initial commit", csv_output)
        self.assertNotIn("track question", csv_output)

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









