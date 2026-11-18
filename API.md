# Website data and sync

- src/sync_task3.py --exporter PATH --env-file PATH [--website-root PATH] [--publish]: fetch all visible student Task 3 results; store raw exports under data/task3/, update the two public JSON files, and optionally commit/push website data. Without --publish there are no Git writes.
- src/sync_task3.py --source-json PATH [--website-root PATH]: offline conversion/verification; cannot be combined with --publish.
- make_snapshot(source): validate complete collection; choose latest per student across configurations; emit only 20/20 verified integer lengths and explicit coverage.
- update_files(root, source): validate with the site's actual JavaScript schema before atomic JSON replacement; preserve other projects; no-op for unchanged results.
- data/task3-leaderboard.json: schemaVersion, organization, caseCount, referenceOnly, coverage, entries, updatedAt. No token or raw plan content.
- site/data/leaderboard.json: published website dataset. project-03 primaryMetric rounds; secondary movementSteps; timeLabel explains that the timestamp is result-generation time.
- LaunchAgent logs: ~/Library/Logs/ece281-task3-sync.stdout.log and .stderr.log. Run launchctl kickstart gui/$(id -u)/com.ece281.task3-sync to refresh manually after installation.
