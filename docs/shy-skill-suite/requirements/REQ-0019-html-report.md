---
id: REQ-0019
title: 把评测和复审意见合成一份单文件 HTML 报告
skill: shy-skill-suite
status: done
kind: feature
iteration: 2
created: 2026-09-16
updated: 2026-09-16
blocked_by: [REQ-0018]
related: [REQ-0018, REQ-0012]
---

# REQ-0019 把评测和复审意见合成一份单文件 HTML 报告

## 问题与目标

评估完成后没有可视化产物：复审结论只在对话里，评测只在 `benchmark.json` / `benchmark.md`。用户想要一个 HTML 页面，一次看完**评测数字 + 复审修改意见**，再决定落不落盘。

- 对标（读源码）：`skill-creator/eval-viewer/generate_review.py`（471 行）读工作区 → 把 runs/grading/benchmark 用 `/*__EMBEDDED_DATA__*/` 嵌进 `eval-viewer/viewer.html` → 起本地 HTTP 或 `--static <path>` 输出独立 HTML；反馈经 `/api/feedback` POST 回写 `feedback.json`。
- **事实澄清**：`skill-forge` **没有** HTML 报告（全仓库 grep `html|viewer|browser` 只命中 `CODE_OF_CONDUCT.md` 的一个 URL），只有 `benchmark.md`。可参照的仅 skill-creator。

目标：技能自包含、**客户端无关**地生成单文件 HTML（数据内嵌、无服务器、无 CDN），opencode / TeleAgent 都能直接打开。

## 触发与分支

- 走 `REQ-0018` 的「呈现门禁」时（复审/评测收工）。
- 用户说"把评估结果给我看 / 出个报告 / 想看看这次的评测"。

## 行为与步骤

1. 新增 `scripts/render_report.py`，用法：

   ```bash
   python render_report.py <iteration-dir> --skill-name <name> [--findings <findings.json>] [--out report.html]
   ```

   - 读 `<iteration-dir>/benchmark.json`（若存在）、各 `eval-N/{eval_metadata.json,with_skill/grading.json,timing.json,baseline/...}`、以及 `--findings`（缺省取 `<iteration-dir>/findings.json`，schema 见 `REQ-0018`）。
   - 输出**单文件 HTML** 到 `--out`（默认 `<iteration-dir>/report.html`）。
2. 新增 `assets/report-template.html`：纯内联 CSS，**无任何外部资源**（无 CDN、无外链字体/脚本）。两个区块：
   - **评测**：summary（with_skill vs baseline 的 pass_rate/tokens/耗时 + delta + 方差）、逐 eval 表。
   - **复审意见**：按 P0/P1/P2 排序、按轴（行为/需求/标准）分组；每条含 位置 / 问题 / 影响 / 建议 / 预期 / 证伪与证据。
   - 缺失数据（只有 findings 无 benchmark，或反之）时对应区块显示"无数据"，不报错。
3. 模板占位符沿用 skill-creator 的方式：`/*__EMBEDDED_DATA__*/` → `const DATA = {...};`。
4. 纯 stdlib、UTF-8、非交互；`--out` 覆盖写（幂等）。
5. 退出码：`0` 成功 / `1` 工作区或模板缺失、无任何可渲染数据 / `2` 参数错误；`--help` 含简述 + 参数 + 至少 1 个示例 + 退出码含义（对齐 `REQ-0012`）。
6. `references/running-evals.md` 增一节「HTML 报告」：命令 + 产物路径 + `findings.json` 指针。
7. `SKILL.md` 资源列表与复审分支各加一句指针（不重述用法）。

## 脚本与资源

- 新增 `scripts/render_report.py`、`assets/report-template.html`（技能首次出现 `assets/`）。
- 改 `references/running-evals.md`（增「HTML 报告」节）、`SKILL.md`（资源清单 + 指针）。

## 降级与边界

