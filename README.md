# ECE2810J · Fall 2026 Leaderboard

SJTU Global College ECE2810J 的静态排行榜，适用于 GitHub Pages。原生 HTML / CSS / JavaScript，无第三方运行时依赖，无需数据库。

> 当前包含两个演示项目，所有队名、成员和成绩均为虚构。页面会显示 **DEMO** 提示。正式使用前请替换数据，并将 `demo` 设为 `false`。

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

只需编辑 [`site/data/leaderboard.json`](site/data/leaderboard.json)，提交并推送到 `main`。

- `demo`：演示数据为 `true`，真实结果改成 `false`。
- `updatedAt`：本次数据发布的 ISO 时间戳，需要时区，例如 `2026-11-04T13:00:00Z`。页面统一显示北京时间 UTC+8。
- `projects`：每个对象是一张独立榜单；复制现有项目对象即可新增。
- 项目的 `id`：唯一、只含小写字母、数字和连字符，也用于分享链接，如 `?project=project-02`。
- `title` / `description`：项目标题和说明。
- `metrics`：可自定义指标列。`key` 为唯一标识，`label` 为显示名，`unit` 为单位（可为空字符串），`decimals` 为显示小数位数（0–6），`direction` 取 `desc`（越高越好）或 `asc`（越低越好）。
- `primaryMetric`：决定正式名次的指标 `key`。
- `entries`：队伍结果；无成绩时使用空数组 `[]`。

每支队伍的数据示例：

```json
{
  "id": "team-01",
  "name": "Your team",
  "members": ["Member A", "Member B"],
  "language": "C++",
  "metrics": { "score": 98.75, "runtime": 12.4, "memory": 8.2 },
  "updatedAt": "2026-11-04T13:00:00Z"
}
```

队伍 `id` 在同一项目内必须唯一；每个配置的指标都需要一个非负有限数值。`members` 可以是空数组。请只发布计划公开的成员显示名和成绩。

## 排名与页面功能

- 按 `primaryMetric` 的数值和方向排名，精确相等的结果并列，使用 `1, 2, 2, 4` 名次。并列队伍按 `id` 稳定排列。
- 显示小数位数仅影响格式，排名使用原始数值；如果不希望四舍五入后看起来相同的结果分属不同名次，请先将源数据舍入到规定精度。
- 点击排名、队名或指标表头可以切换升降序；更换展示顺序不会改变正式名次。
- 搜索队名或成员，支持 `/` 快捷键聚焦搜索框。
- CSV 导出当前搜索、排序后的结果，保留原始指标精度。
- 手机适配、键盘操作、空榜和加载失败提示。
- 通过 URL 的 `project` 参数分享指定项目。

这是展示用静态站点。成绩由仓库维护者更新；提交评测、自动采集和后台管理需要另行接入。字体使用系统字体，页面资源均随仓库发布。

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
