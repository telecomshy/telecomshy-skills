---
id: REQ-0046
title: 实现 / 评审两路分离 + 评审收敛到分拣 + 单次实施
skill: shy-skill-suite
status: done
iteration: 1
created: 2026-09-17
updated: 2026-09-17
blocked_by: []
related: [REQ-0018, REQ-0041, REQ-0043]
---

# REQ-0046 实现 / 评审两路分离 + 评审收敛到分拣 + 单次实施

## 问题与目标

`REQ-0041` 把"复审"做成了"实现的自动尾巴"（实现完必审），`REQ-0043` 又规定"一有发现就停下问"。用户反馈：**别扭**——"我让你实现 X，你却自动评审、然后把一堆我没要的 P0/P1 甩给我"；而且自动环有循环风险。

根因：**把两个触发意图不同的动作硬绑在一起**——"做 X"要的是**交付**，"查一下"要的是**质检**。

目标（用户 2026-09-17 提案）：
- **两路分离**：实现路与评审路各自独立。
- **评审由用户触发**（不再自动）。
- **评审收敛到分拣**：出报告后**逐条**让用户选「立即修 / 以后修 / 丢弃」，**不做批量**；按所选**实施一次即停，不自动再审**。
- 丢弃**不落盘、不留痕**。
- 主/子 REQ **放弃**（价值仅可追溯，不值当）。

## 触发与分支

- 实现路：用户说"做 X / 改 X"。
- 评审路：用户说"评审 / 检查一下 / 跑个复审"、`/shy-review`。

## 行为与步骤

1. **`lifecycle.md` 阶段 2（实现路）**：实现完只跑**静默秒级门**（`validate` + `run_checks` + `selftest`）；绿了报"完成"、红了才说；**不产 findings、不出报告、不自动进评审**。完成判据 = 交付合格（不再要求"审过一轮"）。
2. **`lifecycle.md` 阶段 3（评审路）**：**只在用户要求时进入**；跑完整三轴（行为相关 / 里程碑才加 eval）；收尾 = 报告 + **逐条分拣**（立即修 / 以后修 / 丢弃，不做批量）→ 按所选**实施一次** → 静默门 → **结束，不自动再审**。
3. **`lifecycle.md` 阶段 4**：实现路机械记账自动；评审路按分拣回写（以后修 → 落盘 `ready`；丢弃 → 不落盘）。
4. **`lifecycle.md` 阶段 5**：**用户驱动，不自动推进**（无自动回环）；保留收工判据。
5. **`SKILL.md`** 共用原则 + 开头一句；**`reviewing-skills.md` Step 8**；**`running-evals.md` HTML 节**；**`commands/shy-apply.md`**。
6. **取代 `REQ-0041` / `REQ-0043`**：加 `superseded_by: REQ-0046`、`status: out-of-scope`。
7. **`run_checks.py`**：注册本 REQ 检查。

## 脚本与资源

- 改 `references/lifecycle.md`（阶段 2/3/4/5 + 开头 + 斜杠快捷 + 一句话）、`SKILL.md`、`references/reviewing-skills.md`、`references/running-evals.md`、`commands/shy-apply.md`。
- 改 `docs/.../REQ-0041-*.md`、`REQ-0043-*.md`（取代标注）。
- 改 `scripts/run_checks.py`（注册 `req0046-*`）。

## 降级与边界

- **实现路仍有证据**：静默秒级门照跑，只是**不把结果甩给用户**（绿=报完成，红=才说）。
- **评审路仍是"判断由人"**：分拣即人工闸门。
- **不自动再审**：一次评审只实施用户勾选的那批，不会自我繁殖。
- **丢弃不留痕**：不落盘、不记备注（按用户要求）。
- 不实现"以后修"的自动排期——落盘 `ready` 后由用户按 frontier 决定何时做。

## 验收标准

- [ ] `lifecycle.md` 含「实现路」与「评审路」两条路 — `check:req0046-two-paths`
- [ ] `lifecycle.md` 阶段 3 含「用户主动触发 / 只在用户要求时进入」 — `check:req0046-user-triggered`
- [ ] `lifecycle.md` 含分拣三选项 + 「不落盘」 + 「不自动再审」 — `check:req0046-triage`
- [ ] `SKILL.md` 共用原则含「实现 / 评审两路分离」 — `check:req0046-skill-rule`
- [ ] `REQ-0041` 与 `REQ-0043` 含 `superseded_by: REQ-0046` — `check:req0046-superseded`
- [ ] **顺带修 `run_checks.py` 的跳过缺陷**：未实现的 REQ（`draft`/`ready`）的 `check:` 跳过，不因未注册报红 — `check:req0046-unimplemented-skipped`
- [ ] `validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0 — `check:skill-validate-ok`

## 范围外

- 主 / 子 REQ 层级（放弃）。
- 自动再审环 / 自动修复（明确否决）。
- "以后修"的自动排期。
- 丢弃项留痕。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-17 | 落需求并实施：实现 / 评审两路分离；评审改为用户触发 + 报告 + 逐条分拣 + 单次实施；取代 REQ-0041/0043；同步 `SKILL.md` / `reviewing-skills` / `running-evals` / `commands/shy-apply`。**顺带修 `run_checks.py` 跳过缺陷**：原只跳过 `deferred/out-of-scope`，漏了 `ready/draft`——`REQ-0044/0045`（ready）的 `check:` 因此报红；改为只对 `in-progress/done` 跑 check | `run_checks` **40 通过 / 0 失败**；`validate` ok | **done**（按实现路：静默门绿，自动回写） |

## 备注 / 待办

- 来源：2026-09-17 用户提案（"评审发现的问题不是用户主动提的，要把用户提的和 agent 发现的分开"）。
- 取代：`REQ-0041`（实现→必审门）与 `REQ-0043`（呈现门禁有事才停）——它们的耦合假设被本 REQ 否定。
- 保留 `REQ-0018` 的内核：**判断项由人**（现在落在"分拣"上）。
