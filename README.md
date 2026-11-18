# ECE2810J Fall 2026 · Project 3 Task 3

静态网站：https://Doyona.github.io/SJTU-GC-ECE2810J-26FA/ 。按用户要求移除了 Project 1、2，只显示 Task 3 的同步轮数和移动步数。

## 每小时同步

本机 LaunchAgent `com.ece281.task3-sync` 每 3600 秒读取全部学生 `*project` 仓库的最新可见 P3 结果。

- 原始快照、CSV 与读取状态保存在 `data/task3/`，该目录不提交。
- `data/task3-leaderboard.json` 保存可公开的有效汇总，随后更新 `site/data/leaderboard.json`。
- 只展示 20 个用例全部验证通过的最新运行。同步轮数为路线长度指标；移动步数为 A+B 非等待动作总数。
- release 与用例集版本尚未确认，页面明确标注为参考快照，不作为正式 bonus 名次。
- 只有数据变化时才提交两份 JSON 并推送 `main`，由现有 GitHub Pages 工作流自动部署。
- 读取失败保留旧数据；工作区有无关改动或分支冲突时停止发布，不 reset、stash 或强制推送。
- 凭据沿用外部 Joint-Teapot 配置，不复制到网站。定时器需要 Mac 登录并运行，睡眠或断网会延迟同步。

日志：`~/Library/Logs/ece281-task3-sync.stdout.log` 和 `.stderr.log`。

手动触发：`launchctl kickstart gui/$(id -u)/com.ece281.task3-sync`。
停止任务：`launchctl bootout gui/$(id -u)/com.ece281.task3-sync`。

## 本地检查

```sh
npm test
python3 -B -m unittest discover -s test -p 'test_*.py'
npm run build
npm run dev
```

离线转换：`python3 -B src/sync_task3.py --source-json /path/to/class-lengths.json`。正式采集及发布时使用 `--exporter /absolute/path/to/export_class_lengths.py --env-file /absolute/path/to/teapot.env --publish`。

## 文件

- `src/sync_task3.py`：采集、校验、去重、更新与受限发布。
- `test/test_sync_task3.py`：同步规则测试。
- `site/`：原生 HTML/CSS/JavaScript 网页。
- `scripts/build.mjs`：校验后生成 `dist/`。
- `tests/leaderboard.test.mjs`：排序、并列、搜索、CSV 与数据格式测试。

查看 `context.md`、`API.md` 及 `AGENTS.md` 获取维护约定。
