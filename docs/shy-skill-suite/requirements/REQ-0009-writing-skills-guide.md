---
id: REQ-0009
title: 前向写作指导（writing-skills.md）与 lever 单一事实源
skill: shy-skill-suite
status: done
iteration: 1
created: 2026-09-16
updated: 2026-09-16
blocked_by: []
related: []
---

# REQ-0009 前向写作指导（writing-skills.md）与 lever 单一事实源

## 问题与目标

实测（grep）表明：`writing-for-agents` 的 lever（no-op / cache / leading word / duplication / sprawl / sediment / co-location / 按需披露 / 完成判据 / 提前收工 / 禁止句 / 单一事实源）**大多已在复审里**。缺的是两块：

1. **前向写作指导**：`lifecycle` 阶段 2（实现）只有"脚手架 + 事后复审"，没有"写之前怎么写对"的指南。
2. **lever 的单一事实源**：lever 定义散在复审 Step 2–4；若再补写作指南，就会两处定义同一 lever。

目标：新增 `references/writing-skills.md` 作为 lever 的**单一事实源**（面向写作）；复审 Step 2–4 保留**检查动作**、定义改为指向它；`lifecycle` 阶段 2 引用它。

## 触发与分支

- `lifecycle` 阶段 2（实现）动笔写 `SKILL.md` 时。
- 用户说"怎么写技能 / `SKILL.md` 怎么写 / 帮我写好这个技能"。

## 行为与步骤

1. 新增 `references/writing-skills.md`：面向"写技能"的 lever——
   description 作触发指针 / 调用方式 / 信息层级与按需披露 / co-location / leading word / 否定句 / 剪枝（单一事实源·cache·relevance·sediment·no-op）/ 步骤与完成判据 / 校准（控制力度·默认非菜单·教方法）/ 何时拆分。
2. `reviewing-skills.md` **Step 4（结构与预算）/ Step 5（步骤与完成判据）**：由"内联 lever 定义"改为"**逐条按 `writing-skills.md` 检查**"（保留完成判据）。
3. `reviewing-skills.md` **Step 2（有效性）**：no-op / cache 的定义改为指向 `writing-skills.md` §7；控制力度 / 给默认 / 教方法 / 粒度改为指向 §9 / §10；保留复审特有的真实专长 / gotcha / 事实准确性。
4. `lifecycle.md` 阶段 2：加"写之前 / 之时按 `writing-skills.md` 自查"。
5. `SKILL.md`：资源列表加 `writing-skills.md`；路由加"怎么写技能"入口。

## 脚本与资源

- 新增 `references/writing-skills.md`（纯文档）。
- 改 `references/reviewing-skills.md` / `references/lifecycle.md` / `SKILL.md`。

## 降级与边界

- 只覆盖对**技能写作**有用的 lever；**不引入**通用文档写作（AGENTS.md 等）、`cognitive load`、`router skills`（Tier 3+，已 deferred）。
- 技能自包含：不引用仓库 `docs/`，也不依赖外部 `writing-for-agents` 技能。
- 不新增脚本。

## 验收标准

- [x] `references/writing-skills.md` 含上述 10 组 lever。
- [x] `reviewing-skills.md` Step 4 / Step 5 改为指向 `writing-skills.md`，不再内联定义 lever。
- [x] `reviewing-skills.md` Step 2 的 no-op / cache 定义改为指向 `writing-skills.md` §7。
- [x] **单一事实源抽样**：定义句「模型默认就会做的」只出现在 `writing-skills.md`（`reviewing-skills.md` 中出现 0 次）。
- [x] `lifecycle.md` 阶段 2 引用 `writing-skills.md`。
- [x] `SKILL.md` 资源列出 `writing-skills.md`，路由含写作入口。
- [x] 自包含：`writing-skills.md` 不引用仓库 `docs/`。

## 范围外

- 不引入 `cognitive load` / `router skills` / 通用文档写作；不新增脚本；不做跨平台。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-16 | 落需求 + 实现：新增 `references/writing-skills.md`（10 组 lever）；复审 Step 2/4/5 的 lever 定义改为指向它；`lifecycle` 阶段 2 引用；`SKILL.md` 资源与路由同步 | 7/7 验收通过 | 收敛（done） |

## 备注 / 待办

- 来源：`writing-for-agents`（mattpocock）。我们**自包含地吸收 lever**，不依赖该外部技能。
