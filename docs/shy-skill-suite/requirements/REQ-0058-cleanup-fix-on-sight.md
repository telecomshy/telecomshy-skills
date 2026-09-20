---
id: REQ-0058
title: 台账策略：能确认的问题直接修（并结清现存 7 条）
skill: shy-skill-suite
status: done
kind: hygiene
iteration: 1
created: 2026-09-18
updated: 2026-09-18
blocked_by: []
related: [REQ-0052, REQ-0055]
---

# REQ-0058 台账策略：能确认的问题直接修（并结清现存 7 条）

## 问题与目标

用户反馈（2026-09-18）：**"台账不是轻量、可以确认的错误吗？为什么还开着？每次直接修就好了吧？"**

现状：`cleanup.md` 的 `CL-0030`–`CL-0036` 全是**可确认、机械可修**的卫生项（未勾验收、不可复现的判据、缺交叉引用、重复、cache、缺完成判据），却停在 `open`。台账本意是**轻量**，`open` 越积越多反而成了第二份待办。

目标：规则改成——**能当场确认并机械修的条目，当场修掉并标 `fixed`，不留 `open`**；只有**需要用户决策**（如"要不要合并 B 读数"）或**跨较大改动**的才保持 `open`。并结清现存 7 条。

## 触发与分支

- Step 8 把自洽项写入台账时。
- 任何一轮 Gate / 复审顺手看到 `open` 条时。

## 行为与步骤

1. `references/reviewing-skills.md` Step 8：写台账规则——**能确认即修，修完标 `fixed` + `evidence`**；仅决策 / 跨改动项留 `open`。
2. `writing-requirements.md` §4：同一句指针（不重复正文）。
3. 结清 `CL-0030`–`CL-0036`：
   - `CL-0030`：勾上 `REQ-0046` 64–66 三条已成立的验收。
   - `CL-0031`：`REQ-0012:57` 的 `{python}` 模板改成可复现写法。
   - `CL-0032`：`writing-requirements.md` §1 ↔ §4 加交叉引用。
   - `CL-0033`：删「`falsification`/`evidence` 不进报告」的重复，只留一处（随 `REQ-0057` 的 Step 8 改写）。
   - `CL-0034`：`converged` 公式只留 `glossary.md`，另两处改指针。
   - `CL-0035`：`SKILL.md` 脚本职责清单压成一个指针（去掉 cache）。
   - `CL-0036`：`lifecycle.md` 阶段 6 补完成判据。

## 脚本与资源

- 改 `references/reviewing-skills.md`、`references/writing-requirements.md`、`references/lifecycle.md`、`SKILL.md`。
- 改 `docs/shy-skill-suite/cleanup.md`（7 条转 `fixed`）。
- 改 `docs/shy-skill-suite/requirements/REQ-0012` / `REQ-0046`（判据订正）。
- 无脚本改动。

## 降级与边界

- "直接修"只限**可确认 + 机械**；有争议的仍进台账等决策，不做静默改判。
- 台账字段与关闭路径不变（id / dedup_key / first_seen / status / resolved_in / evidence）。
- 不把行为改动塞进台账——行为改动仍走 REQ。

## 验收标准

- [x] Step 8 写明"能确认即修、修完标 fixed；仅决策 / 跨改动项留 open" — （语义）已落：Step 8「P2 不阻断」bullet 加该规则；`cleanup.md` 备注同步
- [x] `cleanup.md` 的 `CL-0030`–`CL-0036` 全部 `fixed` 且各带 `evidence` — （语义）已落；Gate 台账 open 27→20
- [x] 7 条对应改动已落：`REQ-0046` 验收已勾、`REQ-0012` 判据可复现、§1↔§4 互指、证伪规则去重、converged 单一来源、SKILL 脚本行无清单、阶段 6 有完成判据 — （语义）逐条已改

## 范围外

- 不改台账字段与写命令（`CL-0023`）。
- 不处理需用户决策项（`CL-0025` 已 `wontfix`，其余如 `CL-0020` 保持 open）。
- 不新增脚本检查（内容判定是语义动作）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-18 | 实现：Step 8 与 `cleanup.md` 加"能确认即修"规则；结清 `CL-0030`–`CL-0036`（验收补勾、判据可复现、§ 互指、重复去重、converged 单一来源、脚本行压指针、阶段 6 补完成判据） | Gate：`validate` ok；`run_checks` 32/32、台账 open 27→20；`selftest` 21/21；`converged true` | 收敛 |

## 备注 / 待办

- 来源：2026-09-18 用户提问"台账为什么还开着"。
- 与设计的关系：设计说 `open` 须在 N 次 Gate 内结清——本 REQ 把"结清"提前到"发现当时"，更轻。
