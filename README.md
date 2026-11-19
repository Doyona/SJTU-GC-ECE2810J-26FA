# ECE2810J Fall 2026 · Project 3 Task 3

Website: https://Doyona.github.io/SJTU-GC-ECE2810J-26FA/

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