- **不做服务器、不做反馈回写**（skill-creator 的 `/api/feedback` 是 Claude Code 交互场景；shy 只做"呈现"）。用户反馈走对话，落盘走 `REQ-0020` 的 `/shy-apply`。
- HTML 体积随内嵌数据增长；默认只嵌 `benchmark.json` + findings + 逐 eval 的摘要字段，**不内嵌** run 的原始 `outputs/`（需要的用户自己开工作区目录）。
- 中文内容按 UTF-8 输出；Windows 控制台不打印正文，只打印产物路径。
- 不引入任何第三方依赖。

## 验收标准

- [x] 构造一份假 `iteration-1/`（含 `benchmark.json` + 2 个 eval 的 grading/timing + `findings.json`）→ `render_report.py` 退出码 0，生成 `report.html`（实测 `evals: 2, findings: 3`）。 — `check:render-report-ok`
- [x] `report.html` 为单文件自包含：`grep "https?://"` 0 命中；`<script src>`/`<link href>` 0 命中（样式与数据全内联）。 — （episode）
- [x] HTML 内嵌 JSON 可解析，且评测摘要与 findings 条目数与输入一致（`evals=2`、`findings=3`）。 — （语义）
- [x] 只有 findings（无 benchmark）时仍生成 HTML、退出码 0；只有 benchmark（无 findings）同样退出 0。 — `check:render-report-ok`
- [x] 缺工作区 / 无数据 → 退出码 1 且**错误 JSON 走 stderr**；缺必填参数 → 退出码 2。 — `check:render-report-ok`
- [x] `--help` 含简述、参数、示例、退出码；`--help` 退出码 0。 — `check:scripts-help-ok`
- [x] `validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0；引用无悬空（模板在 `assets/` 内）。 — `check:skill-validate-ok`
- [x] 无第三方依赖（只用标准库）。 — （episode）

## 范围外

- 不做 HTTP 服务器、不做反馈回写（`feedback.json`）。**"不做浏览器自动打开"已被 `REQ-0022` 取代**——现默认生成后自动打开（`--no-open` 可关）。**本行被 `REQ-0054` 部分取代**：报告加前端分拣控件（立即修 / 以后修 / 丢弃）与「复制 / 下载 `triage.json`」；仍无服务器、无自动回传。
- 不改 `aggregate_benchmark.py` 的产出（报告只消费它）。
- 不内嵌 run 原始产出文件（无 base64 图片/PDF）。
- 不做跨平台（`REQ-0020` 的 command 另议）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-16 | 落需求（用户诉求：HTML 呈现评测 + 修改意见） | — | 待开工 |
| 2 | 2026-09-16 | 新增 `scripts/render_report.py`（读 benchmark/evals/findings，静态渲染 + 内嵌 JSON）与 `assets/report-template.html`（内联 CSS）；`running-evals.md` 增「HTML 报告」节；`SKILL.md` 资源清单加脚本与 assets | 2-eval + findings 假数据 → exit 0、`evals=2/findings=3`；无外链；内嵌 JSON 可解析；findings-only / benchmark-only 均 exit 0；无数据→1（stderr）、缺参→2、`--help`→0；`validate_skill` ok | 收敛（done） |
| 3 | 2026-09-18 | 部分订正：报告加前端分拣控件与 triage 导出（`REQ-0054`）；「不做反馈回写」仍指无服务器 / 无自动回传 | `REQ-0054` `check:req0054-triage-ui` | 契约见技能文件与 `REQ-0054` |
| 4 | 2026-09-18 | `iteration-4` 立即修：报告在每个优先级内**按轴分组**（落实 Step 8「分轴报告、不合并」） | `render_report.py` 的 `render_group`；`run_checks` 31/31 | done |

## 备注 / 待办

- 来源：2026-09-16 用户诉求；决策：报告范围 = **评测 + 复审意见合一**。
- 与 skill-creator 的差异：它起服务器 + POST 回写；shy 只出静态单文件——因 opencode/TeleAgent 无稳定"打开浏览器 + 回传"链路。
- `REQ-0012` 的 `--help` 完整化要求对本脚本同样适用。
