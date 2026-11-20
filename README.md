# ECE2810J Fall 2026 · Project 3 Task 3

Website: https://Doyona.github.io/SJTU-GC-ECE2810J-26FA/

## Years

Use the Year selector to view a period. Links include `?year=2026-fall`, and CSV filenames include the selected period. Each period has independent results and timestamps. Fall 2026 is the default; archived periods remain available.

Manage the catalog locally:

```sh
python3 -B src/manage_years.py list
python3 -B src/manage_years.py add --year 2027 --term fall --organization COURSE_ORGANIZATION
python3 -B src/manage_years.py set-default 2027-fall
python3 -B src/manage_years.py archive 2026-fall
python3 -B src/manage_years.py unarchive 2026-fall
```

New periods start with no results. `remove-empty ID` removes only a non-default period without results. The default cannot be archived. These commands edit the catalog without committing or pushing.

Synchronization uses an explicit `--year-id` and `--organization`; its defaults remain `2026-fall` and `ece281s1`, even when another period becomes the website default. Configure a future collector for its own period and organization. Archived periods reject new synchronization.

The site displays one best verified release per student. Results are selected by lowest total Task 3 rounds, then fewest movement steps, then earliest result and run ID. Later failed or worse results do not replace a better result. The interface uses English without explanatory notes.

## Hourly synchronization

The local LaunchAgent `com.ece281.task3-sync` runs every 3600 seconds. It reads student `*project` repositories through the Gitea API and verifies bot-authored `p3-release` results against completed release Actions, the `p3` tag, run number, and full commit SHA. A ranked entry requires all 20 Task 3 cases to be verified.

Private snapshots, CSVs, and collection state stay in the ignored `data/task3/` directory. Historical observations are retained so best results survive later submissions. The public aggregate is `data/task3-leaderboard.json`; the website reads `site/data/leaderboard.json`.

Changed data is committed and pushed to `main`, triggering the existing GitHub Pages workflow. An incomplete read preserves published data. Unrelated edits or conflicting history stop automatic publication. Credentials remain in the external Joint-Teapot configuration. The Mac must be logged in, running, and online.

Only observed release history can be retained; overwritten Issue bodies that were never collected cannot be recovered. Release provenance is verified, while historical case-set identity remains unknown.

Logs: `~/Library/Logs/ece281-task3-sync.stdout.log` and `.stderr.log`.

## Local checks

```sh
npm test
python3 -B -m unittest discover -s test -p 'test_*.py'
npm run build
npm run dev
```

Offline conversion: `python3 -B src/sync_task3.py --source-json /path/to/class-lengths.json`.

Live collection uses `--exporter /absolute/path/to/export_class_lengths.py --env-file /absolute/path/to/teapot.env --publish`.

## Files

- `src/sync_task3.py`: collection, validation, best-result selection, and restricted publication.
- `test/test_sync_task3.py`: synchronization tests.
- `site/`: HTML, CSS, JavaScript, and public data.
- `scripts/build.mjs`: validates and builds `dist/`.
- `tests/leaderboard.test.mjs`: ranking, ties, search, CSV, and schema tests.

Maintenance instructions are in `context.md`, `API.md`, and `AGENTS.md`.
