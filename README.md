# GitHub Achievements Lab

This repository is a controlled experiment documenting how GitHub achievements may be triggered through ordinary repository activity.

## Purpose

The goal of this project is to:
- Explore how GitHub achievements work
- Document which actions appear to trigger them
- Demonstrate edge cases in contribution and reputation systems
- Keep the experiment transparent, bounded, and auditable

## What This Project Contains

- A small activity tracker CLI in `src/tracker.py`
- Structured experiment notes in `docs/`
- A human-readable activity log in `logs/activity-log.md`
- Tests for the local tracking logic in `tests/`

## Ethics & Disclaimer

This repository is created for educational and research purposes only.

It does NOT aim to:
- exploit GitHub
- manipulate rankings or reputation
- encourage spammy behavior
- involve external repositories, unrelated users, or multiple accounts

Instead, it highlights how certain achievements can be obtained through minimal or artificial actions, in order to:
- raise awareness
- improve system transparency
- encourage better design of contribution metrics

## Operating Boundaries

All actions performed here should be:
- contained within a single repository
- executed by a single user
- limited in volume
- documented in the activity log
- stopped after a fixed time window if an experiment session is running

## Local Usage

Record an event:

```powershell
python src/tracker.py record --type commit --title "docs: update methodology"
```

Show a summary:

```powershell
python src/tracker.py summary
```

Show a filtered summary as JSON:

```powershell
python src/tracker.py summary --type commit --since 2026-05-04T00:00:00Z --json --total
```

List recent events:

```powershell
python src/tracker.py list --reverse --limit 5
```

Export filtered events to CSV:

```powershell
python src/tracker.py export-csv --type issue --output exports/issues.csv
```

Validate recorded events:

```powershell
python src/tracker.py validate
```

Run tests:

```powershell
python -m unittest discover -s tests
```

## Status

Ongoing experiment.



