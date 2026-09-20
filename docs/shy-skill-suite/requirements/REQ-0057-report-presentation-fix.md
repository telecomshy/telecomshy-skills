---
id: REQ-0057
title: 修正报告呈现（提交按钮置底、默认选立即修、三字段用白话）
skill: shy-skill-suite
status: done
kind: fix
iteration: 1
created: 2026-09-18
updated: 2026-09-18
blocked_by: []
related: [REQ-0019, REQ-0053, REQ-0054, REQ-0056]
---

# REQ-0057 修正报告呈现（提交按钮置底、默认选立即修、三字段用白话）

## 问题与目标

`iteration-4` 分拣（`--serve`）后，用户反馈（2026-09-18）：

1. **按钮冗余**：有服务器提交了，复制 / 下载按钮不再需要（仅静态兜底保留）。
2. **提交太靠前**：顶部工具条让人没读完就能交；提交应放在**报告最下方**。
3. **清空位置别扭**：不应在顶部。
4. **默认值缺失**：逐条点太累；默认应是「立即修」。
5. **解释看不懂**：finding 里出现 `§5`、「历史散文」、「无条件全量扫」等**不解释的内部引用 / 术语**；用户不知道指什么。
6. **字段过多**：`问题 / 影响 / 建议 / 预期` 四段可合并为三段——**存在问题**（专业简短，含为什么要改与改后好处）/ **白话解释** / **修改建议**。

目标：serve 模式只留「提交给 agent」+「清空」并放到报告末尾；单选默认「立即修」；报告字段改三字段；人类字段写作规则禁止未解释的 `§` 引用、内部术语、裸 `file:line`。静态模式保留复制 / 下载兜底。

## 触发与分支

- 复审 Step 8 生成报告、用户分拣。
- 用户说"按钮太多 / 看不懂解释 / 报告字段太长"。

## 行为与步骤

1. `assets/report-template.html`：删顶部工具条；在 findings 之后加**底栏**；底栏动作按模式渲染——serve（`btnSubmit` + `btnReset`）、静态（`btnCopy` + `btnDownload` + `btnReset`）。
2. `scripts/render_report.py`：`render_finding` 只渲染 `problem`（存在问题）/ `plain`（白话解释）/ `suggestion`（修改建议）；三选一控件默认 `checked` 在「立即修」（有 `localStorage` 记录时按记录恢复）；`build_html` 依 endpoint 选择底栏动作。
3. `references/reviewing-skills.md` Step 8：报告格式改三字段；加**人类字段写作规则**——不出现未解释的 `§` / 术语 / 裸 `file:line`；`falsification` / `evidence` 仍不进报告。
4. `SKILL.md` 共用原则同步三字段。
5. `scripts/run_checks.py`：更新 `req0053-report-human`（新字段）与 `req0054-triage-ui`（静态兜底 + 默认勾选 + 无顶部工具条）；新增 `req0057-serve-actions`（serve 只出提交、静态只出复制/下载）。
6. 把 `iteration-4/findings.json` 重写为新三字段，并用白话重写内容。

## 脚本与资源

- 改 `assets/report-template.html`、`scripts/render_report.py`、`references/reviewing-skills.md`、`SKILL.md`、`scripts/run_checks.py`。
- 改 `skills/shy-skill-suite-workspace/iteration-4/findings.json`（呈现层快照重写）。
- 不改分拣三选项、`triage.json` 结构、`--serve` 协议。

## 降级与边界

- 静态模式只读（无服务器、无控件）；要分拣用 `--serve`（`REQ-0059` 订正）。
- 默认「立即修」不等于批量——每条仍可改；用户提交前应过目。
- 不改 finding 的判定与优先级；`falsification` / `evidence` 仍必须产出。

## 验收标准

- [x] serve 动作栏只有 `btnSubmit`（无复制 / 下载 / 清空）、三选一默认「立即修」；静态报告只读（无控件 / 按钮、含只读提示） — `check:req0057-serve-actions`（2026-09-18 由 `REQ-0059` 部分订正：原"静态保留复制 / 下载"被推翻）
- [x] 报告渲染 存在问题 / 白话解释 / 修改建议 三字段，且不出现 `falsification` / `evidence` 的值；静态页面无顶部工具条、含默认勾选 — `check:req0053-report-human`（PASS）/ `check:req0054-triage-ui`（PASS）
- [x] Step 8 写明三字段与「人类字段不得含未解释引用 / 术语」规则 — （语义）已落：Step 8 报告格式改三字段 + 「说人话」bullet 加禁止项；`SKILL.md` 共用原则同步
- [x] `iteration-4/findings.json` 已重写为三字段且内容为白话 — （语义）已重写 9 条（problem/plain/suggestion）

## 范围外

- 不改 `--serve` 协议与安全边界（回环 + token）。
- 不做批量全选按钮。
- 不改 findings 的判定规则。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-18 | 实现：模板删顶部工具条、加置底动作栏（serve=提交+清空；静态=复制+下载+清空）；三选一默认「立即修」；渲染字段改 存在问题/白话解释/修改建议；Step 8 加三字段与「不得含未解释 § / 术语 / 裸 file:line」规则；重写 `iteration-4/findings.json` | Gate：`validate` ok；`run_checks` 32/32（`req0057-serve-actions`、`req0053-report-human`、`req0054-triage-ui` 全 PASS）；`selftest` 21/21；`untagged 0`、`converged true` | 收敛 |

## 备注 / 待办

- 来源：2026-09-18 用户反馈（按钮、位置、默认值、解释看不懂、字段合并）。
- 与 `REQ-0054` / `REQ-0056` 的关系：本次是第三次呈现调整——静态兜底保留，serve 收敛为单一提交。
