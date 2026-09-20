---
id: REQ-0035
title: 给 description 优化定停止规则（最多 5 轮，卡住就换写法）
skill: shy-skill-suite
status: done
kind: docs
iteration: 1
created: 2026-09-17
updated: 2026-09-17
blocked_by: []
related: [REQ-0010, REQ-0021, REQ-0034]
---

# REQ-0035 给 description 优化定停止规则（最多 5 轮，卡住就换写法）

## 问题与目标

`optimize_description.py` 已实现 train/validation 分层与"按 test 选优"（`REQ-0010`），但规范里**没有"什么时候停"**：没有轮数上限，也没有"卡住怎么办"。

缺口（一手来源：`agentskills.io/skill-creation/optimizing-descriptions`）：**通常 5 轮足够**；卡住时应**换一种结构性写法**，而不是继续微调措辞——继续微调会把 description **过拟合到测试集**（正是 `reviewing-skills.md §3`「泛化，别打补丁」防的那件事）。

> 来源：`docs/shy-skill-suite/research/skill-development-best-practices.md` §6.2 候选 I（"需改造后吸收"）。

目标：给触发优化环一条明确的**停止规则**，避免无限微调。

## 触发与分支

- 复审（`reviewing-skills.md`）Step 1 的触发审查 / description 优化环。
- 用户说"description 一直调不好 / 还要再改几轮"。

## 行为与步骤

1. **`references/reviewing-skills.md` Step 1**：在「怎么验」之后、完成判据之前，加「**迭代停止规则**」——通常 5 轮足够；卡住时换结构性写法（如从"列举分支"改为"按用户意图收口"），不要继续微调措辞。

## 脚本与资源

- 改 `references/reviewing-skills.md`（Step 1）。
- 改 `scripts/run_checks.py`（注册 `req0035-stop-rule`）。
- **不改** `optimize_description.py`：它仍只打分、给建议，循环由 agent 驱动（既定设计，见该脚本 docstring）。

## 降级与边界

- 5 轮是**经验默认值**（一手来源原话 "5 rounds is usually enough"），不是硬门禁；写出为什么超出仍可继续。
- 只加"怎么停"，不引入自动改写 / 自动循环（那是 skill-creator `run_loop.py`，本仓库明确不做）。

## 验收标准

- [ ] `reviewing-skills.md` Step 1 含「迭代停止规则」，写明 5 轮与结构性写法 — （episode）
- [ ] `validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0 — `check:skill-validate-ok`

## 范围外

- 不引入自动 description 改写环（`run_loop.py` 式）。
- 不改 `optimize_description.py` 的算法与参数。
- 不设硬性轮数门禁（只做经验提示）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-17 | `reviewing-skills.md` Step 1 加「迭代停止规则」；`run_checks.py` 注册 `req0035-stop-rule` | `run_checks.py` 全绿 | done |

## 备注 / 待办

- 与 `REQ-0034` 同类：都是"对标调研筛出的可直接吸收项"。
- 与 `REQ-0010` 的关系：`REQ-0010` 落的是"怎么选优"，本 REQ 落的是"什么时候停"，互补。
