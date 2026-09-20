---
id: REQ-0060
title: 做减法前先查引用，别误删还在用的东西
skill: shy-skill-suite
status: done
kind: fix
iteration: 1
created: 2026-09-18
updated: 2026-09-18
blocked_by: []
related: [REQ-0053, REQ-0057, REQ-0059]
---

# REQ-0060 做减法前先查引用，别误删还在用的东西

## 问题与目标

`iteration-5` 复审抓到一条**修复自伤**：为响应用户"报告别放过程"的偏好，删掉了报告摘要里的"被证伪"计数，但复审规范仍要求 `summary` 显示淘汰数。独立子 agent 复核确认：该规则缺口不在别处——`run_checks.py` 里搜 `falsified` / `被证伪` / `淘汰` **零命中**，没有任何机械检查兜底；现有规则也只管大重构的调用点与破坏性操作，不要求"删对外呈现前查引用"。

同时，独立复核澄清了另一件事：「摘要显示淘汰数」与「逐条过程字段（证伪 / 证据）不进报告」两条规则**并不冲突**，但关系没写清，会再次互相打。

目标：
1. **做减法前查引用**：删或隐藏对外呈现 / 检查（按钮 / 字段 / 显示 / `check`）前，先检索技能文件与 `run_checks.py` 注册表，确认没有规则 / 检查仍要求它。
2. **写清两规则关系**：淘汰数是**汇总行、保留可见**；`falsification` / `evidence` 是**逐条过程字段、不进报告**。
3. 给"摘要必须显示淘汰数"加**机械检查**，不再只靠人读规则。

（注：独立复核认为"勾 `done` 前逐条核验"已被 `lifecycle.md:62/:95/:98` 覆盖，属违规而非规则缺口，**本 REQ 不加新规则**。）

## 触发与分支

- 实现路每次做减法（删按钮 / 字段 / 显示 / `check`）之前。
- 复审 Step 8 生成报告、判断摘要该显示什么。

## 行为与步骤

1. `references/lifecycle.md` 阶段 2 完成判据：加"删对外呈现 / 检查前先检索技能文件与 `run_checks.py` 注册表"。
2. `references/reviewing-skills.md` Step 8：在三字段规则旁写清"淘汰数（汇总行）保留可见 vs 逐条过程字段不进报告"。
3. `scripts/run_checks.py`：注册 `req0060-report-summary`——报告可见摘要必须含"候选 N / 通过 M / 被证伪 K"。

## 脚本与资源

- 改 `references/lifecycle.md`、`references/reviewing-skills.md`、`scripts/run_checks.py`。
- 不改 `render_report.py`（摘要已经在渲染淘汰数）。

## 降级与边界

- 减法检查只限"对外呈现 / 注册检查"，不扩成"任何改动前全仓搜"。
- 规则只写一处（`lifecycle.md`），不在 `SKILL.md` 复述。

## 验收标准

- [x] 报告可见摘要含"候选 N / 通过 M / 被证伪 K" — `check:req0060-report-summary`（实测 缺=[]）
- [x] `lifecycle.md` 阶段 2 完成判据含"删对外呈现 / 检查前先检索技能文件与 `run_checks.py` 注册表" — （语义）已落：阶段 2 加「做减法前查引用」段
- [x] Step 8 写清"淘汰数保留、逐条过程字段不进报告" — （语义）已落：Step 8 加「淘汰数与过程字段的关系」bullet

## 范围外

- 不加"勾 done 前逐条核验"新规则（已被 `lifecycle.md:62/:95/:98` 覆盖）。
- 不扩减法检查到所有改动。
- 不改 `render_report.py` 的摘要实现。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-18 | 实现：`lifecycle.md` 阶段 2 加「做减法前查引用」；Step 8 加「淘汰数与过程字段的关系」；`run_checks.py` 注册 `req0060-report-summary`；不加 R1 新规则（已有覆盖） | Gate：`validate` ok；`run_checks` 33/33（新检查 PASS）；`selftest` 21/21；`untagged 0`、`converged true`；`track` ok | 收敛 |

## 备注 / 待办

- 来源：2026-09-18 用户要求"开个子代理复核两条规则"；独立复核结论 = R2 采纳、R1 已有覆盖。
- 独立复核证据：`run_checks.py` 搜 `falsified`/`被证伪`/`淘汰` = 0；HEAD 版 `reviewing-skills.md:172` 已要求淘汰数；`iteration-5/report.html` 可见摘要缺该字段。
- 2026-09-18（`iteration-6` 立即修）：「做减法前查引用」由独立段落**并进阶段 2 完成判据**，使本 REQ 验收「完成判据含」成立（原先只是独立成段，构成 over-claim）。
