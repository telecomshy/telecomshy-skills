---
id: REQ-0047
title: near-miss 触发复测（每条 ≥5 次，区分稳定误触发与噪声）
skill: shy-skill-suite
status: ready
kind: fix
iteration: 1
created: 2026-09-18
updated: 2026-09-18
blocked_by: []
related: [REQ-0010, REQ-0024, REQ-0039, REQ-0044]
---

# REQ-0047 near-miss 触发复测（每条 ≥5 次，区分稳定误触发与噪声）

## 问题与目标

`iteration-3` 复审（2026-09-18）行为轴 P1（待验证）：`description` 的 near-miss 误触发结论**互相打架**——

```
REQ-0039：同一批 near-miss，旧/新描述都是 0/3（判为单跑噪声）
REQ-0044：同一批 near-miss 用 --trials 3 跑出 #101/#103 触发率 0.667（2/3）
```

两处都基于 **n=3** 的小样本，谁也没说服谁；而 `reviewing-skills.md` Step 1 的判据是负例触发率必须 < 0.5。结论不定，就无法判断该不该给 `description` 补负向边界。

目标：用**每条 ≥5 次**的复测，把 near-miss 分成「稳定误触发（≥0.5）」与「噪声（<0.5）」两类，并据此决定是否补边界。

## 触发与分支

- 复审（`reviewing-skills.md`）Step 1 触发审查 / description 优化环。
- 用户说"触发准不准 / 跑一遍触发评测 / 把触发边界收一下"。

## 行为与步骤

1. 用技能自带评测集 `evals/evals.json`（随技能入库，见 `REQ-0049`）的 near-miss 子集，真跑
   `optimize_description.py <skill_dir> --eval-set evals/evals.json --runner opencode --detect shy-skill-suite --trials 5`。
2. 记录**每条**的触发率（0–1）。稳定 > 0.5 的判为真误触发。
3. 对真误触发项：按 `writing-skills.md` §1 补一句负向边界（`不适用于……`），再重测**正例**确认没有把该触发的漏掉；若正例触发率下降，回退该句。
4. 对 < 0.5 的项：在 `REQ-0044` 的迭代记录里把「0.667」更正为噪声，并写明本次样本量。

## 脚本与资源

- 复用 `scripts/optimize_description.py`（`--trials`）、`scripts/agent_runner.py`。
- 评测集 `evals/evals.json`（`REQ-0049` 入库）。
- 可能改 `SKILL.md` 的 `description`（仅当步骤 3 成立）。

## 降级与边界

- **无 runner**（本机无 opencode / TeleAgent 非交互 CLI）时保持 `ready`、**不臆测**结论——`REQ-0039` 已因单跑噪声白改过一次。
- 负向句同样占 `description` 常驻预算，只加必要的、不过度列举。
- 不扩评测集规模、不改评测口径（那是 `REQ-0044`）。

## 验收标准

- [ ] 每条 near-miss 至少跑 5 次、给出触发率（0–1），报告与命令写入迭代记录 — （行为）
- [ ] 稳定误触发项已按 `writing-skills.md` §1 处置：补边界并重测正例不降，或记录为噪声并更正 `REQ-0044` 的数字 — （语义）
- [ ] `python skills/shy-skill-suite/scripts/validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0 — `check:skill-validate-ok`

## 范围外

- 不扩评测集规模（仍用 `evals/evals.json` 的现有条目）。
- 不改 `optimize_description.py` 的评测口径与算法。
- 不做自动 description 改写环。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-18 | 落盘（`iteration-3` 复审 finding 3，用户分拣「以后修」） | `REQ-0039` 0/3 与 `REQ-0044` 0.667 矛盾、n=3 过小 | 待开工 |

## 备注 / 待办

- 来源：`skills/shy-skill-suite-workspace/iteration-3/findings.json` 行为轴 P1（verified: false）。
- 与 `REQ-0039` / `REQ-0044` 的关系：本 REQ 是那两次小样本结论的仲裁。
