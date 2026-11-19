# Website maintenance

Read context.md and API.md before work. Put new source under src/ and tests under test/; preserve existing site/, scripts/ and tests/ paths.

Keep visible website text in English and omit explanatory notes and instructional copy. Each student has one entry: the best valid release by lowest total rounds, then movement steps, then earliest result/run ID. Preserve locally observed release history so later failed or worse runs cannot replace the best result.

The user authorized hourly Task 3 collection and publication to this website. The scheduled job may commit/push only data/task3-leaderboard.json and site/data/leaderboard.json, on main at Doyona/SJTU-GC-ECE2810J-26FA. Never include unrelated changes or push the course JOJ repository. Do not change CI without a separate request.

Gitea credentials stay outside this checkout. data/task3/ is private local collection state and must remain Git-ignored. Collect only bot-authored p3-release results backed by completed Actions release events at refs/tags/p3 with matching run number and full SHA. Ignore all preview data, including old caches. Only 20/20 verified released runs get aggregate metrics. Missing, failed, stale, unreleased and unknown case-set data must not be turned into official bonus results. The user requested removal of Project 1/2; do not restore them.
