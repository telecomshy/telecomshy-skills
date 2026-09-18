---
id: REQ-0051
title: 评审独立化 + converged 机械化（去自证）
skill: shy-skill-suite
status: done
kind: docs
source: retro
iteration: 1
created: 2026-09-18
updated: 2026-09-18
blocked_by: []
related: [REQ-0046, REQ-0050]
---

# REQ-0051 评审独立化 + converged 机械化（去自证）

## 问题与目标

2026-09-18 与用户的复盘得出两条：

1. **评审必须独立三方。** 本次 `iteration-3` 复审是**内联**跑的——同一 agent 既是技能作者又是复审者，**不是独立三方**；而外部独立评审抓到了自审漏掉的一批洞。技能虽已写"派发子代理 / 内联标未隔离"，但**没有把"作者不得自审"与"内联要下调置信度"写死**。
2. **`converged` 是自证。** 现状由跑复审的同一 agent 判 P0/P1 又写 `converged`——同一 agent 自证，可被"把发现降级成 P2"绕过。

目标：
- 评审（判断）**独立于作者**；内联则显式标"未隔离"并下调置信度。
- **独立性只加在评审**，不加到修复上（修复后只跑确定性的 Gate、不自动复审——避免循环）。
- `converged` 改为**机械判据**，由 `run_checks.py` 算出，agent 不得手写。

## 触发与分支

- 复盘（`lifecycle.md` 阶段 6）/ 复审（`reviewing-skills.md`）Step 8。
- 用户说"评审要独立三方 / 别再自证收敛"。

## 行为与步骤

1. **`references/subagents.md`**：加「**评审必须独立于作者**（作者不参与；内联标『未隔离』并下调置信度——自审不是独立评审）」与「**独立性只加在评审**（修复由主代理做；修完只跑 Gate、不派子代理复验、不自动重开）」。
2. **`references/reviewing-skills.md`** Step 8：`converged` 改为**机械判据** `(债达标) 且 (Gate 无失败) 且 (无未注册 check)`，由 `run_checks.py` 算并打印，**agent 不得手写**。
3. **`references/lifecycle.md`** 收工判据同步。
4. **`scripts/run_checks.py`**：算出并打印 `converged: true|false`；注册 `converged-mechanical`。

## 脚本与资源

- 改 `references/subagents.md`、`references/reviewing-skills.md`、`references/lifecycle.md`。
- 改 `scripts/run_checks.py`（机械 `converged` + 注册 `converged-mechanical`）。

## 降级与边界

- 不新增"修复后复验"环节——那会重新引入循环；确定性由 Gate 保证。
- 客户端不支持子代理时仍可内联，但**必须**标"未隔离"。
- `converged` 只读、机械；`state.json` 里只留 `converged_since` 作时间戳。

## 验收标准

- [x] `subagents.md` 含「评审必须独立于作者」与「独立性只加在评审」 — （语义）
- [x] `reviewing-skills.md` Step 8 的 `converged` 是机械判据（由 `run_checks.py` 算，agent 不得手写） — （语义）
- [x] `run_checks.py` 打印机械 `converged` — `check:converged-mechanical`
- [x] `python skills/shy-skill-suite/scripts/validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0 — `check:skill-validate-ok`

## 范围外

- 不实现"修复后自动复验 / 自动再审"（明确否决）。
- 不改 Gate 的确定性语义。
- 不改 `agent_runner.py` 脚本版。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-18 | 落盘并实施：`subagents.md` 加"评审独立于作者 / 独立性只加在评审"；Step 8 `converged` 改机械判据；`run_checks.py` 算并打印 `converged` + 注册 `converged-mechanical` | 见下方「备注」的门禁输出 | **done** |

## 备注 / 待办

- 来源：2026-09-18 用户复盘（"评审最好独立三方" + "修复完停、不自动复审"）。
- 与 `REQ-0046`（实现/评审两路分离）互补：那条定了"两路分离"，这条定了"评审独立、收敛机械"。
- 门禁证据：`run_checks` 全绿并打印 `converged:`；`classify_audit` E=0/S=0；`validate` ok。
