---
id: REQ-0016
title: 给开发生命周期的落需求和实现阶段补上可判定的完成判据
skill: shy-skill-suite
status: done
kind: feature
iteration: 2
created: 2026-09-16
updated: 2026-09-16
blocked_by: []
related: []
---

# REQ-0016 给开发生命周期的落需求和实现阶段补上可判定的完成判据

## 问题与目标

复审（2026-09-16，标准轴 P2，Step 5）：`lifecycle.md` 的六个阶段里，阶段 1 与阶段 2 没有可判定的完成判据。

- 证据（读 `lifecycle.md`）：
  - 阶段 0 有判据（指针到 `grilling.md` 的「frontier 空」）。
  - 阶段 5 有判据（"验收标准全过 / 无 P0-P1 / delta 稳定"）。
  - **阶段 1**（落需求）以「要不要拆成套件？」小节收尾，无判据句。
  - **阶段 2**（实现）以"跑 `validate_skill.py` 再进入复审"收尾——这是事实闸门，但没写成 done / not-done 的判据。
- 依据：`writing-skills.md` §8「每个 step 有可判定的完成判据；模糊的（"理解到位"）会诱发提前收工」。

影响：阶段 1 何时算"需求落好了"、阶段 2 何时算"这个增量做完了"，只能靠感觉——正是"提前收工"的入口。

目标：两个阶段各有一句可判定的完成判据，且强度足够（能挡住半成品）。

## 触发与分支

- 走 `lifecycle.md` 阶段 1 / 阶段 2 时。
- 复审 Step 5（步骤与完成判据审查）。

## 行为与步骤

1. `references/lifecycle.md` 阶段 1 末尾加**完成判据**（倾向措辞）：
   "手里有 1 份 `status: ready` 的 REQ：验收标准逐条可端到端验证、范围外已写、`blocked_by` 已连边（或显式为空）、迭代记录有第 1 行。"
2. `references/lifecycle.md` 阶段 2 末尾加**完成判据**：
   "`validate_skill.py <skill_dir>` → `status: ok`；且该增量声明的每条验收标准都能指出证据（命令输出 / 文件 / 计数），无一条标『待验证』。"
3. 两处判据只写在 `lifecycle.md`，不复制进 `reviewing-skills.md`（保持单一事实源）。

## 脚本与资源

- 只改 `references/lifecycle.md`；不改脚本、不改其它 `references/`。

## 降级与边界

- 判据要"可判定"而非"够严格"；不引入需要额外工具才能判的条件。
- 不要求阶段 2 的判据覆盖"全部增量"——判据是**每个增量**的收工线，与阶段 2 现有"每完成一个增量就进入复审"一致。

## 验收标准

- [x] `lifecycle.md` 阶段 1 含以"完成判据"标示的可判定条件，且提到 `status: ready`、验收标准可端到端验证、`blocked_by`、迭代记录（`lifecycle.md:47`）。 — （episode）
- [x] `lifecycle.md` 阶段 2 含以"完成判据"标示的可判定条件，且提到 `validate_skill.py` 与"每条验收标准有证据"（`lifecycle.md:57`）。 — `check:skill-validate-ok`
- [x] 两处判据措辞不与 `reviewing-skills.md` 的「完成判据」重复：`grep "待开发的 REQ 已达"` → 1（仅 lifecycle）、`grep "无一条标「待验证」"` → 1（仅 lifecycle）。 — （episode）
- [x] `validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0。 — `check:skill-validate-ok`
- [x] 本步只改阶段 1/2；阶段 3–6 未由本步改动（阶段 3/4 的现状是 `REQ-0018` 的合法改动）。 — （episode）

## 范围外

- 不改其它阶段、不改脚本、不改 `REQ-*` 文档。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-16 | 落需求（复审 P2），未实施 | — | 待开工 |
| 2 | 2026-09-16 | 实施：阶段 1 加完成判据（`status: ready` + 验收可验 + `blocked_by` + 迭代记录）、阶段 2 加完成判据（`validate_skill.py` ok + 每条验收有证据） | 判据句各唯一命中（`待开发的 REQ 已达`→1、`无一条标「待验证」`→1，均在 lifecycle.md）；`validate_skill` → ok；本步只改阶段 1/2 | 收敛（done） |

## 备注 / 待办

- 来源：2026-09-16 复审报告，标准轴 P2。
- 低危：阶段 2 已有事实闸门（跑校验器），本 REQ 主要是把它写成判据、并补上阶段 1 的空缺。
- 实施时**证伪了原拟措辞**：阶段 1 判据初稿以「手里有 1 份…」开头，与 `reviewing-skills.md:39`（Step 0 完成判据）字面撞车，违反"判据句唯一"；已改为「待开发的 REQ 已达 `status: ready`…」。记录以免下次重走。
