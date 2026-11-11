# ECE2810J · Fall 2026 Leaderboard

SJTU Global College ECE2810J 的静态排行榜，适用于 GitHub Pages。原生 HTML / CSS / JavaScript，无第三方运行时依赖，无需数据库。

> 两个项目各保留一条 Baseline。实测成绩公布前，指标栏和名次显示为「—」。

## 发布到 GitHub Pages

1. 将本仓库代码推送到 GitHub 的 `main` 分支。
2. 打开仓库 **Settings → Pages → Build and deployment**，将 **Source** 设为 **GitHub Actions**。
3. 在 **Actions → Deploy leaderboard to GitHub Pages** 中选择 **Run workflow**；之后每次向 `main` 推送都会自动校验、测试并部署。
4. 部署成功后，访问：<https://Doyona.github.io/SJTU-GC-ECE2810J-26FA/>。

上面的地址是该仓库对应的预期地址，首次部署成功前可能返回 404。仓库必须具备 Pages 使用权限；组织策略和账户套餐可能影响可用性。

部署遵循 [GitHub 官方自定义 Pages 工作流](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)。发布产物只包含 `dist/` 中的网站文件。

## 本地预览与校验

需要 Node.js 22+ 和 Python 3，无需 `npm install`。

```sh
npm run dev
```

打开 <http://127.0.0.1:8000>。页面通过 HTTP 读取 JSON，请使用本地服务器预览。

```sh
npm test
npm run build
```

`build` 会验证数据并将网站复制到 `dist/`。数据格式不正确会阻止部署，避免发布无效排行榜。

## 更新成绩

由课程维护者在 GitHub 编辑 [`site/data/leaderboard.json`](https://github.com/Doyona/SJTU-GC-ECE2810J-26FA/edit/main/site/data/leaderboard.json)。在对应项目的 `entries` 中添加或修改记录，再把文件顶部的 `updatedAt` 更新为带时区的发布时间。改动进入 `main` 后，GitHub Pages 会自动发布。

- `demo`：演示数据为 `true`，真实结果改成 `false`。
- `updatedAt`：本次数据发布的 ISO 时间戳，需要时区，例如 `2026-11-04T13:00:00Z`。页面统一显示北京时间 UTC+8。
- `projects`：每个对象是一个项目，项目内可按指标切换榜单。
- 项目的 `id`：唯一、只含小写字母、数字和连字符，也用于分享链接，如 `?project=project-02`。
- `title` / `description`：项目标题和说明。
- `metrics`：可自定义指标列。`key` 为唯一标识，`label` 为显示名，`unit` 为单位（可为空字符串），`decimals` 为显示小数位数（0–6），`direction` 取 `desc`（越高越好）或 `asc`（越低越好）。
- `primaryMetric`：首次打开项目时默认选中的排名指标 `key`。
- `entries`：个人成绩记录。

每条记录的格式如下。

```json
{
  "id": "entry-01",
  "submittedAt": "2026-11-11T15:30:00+08:00",
  "name": "学生姓名",
  "metrics": { "searchTime": 12.345, "steps": 24 }
}
```

记录的 `id` 在同一项目内必须唯一。`submittedAt` 是实际提交时间，使用带时区的 ISO 时间戳，页面会换算为北京时间。`name` 是榜单显示的姓名，`searchTime` 是搜索耗时（毫秒），`steps` 是最短步数（非负整数）。

`id` 为 `baseline` 的记录可将 `metrics` 设为 `null`，以显示待填的 Baseline。缺少提交时间的记录显示「—」。

## 排名与页面功能

- 每个项目都有搜索用时榜和最短步数榜，使用同一批成绩分别排名。用时更短或步数更少的成绩在对应榜单上靠前，同指标值并列。首次打开默认选中最短步数榜。
- 点击表头可调整当前表格的展示顺序，切换榜单会恢复对应指标的排序。
- 支持按姓名搜索，按 `/` 可聚焦搜索框。
- CSV 导出当前榜单的四个字段，保留提交时间的原始时区和指标精度。文件名包含排名指标。
- 手机适配、键盘操作、空榜和加载失败提示。
- 通过 URL 的 `project` 和 `ranking` 参数分享指定榜单，例如 `?project=project-02&ranking=searchTime`。

## 文件结构

```text
site/
  index.html             页面结构
  styles.css             样式及响应式布局
  app.mjs                页面交互及 CSV 导出
  leaderboard.mjs        数据校验、排序与排名规则
  data/leaderboard.json  榜单数据
scripts/build.mjs        校验并生成 dist/
tests/leaderboard.test.mjs
.github/workflows/pages.yml
```
