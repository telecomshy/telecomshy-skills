---
id: REQ-0061
title: 按来源决定要不要逼问：用户提的才逼问，agent 提的不逼问
skill: shy-skill-suite
status: done
kind: fix
iteration: 1
created: 2026-09-18
updated: 2026-09-18
blocked_by: []
related: [REQ-0052, REQ-0055]
---

# REQ-0061 按来源决定要不要逼问：用户提的才逼问，agent 提的不逼问

## 问题与目标

2026-09-18 用户观察：**"技能应在新需求提出时逼问，但一直没触发。"** 复核证实：
- 60 张 REQ 里 `未逼问` 记录 **0 条**；
- 跳过规则只写在 `grilling.md:33`——而决定跳过就不会去读 `grilling.md`，规则永不生效（循环依赖）；
- `lifecycle.md` 阶段 1 落需求没有任何"逼问过了吗"的检查点。

同时用户给出判据（已确认）：**触发条件不是"用户 vs agent"，而是"决策缺口在谁那里"**——用户提的才逼问；agent 提的（复审 findings / 建议）信息已在提案里，用户只需「做 / 不做 / 换方案」。

目标：
1. 落 REQ 前加**检查点**：按来源判逼问（判定表进 `lifecycle.md` 阶段 1），并把跳过规则从 `grilling.md` 搬出来（单一事实源）。
2. REQ 模板备注加占位 `逼问：已过 / 跳过（依据：…）`，让每次落 REQ 显式做一次判断。

## 触发与分支

- 实现路阶段 1（落需求）之前。
- 用户说"这也要逼问吗 / 需求还没说清"。

## 行为与步骤

1. `references/lifecycle.md` 阶段 1：加「先判逼问」判定表——
   - 用户提、没说全 → **逼问**（`grilling.md`：设计树 + frontier，每问附建议答案）；
   - 用户提、已给全 → 跳过，记 `未逼问，依据：…`；
   - agent 提（复审 findings / 建议）→ **不逼问**，提案自带 问题与目标 / 范围外 / 验收 / 备选与默认，用户做「做 / 不做 / 换方案」；
   - agent 提案含**真实分叉且无合理默认** → **只就分叉问一次**（mini-grill）。
   并把完成判据补上"备注有逼问记录"。
2. `references/grilling.md`「可跳过」段改成指针：判定表以 `lifecycle.md` 阶段 1 为准，本文件只讲怎么逼问。
3. `references/writing-requirements.md` §6 模板的「备注 / 待办」加占位行 `逼问：<已过 N 轮 / 跳过（依据：…）>`。

## 脚本与资源

- 改 `references/lifecycle.md`、`references/grilling.md`、`references/writing-requirements.md`。
- 无脚本改动（判定是语义动作，且"备注含某行"属措辞检查，不设 `check:`）。

## 降级与边界

- 不改逼问机制本身（设计树 / frontier / 三个动作）。
- 不强制所有 REQ 都逼问；agent 提案走"确认"而非"问答"。
- 判定表只写一处（`lifecycle.md`），`grilling.md` 不重复。

## 验收标准

- [x] `lifecycle.md` 阶段 1 含按来源的逼问判定表（四行）与"备注记逼问"要求 — （语义）已落：阶段 1 加判定表 + 完成判据补"备注有逼问记录"
- [x] `grilling.md`「可跳过」是指针、不重复判定表 — （语义）已落：改为指向 `lifecycle.md` 阶段 1
- [x] `writing-requirements.md` §6 模板备注含 `逼问：…` 占位 — （语义）已落

## 范围外

- 不改逼问的提问方法（`grilling.md` 的三个动作）。
- 不新增机械检查（措辞类）。
- 不回填历史 REQ 的逼问记录。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-18 | 实现：`lifecycle.md` 阶段 1 加「先判逼问」判定表（四行）+ 完成判据补逼问记录；`grilling.md`「可跳过」改指针；`writing-requirements.md` 模板备注加 `逼问：…` 占位 | Gate：`validate` ok；`run_checks` 33/33；`selftest` 21/21；`untagged 0`、`converged true`；`track` ok | 收敛 |

## 备注 / 待办

逼问：已过（用户确认来源判据）——依据：2026-09-18 对话"用户提的才逼问，agent 提的不逼问"。

- 2026-09-18（`iteration-6` 立即修）：备注格式统一为 `逼问：跳过（依据：…）`（判定表与模板一致）；`grilling.md` 只留指针、删掉判定表复述。
