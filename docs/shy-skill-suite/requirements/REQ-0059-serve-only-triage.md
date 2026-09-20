---
id: REQ-0059
title: 分拣只在 serve 模式可用（静态报告只读，删掉复制/下载/清空）
skill: shy-skill-suite
status: done
kind: fix
iteration: 1
created: 2026-09-18
updated: 2026-09-18
blocked_by: []
related: [REQ-0054, REQ-0056, REQ-0057]
---

# REQ-0059 分拣只在 serve 模式可用（静态报告只读，删掉复制/下载/清空）

## 问题与目标

用户反馈（2026-09-18）：打开的报告最下方是「复制分拣结果 / 下载 triage.json / 清空」三个按钮——那是静态兜底，但用户要的是**只有一个「提交给 agent」**；而且**清空也不需要**：每条默认「立即修」，永远有选择。

根因：`REQ-0057` 把静态模式当兜底保留了复制 / 下载；但报告的标准交付方式是 `--serve`，静态只是归档。

目标：**分拣控件与动作栏只存在于 `--serve` 模式**；动作栏只有一个「提交给 agent」；静态报告纯只读（无控件、无按钮，一行只读提示）。删掉复制 / 下载 / 清空的全部代码。

## 触发与分支

- 复审 Step 8 报告呈现与分拣。
- 用户说"静态报告怎么还有这些按钮 / 清空没用"。

## 行为与步骤

1. `render_report.py`：`render_finding` / `render_findings` 增加 `triage` 开关，仅 `--serve` 时渲染三选一与动作栏；静态只留只读提示。
2. `assets/report-template.html`：删除 `btnCopy` / `btnDownload` / `btnReset` 的按钮与处理代码；只保留 `btnSubmit` + `localStorage` + 状态栏。
3. `run_checks.py`：`req0054-triage-ui` 改为校验 serve 模式控件与"只有提交"；`req0057-serve-actions` 改为校验"静态无控件 / 无按钮；serve 只提交"。
4. 文档同步：`running-evals.md` 报告节、`reviewing-skills.md` Step 8、`lifecycle.md` 阶段 3。
5. `REQ-0054` / `REQ-0057` 的受影响措辞按部分取代订正。

## 脚本与资源

- 改 `scripts/render_report.py`、`assets/report-template.html`、`scripts/run_checks.py`。
- 改 `references/running-evals.md`、`references/reviewing-skills.md`、`references/lifecycle.md`。
- 改 `docs/.../REQ-0054` / `REQ-0057`（订正 + 迭代记录）。
- 不改 `--serve` 协议、`triage.json` 结构与三选项。

## 降级与边界

- 无 `--serve` 时报告只读；要分拣就重跑 `--serve`。
- 不做批量按钮；删「清空」（每条必有选择）。
- 不改 finding 判定与 `falsification` / `evidence` 的产出。

## 验收标准

- [x] serve 报告每条带三选一（默认立即修），动作栏只有 `btnSubmit`，且无 `btnCopy` / `btnDownload` / `btnReset` — `check:req0054-triage-ui`（实测 缺=[] 多余按钮=[]）
- [x] 静态报告无分拣控件、无任何按钮，含只读提示；serve 无顶部工具条 — `check:req0057-serve-actions`（实测 未过=[]）
- [x] `running-evals.md` / Step 8 / `lifecycle.md` 阶段 3 写明"分拣只在 serve，静态只读" — （语义）已落三处
- [x] `REQ-0054` / `REQ-0057` 的受影响**验收**已订正 — （语义）已订正并加迭代记录（其「范围外」散文属冻结历史，不追改）

## 范围外

- 不改 `--serve` 安全边界与超时行为。
- 不做批量全选 / 清空。
- 不重跑已有分拣。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-18 | 实现：分拣控件与动作栏改为仅 `--serve` 渲染；删 `btnCopy` / `btnDownload` / `btnReset` 按钮与代码；静态只留只读提示；`req0054-triage-ui` 改 serve 校验、`req0057-serve-actions` 改静态只读校验；文档三处同步；`REQ-0054` / `REQ-0057` 部分取代订正 | Gate：`validate` ok；`run_checks` 32/32（两条检查 PASS）；`selftest` 21/21；`untagged 0`、`converged true` | 收敛 |
| 2 | 2026-09-18 | `iteration-5` 立即修（报告相关）：无 findings 时 `--serve` 不再空等超时；内嵌数据剔除 `falsification` / `evidence`（报告可转发）；摘要补"被证伪"；服务说明改"只读归档"；`lifecycle` 补静态只读、`SKILL.md` 补"默认静态需显式 `--serve`" | Gate：`run_checks` 32/32（`req0053-report-human` 加整文件无过程字段断言）；`selftest` 21/21 | 收敛 |

## 备注 / 待办

- 来源：2026-09-18 用户反馈"应该只有一个提交给 agent 的按钮，连清空都不需要"。
- 与 `REQ-0057` 的关系：其"静态保留复制 / 下载"的取舍被本 REQ 推翻——静态改纯只读。
