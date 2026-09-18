---
id: REQ-0007
title: 盲测 A/B（comparator 落地）
skill: shy-skill-suite
status: done
kind: feature
iteration: 1
created: 2026-09-16
updated: 2026-09-16
blocked_by: []
related: [REQ-0005]
---

# REQ-0007 盲测 A/B（comparator 落地）

## 问题与目标

有一类失效现有三轴抓不到：**两版都过全部断言，但主观质量差很多**（结构 / 可读性 / 忠实度 / 有用性）。pass-rate delta 看不见它。`references/subagents.md` 里已有 `comparator` 角色，但只是 stub——没说**何时用、怎么评、结果怎么解读**。目标：落地为**可选、情景触发**的一步（不设为默认）。

## 触发与分支

- 比较**两个版本**的技能，且产出含主观质量（文风 / 结构 / 设计 / 可读性 / 忠实度）。
- 用户说"哪版更好 / 盲测对比一下 / v2 是不是真的更好"。

## 行为与步骤

1. 扩写 `references/subagents.md` 的 `comparator`：
   - **何时**：两版 + 主观产出；纯行为型技能不需要。
   - **怎么做**：同一 prompt 的两版产出**匿名化、随机标 A/B**；**两个顺序都跑**（抵消位置偏好）；按 rubric 打分（结构 / 可读性 / 忠实度 / 有用性）+ 偏好 + 置信度。
   - **注意**：不告知哪版是哪版；LLM 裁判有位置 / 冗长 / 自我偏好，盲测只缓解不消除，结果是**信号不是证据**；**与断言结果并列报告、不合并**。
2. `reviewing-skills.md` Step 8 加一处指向 `comparator` 的指针。
3. 不新增文件、不新增脚本。

## 脚本与资源

- 只改 `references/subagents.md` 与 `references/reviewing-skills.md`。

## 降级与边界

- 需要子 agent（或两次隔离运行 + 一个裁判）；不支持则内联并注明"未隔离"。
- 仅主观型技能；不设为默认步骤；结果当信号。

## 验收标准

- [x] `subagents.md` 的 `comparator` 含**何时 / 怎么做（匿名 + 随机 + 两顺序 + rubric）/ 注意**。 — （episode）
- [x] 明确"与断言结果**并列报告、不合并**"。 — （episode）
- [x] 明确"结果是**信号**、非证据"与 LLM 裁判偏差提醒。 — （episode）
- [x] `reviewing-skills.md` Step 8 有指向 `comparator` 的指针。 — （episode）
- [x] 未新增文件或脚本。 — （episode）

## 范围外

- 不新增脚本 / 文件；不把 A/B 设为默认步骤；不做跨平台。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-16 | 落需求 + 实现：扩写 `subagents.md` 的 comparator（何时 / 怎么做 / 注意）；`reviewing-skills.md` Step 8 加指针 | 5/5 验收通过 | 收敛（done） |

## 备注 / 待办

- 参考：skill-creator / skill-forge 的 `comparator`；我们**只落地到 `subagents.md`**，不新增文件。
