---
name: punchcli
description: CLI time tracker. Logs sessions to SQLite per-project. Use when an agent needs to record, query, edit, or report on time spent.
---

# punchcli

`punch <command> [options]`. Storage = `.punch/` at repo root (walk-up discovery; override with `PUNCH_DIR`).

## Commands

### `punch init`
Create `.punch/` in cwd. Idempotent. Writes `.punch/.gitignore` (ignores `state.json`).

### `punch in`
Start tracking. Fails if already active.
- `-m, --message TEXT` — free text, ≤256 chars, no newlines.
- `-t, --tags LIST` — comma-separated, lowercase `[a-z0-9_-]{1,32}`, max 5.

### `punch out`
Stop active session, append row, regenerate `REPORT.md`. No flags.

### `punch status`
Print active session info or "no active session". No flags. Exit 0 either way.

### `punch report`
Print totals summary.
- `--today` / `--week` / `--month`
- `--from YYYY-MM-DD` / `--to YYYY-MM-DD`
- `--tag NAME`
- `--write` — also regenerate `REPORT.md`.

### `punch log`
Print recent sessions table.
- `--today` / `--week` / `--month`
- `--tag NAME`
- `-n N` — last N (default 20).

### `punch tags`
List tags with totals + last-used. No flags.

### `punch edit ID`
Update entry by id (positional). At least one update flag required.
- `--start TS` — new start timestamp.
- `--end TS` — new end timestamp.
- `-m, --message TEXT` — `""` to clear.
- `-t, --tags LIST` — `""` to clear.

### `punch add`
Backfill a past session. Provide exactly two of `--from`, `--to`, `--duration`.
- `--from TS` / `--to TS`
- `--duration D` — e.g. `45m`, `2h`, `1h30m`.
- `-m, --message TEXT`
- `-t, --tags LIST`
- `--force` — skip overlap-confirmation prompt.

### `punch export`
Write entries to stdout. Format flag required.
- `--csv` | `--md` (mutually exclusive, required)
- `--from YYYY-MM-DD` / `--to YYYY-MM-DD`
- `--tag NAME`

### `punch import FILE`
Bulk-import CSV. Header required, must include `started_at,ended_at`. `id` and `duration_s` columns ignored/recomputed. Invalid rows skipped with warnings.
- `--dry-run` — parse + validate, insert nothing.
- `--force` — skip per-row overlap prompt.

## Timestamp formats
- ISO 8601 with offset: `2026-04-30T09:00:00+02:00`
- `YYYY-MM-DD HH:MM` (local tz)
- `HH:MM` (today, local tz)
- `today HH:MM` / `yesterday HH:MM`

## Duration formats
`<int>m`, `<int>h`, `<int>h<int>m`. Examples: `45m`, `2h`, `1h30m`.

## Exit codes
- `0` success
- `1` user error (bad args, validation, no active session, already tracking)
- `2` I/O or database error

## Environment
- `PUNCH_DIR` — override `.punch/` discovery.
