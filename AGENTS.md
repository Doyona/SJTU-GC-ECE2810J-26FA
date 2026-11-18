# Website maintenance

Read context.md and API.md before work. Put new source under src/ and tests under test/; preserve existing site/, scripts/ and tests/ paths.

The user authorized hourly Task 3 collection and publication to this website. The scheduled job may commit/push only data/task3-leaderboard.json and site/data/leaderboard.json, on main at Doyona/SJTU-GC-ECE2810J-26FA. Never include unrelated changes or push the course JOJ repository. Do not change CI without a separate request.

Gitea credentials stay outside this checkout. data/task3/ is private local collection state and must remain Git-ignored. Only 20/20 verified runs get aggregate metrics. Missing, failed, stale, unreleased and unknown case-set data must not be turned into official bonus results. The user requested removal of Project 1/2; do not restore them.
