---
id: REQ-0054
title: 报告内交互式分拣（前端勾选 + 复制/下载 triage.json）
skill: shy-skill-suite
status: done
kind: feature
iteration: 1
created: 2026-09-18
updated: 2026-09-18
blocked_by: []
related: [REQ-0019, REQ-0053]
---

# REQ-0054 报告内交互式分拣（前端勾选 + 复制/下载 triage.json）

## 问题与目标

复审收尾要用户**逐条分拣**（立即修 / 以后修 / 丢弃，见 `reviewing-skills.md` Step 8）。现在只能在对话里一条条回答，10 条 findings 就要来回很多轮。

用户诉求（2026-09-18）：**能不能在 HTML 报告页直接勾选，然后提交？**

约束：报告是 `file://` 单文件、无服务器、无外链（`REQ-0019` 范围外）；浏览器到 agent 没有回传链路。所以"直接提交"落地为：页面内勾选 → 一次点击**复制到剪贴板**（粘贴回对话）或**下载 `triage.json`**（告知路径）。

目标：报告内每条 finding 带三选一控件 + 两个导出按钮；仍保持单文件、无服务器、逐条选择（不做批量全选）。

## 触发与分支

- 复审 Step 8 生成报告后，用户逐条分拣。
- 用户说"在页面上勾 / 怎么提交分拣 / 报告能点吗"。

## 行为与步骤

1. `render_report.py`：每条 finding 渲染一个分拣块（三选一 radio + 可选备注），带稳定 id（`F1`…`Fn`，按报告顺序）。
2. `assets/report-template.html`：加顶部工具条——「复制分拣结果」「下载 triage.json」「清空」+ 状态提示；内联脚本负责：
   - 勾选写 `localStorage`（刷新不丢）；
   - 复制文本形如 `shy-skill-suite iteration-4 分拣：F1=立即修 F2=以后修 …`；
   - 下载 `triage.json`（`{skill, iteration, generated_at, triage:[{id, choice, note}]}`）。
3. 无 findings 时隐藏工具条。
4. 文档同步：`reviewing-skills.md` Step 8（分拣可用页面完成）、`running-evals.md` 报告节（控件 + 仍无服务器/无自动回传）。
5. 不给已有 REQ 的 `（语义）` 判据添乱；`REQ-0019` 的「不做反馈回写」按部分取代订正（无服务器、无自动回传仍成立）。

## 脚本与资源

- 改 `scripts/render_report.py`（finding 分拣块）、`assets/report-template.html`（工具条 + 内联脚本 + 样式）。
- 改 `references/reviewing-skills.md` Step 8、`references/running-evals.md` 报告节、`SKILL.md` 资源行、`REQ-0019` 范围外/迭代记录。
- 改 `scripts/run_checks.py`：注册 `req0054-triage-ui`。
- 不改 `findings.json` schema（分拣结果另存 `triage.json`）。

## 降级与边界

- **不做 HTTP 服务器、不做自动回传**——没有浏览器到 agent 的稳定通道；"提交"= 复制/下载 + 一次粘贴或告知路径。
- 剪贴板在少数环境不可用时，附手动抄写文本兜底。
- `triage.json` 由用户保存；agent 不主动扫下载目录。

## 验收标准

- [x] 报告每条 finding 带 `data-fid` 三选一控件（默认立即修），动作栏只有「提交给 agent」、无复制 / 下载 / 清空、可见内容无外链 — `check:req0054-triage-ui`（2026-09-18 由 `REQ-0059` 部分取代：分拣只在 `--serve`，静态只读）
- [x] 勾选写 `localStorage`，刷新页面后保留 — （语义）已落：模板内联脚本以 `shy-triage-<skill>-<iteration>` 为键读写；待用户打开报告实测
- [x] `reviewing-skills.md` Step 8 与 `running-evals.md` 报告节写明页面分拣与边界 — （语义）**2026-09-18 由 `REQ-0059` 部分取代**：分拣只在 `--serve`、静态只读；原文「复制 / 下载」边界已不适用（见 `REQ-0059`）
- [x] `REQ-0019` 的「不做反馈回写」已按部分取代说明订正 — （语义）已落：范围外加 `REQ-0054` 部分取代说明，迭代记录加第 3 行

## 范围外

- 不做批量全选（分拣保持逐条）。
- 不改 `findings.json` 的字段集合。
- 不做服务器、不做自动回传、不做账号/持久化到远端。
- 不引入第三方依赖或外链。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-18 | 实现：`render_report.py` 每条 finding 渲染三选一 + 备注块（`F1`…`Fn`）；`report-template.html` 加工具条（复制 / 下载 triage.json / 清空）+ localStorage 内联脚本；`run_checks.py` 注册 `req0054-triage-ui`；`lifecycle.md` / `running-evals.md` / `SKILL.md` 同步；`REQ-0019` 部分取代订正 | Gate：`validate` ok；`run_checks` 30/30（`req0054-triage-ui` PASS、`缺=[] 外链=0`）；`selftest` 20/20；`untagged 0`、`converged true` | 收敛 |
| 2 | 2026-09-18 | 部分被 `REQ-0059` 取代：分拣只在 `--serve`；删复制 / 下载 / 清空；静态报告只读 | `check:req0054-triage-ui` 改为 serve 校验 | 现状见 `REQ-0059` |

## 备注 / 待办

- 来源：2026-09-18 用户提问"能否直接在 html 报告页面勾选然后提交"。
- 与 `REQ-0019` 的关系：部分取代其「不做反馈回写」——仍无服务器/无自动回传，只加前端导出。
- triage 文件位置由用户决定；agent 在用户告知路径后读取并执行。
