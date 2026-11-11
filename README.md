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
- `projects`：每个对象是一张独立榜单；复制现有项目对象即可新增。
- 项目的 `id`：唯一、只含小写字母、数字和连字符，也用于分享链接，如 `?project=project-02`。
- `title` / `description`：项目标题和说明。
- `metrics`：可自定义指标列。`key` 为唯一标识，`label` 为显示名，`unit` 为单位（可为空字符串），`decimals` 为显示小数位数（0–6），`direction` 取 `desc`（越高越好）或 `asc`（越低越好）。
- `primaryMetric`：决定正式名次的指标 `key`。
- `entries`：个人成绩记录。

每条记录的格式如下。

```json
{
  "id": "entry-01",
  "name": "学生姓名",
  "metrics": { "searchTime": 12.345, "steps": 24 }
}
```

记录的 `id` 在同一项目内必须唯一。`name` 是榜单显示的姓名，`searchTime` 是搜索耗时（毫秒），`steps` 是最短步数（非负整数）。

`id` 为 `baseline` 的记录可将 `metrics` 设为 `null`，以显示待填的 Baseline。取得实测数据后，填入 `searchTime` 和 `steps`。

## 排名与页面功能

- 两个项目默认按最短步数从少到多排名。相同步数并列，名次如 `1, 2, 2, 4`。
- 点击姓名、搜索用时或其他表头可以切换展示顺序，正式名次保持原样。
- 支持按姓名搜索，按 `/` 可聚焦搜索框。
- CSV 导出当前搜索、排序后的结果，保留原始指标精度。
- 手机适配、键盘操作、空榜和加载失败提示。
- 通过 URL 的 `project` 参数分享指定项目。

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
