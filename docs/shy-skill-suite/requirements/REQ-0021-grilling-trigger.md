---
id: REQ-0021
title: description 补逼问域限定触发词（修复逼问分支不可达）
skill: shy-skill-suite
status: done
iteration: 2
created: 2026-09-16
updated: 2026-09-16
blocked_by: []
related: [REQ-0006, REQ-0010, REQ-0020]
---

# REQ-0021 description 补逼问域限定触发词（修复逼问分支不可达）

## 问题与目标

用户实测"逼问模式**每次都不触发**"。根因（已核对）：

- 证据（读源码）：`SKILL.md:19` 路由表有「逼问需求 / 拷问一个技能该做什么」分支，但 `SKILL.md:3` 的 `description` 只列 新建/修改技能、写需求、复审、改 SKILL.md、校验结构、迭代回写——**不含任何逼问/拷问/澄清字眼**。路由表是**技能触发之后**才读的，所以裸说"逼问"永远不会命中 shy。
- 证据（`REQ-0010` 备注自述）：「`REQ-0006` 的验收要求的是**路由表**含逼问入口，不要求 description 保留裸短语」——即逼问入口一直只在路由表里，description 从未覆盖。
- 竞品：mattpocock 的 `grilling` 是独立 model-invoked 技能，description 就是「any 'grill' trigger phrases」。用户说"逼问/grill"时命中的是它，不是 shy。

目标：让"逼问一个**技能**该做什么"能命中 shy，同时**不重演 `REQ-0010` 的误触发**——沿用"意图式 + 域限定"，不引入裸短语。

## 触发与分支

- 触发 `SKILL.md` 的逼问分支（`references/grilling.md`）。
- 用户说"逼问这个技能 / 拷问一下它要做什么 / 帮我澄清这个技能该做什么"。

## 行为与步骤

1. `SKILL.md` 的 `description` 触发段补**域限定**说法（倾向措辞，不逐字照搬）：在现有列举中加「逼问 / 澄清某个**技能**该做什么，或给既有技能回溯意图」。
2. 保持意图式表述；**禁止**把裸短语（"逼问X"不带"技能"、或"grill"）直接列为触发示例（`REQ-0010` 已证伪此法）。
3. `description` ≤ 1024 字符；不改路由表、不改 `grilling.md`。
4. 与 `REQ-0020` 的 `/shy-grill` 互补：命令保证必达，description 补自然语言召回。

## 脚本与资源

- 只改 `SKILL.md` 的 frontmatter `description`；不改脚本、不改 `references/`、不改路由表。

## 降级与边界

- 会轻微增加与 mattpocock `grilling` 的重叠；以"技能域限定"区分（本技能只管**技能**这一产物的逼问，通用 grill 仍归 mattpocock）。
- 措辞精度无法用启发式脚本取证（`running-evals.md` 已声明 `heuristic` 不是证据）；以真实子 agent 轨迹为准。

## 验收标准

- [x] `description` 含"逼问"（措辞：「逼问 / 澄清某个技能该做什么」），每处出现都带"技能"域限定。
- [x] `description` 不含裸短语触发（无「逼问一个需求」这类无域限定写法）。
- [x] `description` ≤ 1024 字符（实测 166）。
- [x] `validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0。
- [x] 本步只改 `SKILL.md` 的 frontmatter `description` 行；路由表与 `references/` 未改动。
- [ ] **待验证**：回归（正例）「逼问一下这个技能该做什么」→ 触发并进入 `references/grilling.md`。本机 `shy-skill-suite` 未部署到 `~/.agents/skills`（子 agent 的 available_skills 不含它），无法取真实轨迹。
- [ ] **待验证**：回归（near-miss）「帮我澄清这段代码要做什么」→ 不落盘、不进入技能开发流程。同上，无真实轨迹。

## 范围外

- 不改路由表（`REQ-0006` 已有逼问入口）、不改 `grilling.md` 内容、不新增 command（`REQ-0020`）。
- 不改 mattpocock 的 `grilling` 技能。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-16 | 落需求（用户实测：逼问不触发） | — | 待开工 |
| 2 | 2026-09-16 | 实施：`description` 加域限定「逼问 / 澄清某个技能该做什么」 | `description` 实测 166 字符、含域限定逼问；`validate_skill` → ok；本步只改 description 行。**触发真实轨迹：待验证**（技能未部署到 `~/.agents/skills`，无法取轨迹） | done（附 2 条待验证） |

## 备注 / 待办

- 来源：2026-09-16 用户诉求；决策：**opencode + 加域限定触发词**。
- 与 `REQ-0010` 不冲突：`REQ-0010` 删的是**无域限定的裸短语**；本 REQ 加的是**带技能域限定**的意图式说法。
