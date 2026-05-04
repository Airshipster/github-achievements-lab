"""Small local tracker for documenting repository activity.

The tracker intentionally works on local Markdown/JSON files only. It does not call
GitHub APIs or automate platform activity.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "logs" / "activity-events.json"
MARKDOWN_LOG = ROOT / "logs" / "activity-log.md"

VALID_EVENT_TYPES = {
    "commit",
    "issue",
    "pull_request",
    "discussion",
    "refactor",
    "note",
}

CSV_FIELDS = ["timestamp", "event_type", "title", "details"]
TABLE_FIELDS = ["timestamp", "event_type", "title"]


@dataclass(frozen=True)
class ActivityEvent:
    timestamp: str
    event_type: str
    title: str
    details: str = ""

    def validate(self) -> None:
        if self.event_type not in VALID_EVENT_TYPES:
            allowed = ", ".join(sorted(VALID_EVENT_TYPES))
            raise ValueError(f"Unknown event type '{self.event_type}'. Expected one of: {allowed}")
        if not self.title.strip():
            raise ValueError("Event title cannot be empty")
        parse_timestamp(self.timestamp)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_events(path: Path = DATA_FILE) -> list[ActivityEvent]:
    if not path.exists():
        return []
    raw_events = json.loads(path.read_text(encoding="utf-8"))
    return [ActivityEvent(**item) for item in raw_events]


def save_events(events: Iterable[ActivityEvent], path: Path = DATA_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = [asdict(event) for event in events]
    path.write_text(json.dumps(serialized, indent=2) + "\n", encoding="utf-8")


def append_markdown_log(event: ActivityEvent, path: Path = MARKDOWN_LOG) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("# Activity Log\n\n", encoding="utf-8")

    details = f" - {event.details.strip()}" if event.details.strip() else ""
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"- {event.timestamp} | {event.event_type} | {event.title}{details}\n")


def record_event(
    event_type: str,
    title: str,
    details: str = "",
    timestamp: str | None = None,
    data_path: Path = DATA_FILE,
    markdown_path: Path = MARKDOWN_LOG,
) -> ActivityEvent:
    event = ActivityEvent(
        timestamp=timestamp or utc_now(),
        event_type=event_type,
        title=title.strip(),
        details=details.strip(),
    )
    event.validate()

    events = load_events()
    events.append(event)
    save_events(events)
    append_markdown_log(event)
    return event


def filter_events(
    events: Iterable[ActivityEvent],
    event_type: str | None = None,
    since: str | None = None,
) -> list[ActivityEvent]:
    since_timestamp = parse_timestamp(since) if since else None
    filtered_events = []
    for event in events:
        event.validate()
        if event_type is not None and event.event_type != event_type:
            continue
        if since_timestamp is not None and parse_timestamp(event.timestamp) < since_timestamp:
            continue
        filtered_events.append(event)
    return filtered_events


def order_events(events: Iterable[ActivityEvent], reverse: bool = False) -> list[ActivityEvent]:
    event_list = list(events)
    return list(reversed(event_list)) if reverse else event_list


def limit_events(events: Iterable[ActivityEvent], limit: int | None = None) -> list[ActivityEvent]:
    event_list = list(events)
    if limit is None:
        return event_list
    if limit < 0:
        raise ValueError("Limit cannot be negative")
    return event_list[:limit]


def validate_events(events: Iterable[ActivityEvent]) -> int:
    count = 0
    for event in events:
        event.validate()
        count += 1
    return count


def summarize(events: Iterable[ActivityEvent]) -> dict[str, int]:
    summary = {event_type: 0 for event_type in sorted(VALID_EVENT_TYPES)}
    for event in events:
        event.validate()
        summary[event.event_type] += 1
    return {key: value for key, value in summary.items() if value}


def summary_total(summary: dict[str, int]) -> int:
    return sum(summary.values())


def summary_to_json(summary: dict[str, int]) -> str:
    return json.dumps(summary, indent=2, sort_keys=True) + "\n"


def events_to_csv(events: Iterable[ActivityEvent]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for event in events:
        event.validate()
        writer.writerow(asdict(event))
    return output.getvalue()


def export_csv(output_path: Path, events: Iterable[ActivityEvent]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(events_to_csv(events), encoding="utf-8")


def format_event_table(events: Iterable[ActivityEvent]) -> str:
    rows = []
    for event in events:
        event.validate()
        rows.append([event.timestamp, event.event_type, event.title])

    if not rows:
        return "No events recorded yet."

    widths = [len(field) for field in TABLE_FIELDS]
    for row in rows:
        widths = [max(width, len(value)) for width, value in zip(widths, row)]

    header = "  ".join(field.ljust(width) for field, width in zip(TABLE_FIELDS, widths))
    divider = "  ".join("-" * width for width in widths)
    body = ["  ".join(value.ljust(width) for value, width in zip(row, widths)) for row in rows]
    return "\n".join([header, divider, *body])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Track local experiment activity")
    subcommands = parser.add_subparsers(dest="command", required=True)

    record = subcommands.add_parser("record", help="record one activity event")
    record.add_argument("--type", required=True, choices=sorted(VALID_EVENT_TYPES))
    record.add_argument("--title", required=True)
    record.add_argument("--details", default="")
    record.add_argument("--timestamp", default=None, help="ISO timestamp for imported events")

    export = subcommands.add_parser("export-csv", help="write recorded events to CSV")
    export.add_argument("--output", required=True, type=Path)
    export.add_argument("--type", choices=sorted(VALID_EVENT_TYPES), default=None)
    export.add_argument("--since", default=None, help="include events at or after this ISO timestamp")

    list_events = subcommands.add_parser("list", help="print recorded events")
    list_events.add_argument("--type", choices=sorted(VALID_EVENT_TYPES), default=None)
    list_events.add_argument("--since", default=None, help="include events at or after this ISO timestamp")
    list_events.add_argument("--limit", type=int, default=None, help="maximum number of events to print")
    list_events.add_argument("--reverse", action="store_true", help="print newest matching events first")

    subcommands.add_parser("validate", help="validate recorded events")

    summary = subcommands.add_parser("summary", help="print activity counts by event type")
    summary.add_argument("--type", choices=sorted(VALID_EVENT_TYPES), default=None)
    summary.add_argument("--since", default=None, help="include events at or after this ISO timestamp")
    summary.add_argument("--json", action="store_true", help="print summary as JSON")
    summary.add_argument("--total", action="store_true", help="include total event count")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.command == "record":
        event = record_event(args.type, args.title, args.details, args.timestamp)
        print(f"Recorded {event.event_type}: {event.title}")
        return 0

    if args.command == "export-csv":
        events = filter_events(load_events(), args.type, args.since)
        export_csv(args.output, events)
        print(f"Exported activity events to {args.output}")
        return 0

    if args.command == "validate":
        count = validate_events(load_events())
        print(f"Validated {count} event(s).")
        return 0

    if args.command == "list":
        events = filter_events(load_events(), args.type, args.since)
        print(format_event_table(events))
        return 0

    if args.command == "summary":
        events = filter_events(load_events(), args.type, args.since)
        summary = summarize(events)
        if args.json:
            print(summary_to_json(summary), end="")
            return 0
        if not summary:
            print("No events recorded yet.")
            return 0
        for event_type, count in summary.items():
            print(f"{event_type}: {count}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())








