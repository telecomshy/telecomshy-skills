---
id: REQ-0075
title: 消除台账「发现即修」与复审「不自动修改」的矛盾（明确谁修、何时修）
skill: shy-skill-suite
status: done
kind: fix
iteration: 2
created: 2026-09-20
updated: 2026-09-20
blocked_by: []
related: [REQ-0046, REQ-0058, REQ-0071]
---

# REQ-0075 台账「发现即修」的矛盾治理

## 问题与目标

**矛盾（三处原文对质）**：

- `references/reviewing-skills.md:173` 台账类「写进 `cleanup.md`、**发现即修**、不进 findings」；`:172`「能当场确认并机械修的，**当场修掉**…不留 `open`」。
- `commands/shy-review.md:11`「**只呈现、不回写、不自动修改**」。
- `references/subagents.md:71` 复审子代理「**不写仓库**…不得改 `skills/` / `docs/` / 用户配置」。

**两层问题**：① 规则层——「发现即修」与「不自动修改」**直接打架**；② 分工层——复审的"发现"按设计是**子代理**做的（独立性），而子代理**禁写**，"当场修"只能由**主 agent** 做，但**没有一处写明**。

**实测后果**：2026-09-20 一次复审，子代理报了 7 条台账候选，主 agent 按 `/shy-review` 的"不自动修改"没动，它们一直 `open`，直到用户另行要求才清（19 → 9）。

**目标**：明确**谁修、何时修**，让两条规则共存——**行为类 findings 仍要用户分拣**（不自动改），**卫生类台账机械项由主 agent 当轮结清**（不占用户分拣）。

## 触发与分支

- 复审路 Step 8 收尾；任何一次复审产生台账候选时。
- 用户说"台账要发现即修，但复审又说不自动修改，矛盾"。

## 行为与步骤

1. **分工与时点**：台账**机械项**由**主 agent** 在复审 **Step 8（出报告前）当轮结清**；复审**子代理只负责发现、返回台账候选**（仍**禁写**）。
2. **限定「不自动修改」**：`commands/shy-review.md` 改为——"**不自动修改技能行为 / findings**；**台账（自洽/卫生）机械项由 agent 当轮结清**"（去掉无条件的"不自动修改"）。
3. **机械可修 vs 需决策的边界**（写进 `reviewing-skills.md` Step 8）：
   - **机械可修**（当轮结清、标 `fixed` + `evidence`）：去重 / 改指针 / 行号订正 / 死字段删除 / 计数漂移等**不改行为**的文本与卫生项；**改前查引用、改后过 Gate**。
   - **需决策**（留 `open`）：设计取舍 / 跨较大改动 / **会改 Gate 行为**（如接线新字段）/ 需用户拍板；在报告里**一句话提示**，不占 findings、不阻断。
4. **写入边界**（写进 `subagents.md` 副作用禁令）：子代理禁写**不变**；**主 agent 可改技能文件与 `cleanup.md`**（台账项常需改技能文件，如去重），改完过 Gate。
5. `references/lifecycle.md` 阶段 3 收尾表述与上述一致（含"台账机械项当轮结清"；"不自动再审"不变）。
6. `run_checks.py` 注册本 REQ 检查。

## 脚本与资源

- 改 `references/reviewing-skills.md`（Step 8 台账规则：谁修 / 何时 / 机械 vs 决策边界）。
- 改 `commands/shy-review.md`（「不自动修改」限定）。
- 改 `references/subagents.md`（副作用禁令节：台账由主 agent 结清、子代理只发现）。
- 改 `references/lifecycle.md`（阶段 3 收尾）。
- 改 `scripts/run_checks.py`（注册 `req0075-*`）。

## 降级与边界

- 子代理**禁写**不变（副作用禁令仍适用于子代理）；变的只是明确"台账由主 agent 结清"。
- **不引入无条件自动修改**：行为类 findings 仍走用户分拣。
- 需决策项**不擅自 `wontfix`**。
- 不改台账的字段结构（`dedup_key` / 写权等仍属 `CL-0023` 的设计决策）。

## 验收标准

- [x] `commands/shy-review.md` 不再无条件"不自动修改"，写明"不自动修改**技能行为 / findings**；台账机械项由 agent 当轮结清" — `check:req0075-triage-scope`
- [x] `references/reviewing-skills.md` Step 8 台账规则写明**由主 agent 在 Step 8 当轮结清**，并含**机械可修 / 需决策**的边界 — `check:req0075-ledger-owner`
- [x] `references/subagents.md` 副作用禁令写明"台账由主 agent 结清、子代理只发现（禁写不变）" — `check:req0075-subagents-boundary`
- [x] `references/lifecycle.md` 阶段 3 含"台账机械项当轮结清"且"不自动再审"不变 — `check:req0075-lifecycle`
- [x] `validate_skill.py skills/shy-skill-suite` → `status: ok`；`selftest.py` 退出码 0 — `check:skill-validate-ok` / `check:skill-selftest`
- [x] （语义）三处文本不再互相矛盾（复审"不自动修改"仅指行为/findings；台账机械项当轮结清、需决策项留 open 并在报告提示）；由复审人工判读 — 已落：`shy-review.md:11` 限定为"技能行为 / findings"+台账当轮结清；`reviewing-skills.md` Step 8 加机械可修/需决策边界；`subagents.md:71` 禁写不变、主 agent 结清；`lifecycle.md:87` 加"台账机械项当轮结清"、`:92` "不自动再审"保留

## 范围外

- 不改台账字段结构 / `dedup_key` 归一化 / 写命令（属 `CL-0023` 设计决策）。
- 不做"发现即修"的无条件自动修改（仅限机械卫生项）。
- 不改 findings 的分拣流程与报告 schema。
- 不改子代理禁写约束。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-20 | 落需求（未实现） | — | 待实现 |
| 2 | 2026-09-20 | 实现：`shy-review.md` 把「不自动修改」限定为技能行为 / findings、台账机械项当轮结清；`reviewing-skills.md` Step 8 写明主 agent 当轮结清 + 机械可修 / 需决策边界；`subagents.md` 副作用禁令写明台账由主 agent 结清、子代理只发现（禁写不变）；`lifecycle.md` 阶段 3 加「台账机械项当轮结清」（「不自动再审」保留）；`run_checks.py` 注册 `req0075-*` | Gate：`validate` ok；`run_checks` 64/64、未分类债 0、`converged true`；`selftest` 36/36；`track_requirements` status ok | 收敛（done） |

## 备注 / 待办

逼问：已过 1 轮——frontier：A（谁修/何时：主 agent 在 Step 8）+ B（「不自动修改」限定为行为/findings）+ C（机械可修 vs 需决策边界）+ D（子代理禁写不变、主 agent 可改技能文件与台账）；用户确认「按推荐」。

- 来源：2026-09-20 用户质疑「台账要求发现立即修，子代理又不能修，是不是技能上的 bug」。
- 关联：`REQ-0058`（台账"发现即修"规则的来源）、`REQ-0046`（实现/评审两路分离）、`REQ-0071`（评测独立）。
