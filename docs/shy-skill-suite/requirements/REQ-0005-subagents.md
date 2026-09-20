---
id: REQ-0005
title: 复审时把部分活外派给子 agent（执行 / 打分 / 需求核对 / 分析 / 对比）
skill: shy-skill-suite
status: done
kind: feature
iteration: 1
created: 2026-09-16
updated: 2026-09-16
blocked_by: []
related: []
---

# REQ-0005 复审时把部分活外派给子 agent（执行 / 打分 / 需求核对 / 分析 / 对比）

## 问题与目标

复审里最该避免的两种偏差，主 agent 恰恰都犯：
- **自己写的自己评**（自我合理化）；
- **在含本会话历史的上下文里跑技能**（技能被"知道答案的 agent"执行，评测失真）。

skill-creator 与 skill-forge 都把"**跑**""**评**""**分析**"外派给子 agent。目标：把这几类工作按**窄 brief**外派，主 agent 只保留"写""问用户""综合决策"。

## 触发与分支

- 复审的 Step 1（触发）/ Step 2（有效性）/ Step 3（Spec）/ Step 8（汇总裁决）。
- 用户说"跑评测 / 用子 agent 评 / 复审这个技能"。

## 行为与步骤

1. 新增 `references/subagents.md`，定义 5 个角色，每个含**输入 / 任务 / 输出 / 禁止事项**：
   - **executor**：在**干净上下文**里跑一条 prompt（有技能 / 无技能），产出文件 + `timing.json`，不重试、不评判。
   - **grader**：对断言逐条 PASS/FAIL + **引用证据** → `grading.json`（`pass_rate`），不给自己打分、不知哪份是 with/baseline。
   - **spec-reviewer**：逐条验收标准 → 通过/部分/未实现（**引用 REQ 行**）+ 范围蔓延 + 文档-实现不一致。
   - **analyzer**（可选）：对 `benchmark.json` / `grading.json` 做失败聚类、flaky、回归、成本离群、触发 TPR/FPR。
   - **comparator**（可选）：盲测 A/B 两版产出（匿名、随机标 A/B）打分。
2. 写明**派发 / 内联**规则：客户端支持子 agent（opencode Task / Claude Code Task / TeleAgent 子任务）就派发；不支持则内联执行，并在报告注明"**未隔离**（独立性打折）"。
3. 在 `reviewing-skills.md` 的 Step 1 / 2 / 3 / 8 各加一处指向 `subagents.md` 的指针（按需加载）。
4. 写明与 `agent_runner.py` 的关系：**脚本版**=无头 / 可脚本化（`--runner opencode|teleagent|cmd`）；**子 agent 版**=agent 原生 / 真上下文隔离；二者互补，能派发时优先子 agent。

## 脚本与资源

- 新增 `references/subagents.md`（纯文档，无脚本）。
- 改 `references/reviewing-skills.md`（4 处指针）；`SKILL.md` 资源列表同步。

## 降级与边界

- 子 agent 支持因客户端而异；不支持时**内联并注明**，不假装隔离。
- **触发检测**依赖客户端可观测性：能拿到子 agent 的工具调用 → 主 agent 判定 `used_skill`；否则子 agent 自报（较弱，需标注）。
- 不改任何脚本；不实现具体子 agent 配置（那是客户端的事）。

## 验收标准

- [x] `references/subagents.md` 含 5 个角色，每个有 输入 / 任务 / 输出 / 禁止事项。 — （episode）
- [x] 明确"支持则派发、否则内联并注明未隔离"。 — （episode）
- [x] 明确 grader 与 spec-reviewer **独立于作者**、executor 用**干净上下文**。 — （episode）
- [x] `reviewing-skills.md` 的 Step 1 / 2 / 3 / 8 各有一处指向 `subagents.md` 的指针。 — （episode）
- [x] 说明与 `agent_runner.py` 的关系（脚本版 vs 子 agent 版）。 — （语义）
- [x] `SKILL.md` 资源列出 `subagents.md`。 — （episode）
- [x] 技能自包含：`subagents.md` 不引用仓库 `docs/`。 — （episode）

## 范围外

- 不实现具体子 agent 配置、不改脚本、不做跨平台转换。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-16 | 落需求 + 实现 `references/subagents.md`（5 角色 + 派发/内联规则 + 与 `agent_runner.py` 关系）；`reviewing-skills.md` Step 1/2/3/8 加指针；`SKILL.md` 资源同步 | 7/7 验收通过 | 收敛（done） |

## 备注 / 待办

- 参考：skill-creator 的 `agents/`（analyzer / comparator / grader）、skill-forge 的 8 个 agent；**吸收角色划分，不照搬其结构**。
