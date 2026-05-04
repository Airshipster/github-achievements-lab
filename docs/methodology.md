# Methodology

This experiment treats GitHub achievements as observable product behavior rather than as a target for spam.

## Principles

- Keep all activity inside one repository.
- Avoid external repositories, unrelated users, and multiple accounts.
- Prefer meaningful code, documentation, tests, and refactoring over empty changes.
- Record actions in `logs/activity-log.md` so the experiment remains auditable.
- Stop any manual experiment session after 60 minutes.

## Suggested Manual Workflow

1. Make a small local code or documentation change.
2. Record the action with `src/tracker.py`.
3. Commit with a clear, varied message.
4. If using GitHub, keep PRs/issues limited and relevant to the project.
5. Update `docs/findings.md` when an observed result changes.

## Non-Goals

- No automated GitHub API activity for achievements.
- No high-volume issue or PR churn.
- No activity involving unrelated repositories or users.
