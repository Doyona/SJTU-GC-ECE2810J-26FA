# Website context

Static GitHub Pages leaderboard at https://Doyona.github.io/SJTU-GC-ECE2810J-26FA/. The existing main-branch push workflow tests/builds site/ and deploys dist/. No third-party runtime dependencies. The user requested removal of Project 1/2 during this work; only Project 3 / Task 3 remains.

Task 3 reads the local course exporter in /Users/twistzz/ece281repo/ece281s1-joj/home/tt/.config/joj/project/p3/src/export_class_lengths.py. That exporter performs authenticated GET requests using the existing external Joint-Teapot .env. Raw snapshots and CSVs are stored under data/task3/ (ignored). Sanitized valid results and coverage are in data/task3-leaderboard.json; site/data/leaderboard.json adds project-03 with rounds and movementSteps metrics. No shortest-path optimality is claimed. Release-only policy: trust bot-course Issue authors, require p3-release plus completed Actions release events at refs/tags/p3 with matching run number and full SHA. Unverified/preview snapshots and old preview caches cannot be published. Case-set identity still requires course-side confirmation. On 2026-11-19 a full 102-repository read found no verified P3 release results; the previous preview entries were removed from the public board.

The hourly LaunchAgent is com.ece281.task3-sync, StartInterval 3600, RunAtLoad true. It runs src/sync_task3.py --publish. The runner refuses unrelated local/staged changes, branches other than main, and unrelated unpublished commits. It only fast-forwards a clean checkout, and commits only the two JSON files when results change. Incomplete fetches retain last published data. A failed data-only push can be retried. The Mac must be logged in and running; sleep/offline delays updates.

GitHub HTTPS authentication depended on an expired VS Code askpass socket. The website origin uses existing authenticated GitHub SSH access instead. The runner removes editor askpass variables and uses noninteractive SSH with known-host verification; no new credentials are stored.

Build/check commands: npm test; python3 -B -m unittest discover -s test -p 'test_*.py'; npm run build. No workflow changes are required.
